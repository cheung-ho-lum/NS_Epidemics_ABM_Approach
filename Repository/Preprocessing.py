import datetime
import random
import statistics

import networkx as nx
from ABM.AirGraph import AirGraph
from Parameters import EnvParams, SimulationParams, DisplayParams
from pathlib import Path
import math
from transliterate import translit
import codecs
import csv
import reverse_geocoder
import numpy as np
import geopy
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

def generate_cercanias_map():

    file_to_open = Path('Data/madrid/trains/station_list.csv')
    subway_map = nx.Graph()

    routes_and_stations = {}
    complex_to_station_dict = {}
    """ CÓDIGO	DESCRIPCION	LATITUD	LONGITUD	DIRECCIÓN	C.P.	POBLACION	PROVINCIA	Fichas	Túneles lavado"""
    with open(file_to_open, 'r') as f:
        next(f)  # skip header row
        for row in f:
            station_data = row.split(';')
            station_id = int(station_data[0])  # station code
            station_name = station_data[1]  # description
            station_lat_y = float(station_data[2])  # Latitude
            station_long_x = float(station_data[3])  # Longtitude
            _ = station_data[4]  # Direction? ??
            station_zip = station_data[5]  # probably codigo postal (postal code). Wish NYC did this.
            station_region = station_data[6]  # poblacion? probably region
            _ = station_data[7]  # province (pretty much madrid with a few exceptions)


            if station_id >= 9999999:
                coordinates = (station_lat_y, station_long_x)
                locator = Nominatim(user_agent='myGeocoder')
                location = locator.reverse(coordinates)
                print(station_id, location.raw['address']['postcode'], station_zip, station_region)

            #Adding Station
            subway_map.add_node(station_id)
            subway_map.nodes[station_id]['routes'] = []
            subway_map.nodes[station_id]['x'] = station_long_x
            subway_map.nodes[station_id]['y'] = station_lat_y
            subway_map.nodes[station_id]['pos'] = (station_long_x, station_lat_y)
            subway_map.nodes[station_id]['div'] = 'nodiv'
            subway_map.nodes[station_id]['name'] = station_name
            subway_map.nodes[station_id]['region'] = station_region
            subway_map.nodes[station_id]['zip'] = station_zip

    #Adding routes and edges
    file_to_open = Path('Data/madrid/parsed/madrid_our_routing_simple.csv')
    with open(file_to_open, 'r') as f:
        """Station Id,Station Name,Route,Stop Order,CIVIS Stop Order,Reverse Order,CIVIS Reverse"""
        next(f)
        previous_station = -1
        for row in f:
            station_data = row.split(',')
            station_id = int(station_data[0])
            station_name = station_data[1]
            station_route = station_data[2]
            station_stop_order = station_data[3]
            station_civis_order = station_data[4]  # TODO? we won't build CIVIS routes for now

            routes_and_stations.setdefault(station_route, []).append(station_id)

            #ignore stations not on the route for linkage?
            if len(station_stop_order) > 0:
                station_stop_order = int(station_stop_order)
                if station_stop_order > 0:  # not a terminal station (or rather the terminal at 0)
                    subway_map.add_edge(previous_station, station_id)

                previous_station = station_id

    #Setting some default node attributes
    nx.set_node_attributes(subway_map, EnvParams.NODE_TYPE_STATION, 'type')
    nx.set_node_attributes(subway_map, 0, 'exposure')
    nx.set_node_attributes(subway_map, 0, 'flow')



    #update flow and population data
    # TODO: actually do
    nx.set_node_attributes(subway_map, 100000, 'flow')
    nx.set_node_attributes(subway_map, 100000, 'population')
    nx.set_node_attributes(subway_map, 0.5, 'commuter_ratio')


    #update_flow_data(subway_map, 'Turnstile_Data.csv', complex_to_station_dict, date_start, date_end)
    #update_population_flow_data(subway_map, location='NYC')

    MADRID_CENTER = [18000] # Cercanias central stations. atocha only.

    for station_id in subway_map:
        station_shortest_path = 999999
        for dest_id in MADRID_CENTER:
            path_len = nx.algorithms.shortest_path_length(subway_map, station_id, dest_id)
            if path_len < station_shortest_path:
                station_shortest_path = path_len
        # really the 'commute distance'
        subway_map.nodes[station_id]['commute_time'] = station_shortest_path

    return subway_map, routes_and_stations


def generate_geometric_map(type="sierpinski"):
    file_to_open = Path('Data/Theory/ss_' + type + '.csv')
    # TODO: catch in case of stupidity?
    # Our simplified subway has no complexes. Routes and stations only.
    routes_and_stations = {}
    subway_map = nx.Graph()
    with open(file_to_open, 'r') as f:
        next(f)
        for row in f:
            #REMINDER TODO: FILL OUT ROUTE/station data! trivial.
            route_data = row.strip().split(',')
            route_name = route_data.pop(0)
            route_list = list(filter(None, route_data))
            previous_station_id = -1
            for station in route_list:
                station_id = int(station)
                #sets if exists, appends if not TODO: redo the other way of doing things.
                routes_and_stations.setdefault(route_name, []).append(station_id)
                #TODO: encapsulate this (almost same as generate_nyc_subway_map)
                #Builds the stations
                if not subway_map.has_node(station_id):
                    subway_map.add_node(station_id)
                    subway_map.nodes[station_id]['routes'] = [route_name]
                    #subway_map.nodes[station_id]['x'] = station_long_x
                    #subway_map.nodes[station_id]['y'] = station_lat_y
                    #subway_map.nodes[station_id]['pos'] = (station_long_x, station_lat_y)
                    #subway_map.nodes[station_id]['div'] = division_id
                    #subway_map.nodes[station_id]['name'] = stop_name
                else:
                    subway_map.nodes[station_id]['routes'].append(route_name)

                #Builds their connections
                if previous_station_id != -1:
                    subway_map.add_edge(int(previous_station_id), int(station_id))
                previous_station_id = station_id

    nx.set_node_attributes(subway_map, EnvParams.NODE_TYPE_STATION, 'type')
    nx.set_node_attributes(subway_map, 0, 'exposure')
    nx.set_node_attributes(subway_map, 0, 'flow')
    return subway_map, routes_and_stations

def generate_moskva_subway_map():
    """This is even more straightforward, but we have to pull data from elsewhere and add interchange links ourselves"""
    """i.e. novokuznetskaya - tretyakovskaya"""
    """Line,LineColor,Name,PseudoID,Latitude,Longitude,Order"""
    """Калининская,FFCD1C,Новокосино,55.745113,37.864052,0"""
    """Note: I coded pseudoID for each station"""
    """Note: GPS Coords vary slightly for a station based on what line it is on. whatever?"""
    """Also: Moscow subway lines have numbers as identifiers, but this guy used their names. whatever (for now)"""
    """Note: We also depend on the list being ordered by line and then route ordering"""
    # TODO: circular lines are not closed (they are incorrect)
    # TODO: these stations are not part of gcc  #{86, 23, 186, 28, 189, 190, 31} <-- due to missing ped. links
    subway_map = nx.Graph()
    file_to_open = Path('Data/Moscow/Subway/list_of_moscow_metro_stations.csv')
    routes_and_stations = {}
    with codecs.open(file_to_open, 'r', encoding='utf8') as f:
        next(f)  # skip header row
        current_line = ""
        last_station_order = -1  # will be used for some error checking
        last_station_id = -1
        for row in f:
            station_data = row.split(',')
            line_name = translit(station_data[0], 'ru', reversed=True)
            line_color = station_data[1]
            station_name = translit(station_data[2], 'ru', reversed=True)
            station_id = int(station_data[3])
            station_lat_y = float(station_data[4])
            station_long_x = float(station_data[5])
            station_order = int(station_data[6])

            if subway_map.has_node(station_id):
                subway_map.nodes[station_id]['routes'].append(line_name)
            else:
                # Add Station if it does not exist.
                subway_map.add_node(station_id)
                subway_map.nodes[station_id]['x'] = station_long_x
                subway_map.nodes[station_id]['y'] = station_lat_y
                subway_map.nodes[station_id]['pos'] = (station_long_x, station_lat_y)
                subway_map.nodes[station_id]['div'] = ""
                subway_map.nodes[station_id]['name'] = station_name
                subway_map.nodes[station_id]['routes'] = [line_name]

            # Adding connections on the same line
            if station_order == 0:
                current_line = line_name
                routes_and_stations[line_name] = [station_id]
            else:
                routes_and_stations[line_name].append(station_id)
                #if current_line != line_name or station_order <= last_station_order:
                    # Some sanity check (may not be necessary, but someone might rearrange the list)
                #    print('WARNING! REVIEW:', station_id, line_name, station_order)
                #else:
                subway_map.add_edge(station_id, last_station_id)

            last_station_id = station_id
            last_station_order = station_order

            # Adding any pedestrian transfers
            #TODO: There are pedestrian transfers. esp at big central stations
            #TODO: i.e. novokuznetskaya + tretyakovskaya

    # Adding circular links TODO: kludgy, no?
    subway_map.add_edge(19, 109)  # koltsevaya
    subway_map.add_edge(113, 87)  # МЦК

    nx.set_node_attributes(subway_map, EnvParams.NODE_TYPE_STATION, 'type')
    nx.set_node_attributes(subway_map, 0, 'exposure')
    nx.set_node_attributes(subway_map, 0, 'flow')

    return subway_map, routes_and_stations
def generate_LON_subway_map():
    subway_map = nx.Graph()
    routes_and_stations = {}

    # Stations
    file_to_open = Path('Data/London/Subway/Stations.csv')
    """id","latitude","longitude","name","display_name","zone","total_lines","rail,borough,Comments"""
    borough_to_station_dict = {}
    with open(file_to_open, 'r') as f:
        next(f)
        for row in f:
            station_data = row.split(',')
            station_id = int(station_data[0])  # station id as int (we'll try to keep this convention)
            station_lat_y = float(station_data[1])
            station_long_x = float(station_data[2])
            stop_name = station_data[3]
            _ = station_data[4]
            zone = float(station_data[5])  # zone
            _ = station_data[6]
            _ = station_data[7]
            station_borough = station_data[8]

            subway_map.add_node(station_id)
            subway_map.nodes[station_id]['x'] = station_long_x
            subway_map.nodes[station_id]['y'] = station_lat_y
            subway_map.nodes[station_id]['pos'] = (station_long_x, station_lat_y)
            subway_map.nodes[station_id]['name'] = stop_name
            subway_map.nodes[station_id]['commute_time'] = 2 * zone + 1
            subway_map.nodes[station_id]['region'] = station_borough
            subway_map.nodes[station_id]['zip'] = station_borough

            borough_to_station_dict.setdefault(station_borough, []).append(station_id)

            #For finding the borough of the station initially
            if station_id >= 99999:  # in [37,46,50,51,53,62,68,88,158,168,214,256,280]:
                coordinates = (station_lat_y, station_long_x)
                locator = Nominatim(user_agent='myGeocoder')
                location = locator.reverse(coordinates)
                #London does a lot of things well, but sometimes no 'borough' sorting
                raw_string = str(location.raw)
                #print(raw_string)
                try:
                    borough_name = raw_string.split('London Borough of ')[1].split(',')[0]
                except:
                    borough_name = raw_string

                print(station_id, borough_name)

    # Routes
    file_to_open = Path('Data/London/Subway/Routes.csv')
    with open(file_to_open, 'r') as f:
        """line","name","colour","stripe"""
        next(f)
        for row in f:
            route_data = row.split(',')
            route_id = int(route_data[0])
            routes_and_stations[route_id] = []

    # Routing Data
    nx.set_node_attributes(subway_map, [], 'routes')
    file_to_open = Path('Data/London/Subway/Routing.csv')
    with open(file_to_open, 'r') as f:
        next(f)
        """station1","station2","line"""
        for row in f:
            routing_data = row.split(',')
            station_1 = int(routing_data[0])
            station_2 = int(routing_data[1])
            route_id = int(routing_data[2])
            subway_map.add_edge(station_1, station_2)

            if station_1 not in routes_and_stations[route_id]:
                routes_and_stations[route_id].append(station_1)
            if station_2 not in routes_and_stations[route_id]:
                routes_and_stations[route_id].append(station_2)

        for route in routes_and_stations:
            for station in routes_and_stations[route]:
                subway_map.nodes[station]['routes'].append(route)

    # Flow Data
    nx.set_node_attributes(subway_map, 0.5, 'commuter_ratio')
    nx.set_node_attributes(subway_map, 10000, 'flow')

    # Population Data
    borough_pop_dict = {}  #TODO: this is useful later? I forget.
    file_to_open = Path('Data/London/Case Data/london_pop_by_borough.csv')
    """Borough,Population,Borough Code"""
    with open(file_to_open, 'r') as f:
        next(f)
        for row in f:
            borough_data = row.replace('\n', '').split(',')
            borough_name = borough_data[0]
            borough_population = int(borough_data[1])

            if borough_name in ['Bexley', 'Bromley', 'Croydon', 'Kingston upon Thames', 'Sutton']: #skip areas with no stations
                continue

            borough_pop_dict[borough_name] = borough_population
            if borough_name not in borough_to_station_dict.keys():
                continue

            borough_stations = borough_to_station_dict[borough_name]

            for station_id in borough_stations:
                station_population = borough_population / len(borough_stations)
                subway_map.nodes[station_id]['population'] = station_population

    for key in borough_pop_dict:
        if key not in borough_to_station_dict.keys():
            print('Warning, adding borough with no stations:', key)

    # Other Data
    nx.set_node_attributes(subway_map, EnvParams.NODE_TYPE_STATION, 'type')
    nx.set_node_attributes(subway_map, 0, 'normalized_hotspot')

    # Remove subway stations in other cities
    stations_in_other_cities = [37, 46, 50, 51, 53, 62, 68, 88, 158, 168, 214, 256, 280, 6]
    for station in stations_in_other_cities:
        subway_map.remove_node(station)

    return subway_map, routes_and_stations

def generate_NYC_subway_map():
    """This is pretty straightforward as NYC keeps station data in a csv. In principle, we should probably
    make this a general import, but in reality, who is going to format their station data like NYC MTA?"""
    """Rant section:
    what is this data?!
    167,167,A32,IND,8th Av - Fulton St,W 4 St,M,A C E,Subway,40.732338,-74.000495,Uptown - Queens,Downtown & Brooklyn
    167,167,D20,IND,6th Av - Culver,W 4 St,M,B D F M,Subway,40.732338,-74.000495,Uptown - Queens,Downtown & Brooklyn
    """
    #TODO: some thinking needs to be done about station 167. We need to change it to a complex.
    #TODO: as it stands, 2nd node overwrites first node. by luck or good programming, all routes are preserved.
    #TODO: (line would be overwritten)
    #TODO: NYC-specific eccentricity calculation should be generalized.

    """Station ID,Complex ID,GTFS Stop ID,Division,Line,Stop Name,Borough,Daytime Routes,Structure,GTFS Latitude,GTFS Longitude,North Direction Label,South Direction Label"""
    subway_map = nx.Graph()
    file_to_open = Path('Data/NYC/Subway/Stations.csv')
    routes_and_stations = {}
    complex_to_station_dict = {}
    modzcta_to_stations_dict = {}
    zip_to_modzcta = {} #TODO: this last dictionary could be stored elsewhere.
    #TODO: more importantly, maybe just reverse geocode the modzcta... jeez.
    #I Mean... did they even code the zip codes right or just randomly slap them on?!
    zip_to_modzcta['10153'] = '10022'
    zip_to_modzcta['11227'] = '11217'
    zip_to_modzcta['10000'] = '10007'
    zip_to_modzcta['10279'] = '10007'
    zip_to_modzcta['12692'] = '11692'  # this was clearly an error. fixed in file anyway.
    zip_to_modzcta['10020'] = '10019'  # rockefeller center -> midtown
    zip_to_modzcta['11451'] = '11432'
    zip_to_modzcta['10115'] = '10035'  # east harlem
    zip_to_modzcta['10107'] = '10019'  # 50th st. -> midtown
    zip_to_modzcta['10199'] = '10001'

    with open(file_to_open, 'r') as f:
        next(f)  # skip header row
        complex_dict = {}  # dictionary of complexes. values = stations at that complex
        for row in f:
            station_data = row.split(',')
            station_id = int(station_data[0])  # station id as int (we'll try to keep this convention)
            complex_id = station_data[1]  # complex
            _ = station_data[2]  # GTFS Stop ID
            division_id = station_data[3]  # Division. These are not ints!
            _ = station_data[4]  # Line Caution!! Lines != Routes, not what you think it is!
            stop_name = station_data[5]  # Stop Name
            station_borough = station_data[6]  # Borough
            routes = station_data[7] # daytime(?) Routes
            _ = station_data[8]  #
            station_lat_y = float(station_data[9])  # Latitude
            station_long_x = float(station_data[10])  # Longtitude
            _ = station_data[11] #north label
            _ = station_data[12] #south label
            station_zip = station_data[13] #TODO: convert this to a string too eventually

            if station_zip in zip_to_modzcta.keys():
                station_zip = zip_to_modzcta[station_zip]

            #done once to get the zip codes for all stations. Keeping this code for... posterity I guess.
            #station 225, 315, 328, 330, 466, 468 errors. no zip code.
            #some zips are weird and I went back and fixed them (station 115)
            if station_id >= 99999:
                print(station_id)
                coordinates = (station_lat_y, station_long_x)
                locator = Nominatim(user_agent='myGeocoder')
                location = locator.reverse(coordinates)
                actual_zip = location.raw['address']['postcode']
                if actual_zip != station_zip:  #-.- need to validate MTA's zip codes
                    print(station_id, actual_zip, station_zip)


            #TODO: turns out complexID + divid is not a unique identifier! see 467, 468
            complex_to_station_dict[(complex_id, division_id)] = station_id
            modzcta_to_stations_dict.setdefault(station_zip, []).append(station_id)

            # We're not counting Staten Island
            if 'SIR' in routes:
                continue

            #Adding Station
            subway_map.add_node(station_id)
            subway_map.nodes[station_id]['routes'] = routes.split()
            subway_map.nodes[station_id]['x'] = station_long_x
            subway_map.nodes[station_id]['y'] = station_lat_y
            subway_map.nodes[station_id]['pos'] = (station_long_x, station_lat_y)
            subway_map.nodes[station_id]['div'] = division_id
            subway_map.nodes[station_id]['name'] = stop_name
            subway_map.nodes[station_id]['region'] = station_borough
            subway_map.nodes[station_id]['zip'] = station_zip

            #Adding any transfers
            if complex_id in complex_dict:
                for transfer_station_id in complex_dict[complex_id]:
                    subway_map.add_edge(transfer_station_id, station_id)
                complex_dict[complex_id].append(station_id)
            else:
                complex_dict[complex_id] = [station_id]

            #Adding edges between stations
            # TODO: this is crappy programming, but, besides geolocation, there's no good way to discover direct connections
            """ok here's what we actually do: we add the station and their xy coords to a list by route
            we order the routes by xy position (look up how to, but euclidean probably suffices) 
            we build those and only those edges"""
            # you know, this doesn't even guarantee correctness. just logical correctness.

            for route in routes.split():
                routes_and_stations.setdefault(route, []).append(station_id)

    build_edges_from_file = True
    # Builds the edges between stations based on our own listing of correct edges between stations
    # The first column in each row is the route name or a fake route name
    # successor columns are consecutive stations. just link em up
    # TODO: note that in ods, racepark or aqueduct or something is not fixed.
    if build_edges_from_file:
        file_fixed_routings = Path('Data/NYC/Subway/Fixed_Routings.csv')
        with open(file_fixed_routings, 'r') as f_routes:
            for row in f_routes:
                route_data = row.split(',')[1:]
                previous_station = -1
                for station in route_data:
                    if previous_station != -1:
                        subway_map.add_edge(int(previous_station), int(station))
                    previous_station = station


    nx.set_node_attributes(subway_map, EnvParams.NODE_TYPE_STATION, 'type')
    nx.set_node_attributes(subway_map, 0, 'exposure')
    nx.set_node_attributes(subway_map, 0, 'flow')
    nx.set_node_attributes(subway_map, 0, 'normalized_hotspot')

    # TODO: Of course these should be model params, but we haven't the least  idea how to use them yet.
    date_start = datetime.datetime(2020, 2, 16, 0, 0)  # inclusive
    date_end = datetime.datetime(2020, 3, 7, 0, 0)  # inclusive

    # I suppose the nice thing about python is I don't have too much to update if I need to return something new.
    update_flow_data(subway_map, 'Turnstile_Data.csv', complex_to_station_dict, date_start, date_end)
    update_population_flow_data(subway_map, location='NYC', zc_to_stations_dict=modzcta_to_stations_dict)

    NYC_TIMES_SQUARE = [11, 317, 467, 468]
    NYC_GRAND_CENTRAL = [465, 469, 402, ]

    # Eigenvalue centrality
    # centrality = nx.eigenvector_centrality(subway_map)
    # print({k: v for k, v in sorted(centrality.items(), key=lambda item: item[1], reverse=True)})

    #TODO: you can do this in subwaygraph after you've created the shortest path dictionary

    for station_id in subway_map:
        station_shortest_path = 999999
        for dest_id in NYC_GRAND_CENTRAL + NYC_TIMES_SQUARE:
            path_len = nx.algorithms.shortest_path_length(subway_map, station_id, dest_id)
            if path_len < station_shortest_path:
                station_shortest_path = path_len

        # This is really a proxy for ... additional exposure due to commute time. Hmm....
        subway_map.nodes[station_id]['commute_time'] = station_shortest_path + 1

        #TODO: this sucks a bit.
        #sqrt_eccentricity = math.sqrt(nx.algorithms.distance_measures.eccentricity(subway_map,station_id))
        #subway_map.nodes[station_id]['commute_time'] = sqrt_eccentricity

    return subway_map, routes_and_stations

# for NYC, 3 week total passenger flow was about 124975642
def update_flow_data(subway_map, flow_files, complex_to_station_dict, date_start, date_end):
    """this will look substantially different from our geographically/train based map.
    we will look at the turnstile data from Mar 1 - Mar 21 when the pandemic was starting
    so... maybe this function should eventually take unix time etc., but we'll hardcode it for now"""
    # Protip: you can get station id from complex id + division and referencing stations.csv
    """stop_name,daytime_routes,division,line,borough,structure,gtfs_longitude,gtfs_latitude,complex_id,date,entries,exits"""
    """Astoria - Ditmars Blvd,N W,BMT,Astoria,Q,Elevated,-73.912034,40.775036,1,2020-01-01,7024,7060"""
    # So we filter down by date, sum up the entrance and exits, and call it 'passenger flow' node attribute.
    # Remember that complex id and div id are strings!
    file_to_open = Path('Data/NYC/Subway/' + flow_files)
    total_flow = 0
    per_day_trip_modifier = 2 * (date_end - date_start).days  # in/out = 1 trip, #days = number of days
    with open(file_to_open, 'r') as f:
        next(f)  # skip header row
        for row in f:
            flow_data = row.split(',')
            _ = flow_data[0]  # stop name
            _ = flow_data[1]  # daytime routes
            flow_division = flow_data[2]  # division
            _ = flow_data[3]  # line
            _ = flow_data[4]  # borough
            _ = flow_data[5]  # structure
            _ = flow_data[6]  # gtfs longtitude
            _ = flow_data[7]  # gtfs latitude
            flow_complex_id = flow_data[8]  # complex id
            flow_date = datetime.datetime.strptime(flow_data[9], '%Y-%m-%d')  # date
            flow_in = int(flow_data[10])  # entries
            flow_out = int(flow_data[11])  # exits
            if date_end >= flow_date >= date_start:
                if (flow_complex_id, flow_division) in complex_to_station_dict:
                    station_id = complex_to_station_dict[(flow_complex_id, flow_division)]
                    if station_id in subway_map.nodes():  # we may have removed some stations (cough, staten island)
                        subway_map.nodes[station_id]['flow'] += (flow_in + flow_out) / per_day_trip_modifier
                        total_flow += (flow_in + flow_out) / per_day_trip_modifier

    # TODO: HACK ALERT! DUE TO ISSUES WITH COMPLEX/STATION DATA. REFERENCE COMPLEX_TO_STATION_DICT TODO:
    for station_id in subway_map.nodes():
        station_name = subway_map.nodes[station_id]['name']
        if subway_map.nodes[station_id]['flow'] == 0:
            estimated_flow = estimate_feature_from_nn(subway_map, 'flow', station_id, ignore_zeros=True)
            subway_map.nodes[station_id]['flow'] = estimated_flow
            #print('flow estimated!!', station_id, estimated_flow)
            total_flow += estimated_flow
            #print('Flow estimate:', station_id, station_name, subway_map.nodes[station_id]['flow'])
    print('trips per day:', total_flow)
    return total_flow


def update_population_flow_data(network, location='NYC', pop_files=None, zc_to_stations_dict=None):
    """creates population data, normalizes flow to population. Really requires a zipdict"""
    if location == 'NYC':
        #The link below is useful for some approximate data while we make the real thing.
        """https://psplvv-ctwprtla.nyc.gov/assets/planning/download/pdf/planning-level/housing-economy/nyc-ins-and-out-of-commuting.pdf"""

        # Percentage of total population and flow percentage
        # Bronx     0.1806  0.07    2.53
        # Brooklyn  0.3226  0.20    1.61
        # Manhattan 0.2074  0.60    0.34
        # Queens    0.2894  0.13    2.30

        #nyc_population = 7853000  # Population NOT on Staten Island

        # total commuters should be about 3 million
        #TODO: base this on popdict... valid zipcodes only.
        pop_dict = get_population_by_modzcta_dict()
        keys_to_remove = []
        for key in pop_dict.keys():
            if key not in zc_to_stations_dict.keys():
                keys_to_remove.append(key)
        for key in keys_to_remove:
            pop_dict.pop(key)

        total_population = sum(pop_dict.values())
        print('population considered:', total_population)

        # Used to see how commuter ratio is adjusted
        adjustments_by_borough = {EnvParams.BOROUGH_MANHATTAN: [],
                                  EnvParams.BOROUGH_QUEENS: [],
                                  EnvParams.BOROUGH_BROOKLYN: [],
                                  EnvParams.BOROUGH_BRONX: []}
        for n in network.nodes():
            #Write population and commuter data
            # TODO: population data should be independent of flow data
            # commuter ratio too...

            zipcode = network.nodes[n]['zip']
            stations_in_zc = zc_to_stations_dict[zipcode]
            if zipcode not in pop_dict.keys():
                print('Warning! zip', zipcode, 'not in pop dict!')
                zipcode='10019'
            population_in_zc = pop_dict[zipcode]

            station_population = population_in_zc / len(stations_in_zc)
            if DisplayParams.PRINT_DEBUG and station_population >= 40000:
                print('High Population Station', n, zipcode, station_population, network.nodes[n]['name'])
            #network.nodes[n]['population'] = min(40000, station_population) #cap station population to 40k
            network.nodes[n]['population'] = station_population

            if DisplayParams.PRINT_DEBUG and 42 <= n <= 55:
                print('numbers for station', n, network.nodes[n]['flow'], network.nodes[n]['population'])

            flow = network.nodes[n]['flow']
            population = network.nodes[n]['population']
            name = network.nodes[n]['name']
            borough = network.nodes[n]['region']


            if borough == EnvParams.BOROUGH_BRONX:
                commuter_ratio = EnvParams.COMMUTER_RATIO_BRONX
            elif borough == EnvParams.BOROUGH_BROOKLYN:
                commuter_ratio = EnvParams.COMMUTER_RATIO_BROOKLYN
            elif borough == EnvParams.BOROUGH_MANHATTAN:
                commuter_ratio = EnvParams.COMMUTER_RATIO_MANHATTAN
            elif borough == EnvParams.BOROUGH_QUEENS:
                commuter_ratio = EnvParams.COMMUTER_RATIO_QUEENS
            else:
                print('Borough ID error', n, borough)

            #if population < 5000 and borough != 'M':
            #    print('low population', n, borough, population)

            number_of_commuters = population * commuter_ratio
            # if the flow numbers simply cannot be representative, adjust the ratio down until it can
            adjusted = False
            if flow < number_of_commuters and EnvParams.ADJUST_COMMUTERS_BY_FLOW: #if the only people using this station was its own commuters
                commuter_ratio = flow / population
                adjustments_by_borough[borough].append(commuter_ratio)


            network.nodes[n]['commuter_ratio'] = commuter_ratio

        if DisplayParams.PRINT_DEBUG:
            # this analysis is only valid if commuter ratio params are 1 or something high)
            print('Recommended Commuter Ratios Based on Residential Areas:')
            for borough in adjustments_by_borough:
                if len(adjustments_by_borough[borough]) > 0:
                    print(borough, statistics.median(adjustments_by_borough[borough]))

            for borough in adjustments_by_borough:
                for adjustment in adjustments_by_borough[borough]:
                    print(borough, adjustment)

        #print(total_commuters) #this should be about 3 million, total ridership should be 7 million


def get_population_by_modzcta_dict():
    # it appears this file (and all its successors) has stopped with the crappy NA and zip code 99999 crap.
    # Not that it matters.
    file_to_open = 'Data/NYC/Case_Death_Recovery/data-by-modzcta.csv'
    # MODIFIED_ZCTA,NEIGHBORHOOD_NAME,BOROUGH_GROUP,COVID_CASE_COUNT,COVID_CASE_RATE,POP_DENOMINATOR,COVID_DEATH_COUNT,COVID_DEATH_RATE,PERCENT_POSITIVE,TOTAL_COVID_TESTS
    modzcta_pop_dict = {}

    with open(file_to_open, 'r') as f:
        next(f)
        for row in f:
            modzcta_data = row.split(',')
            modzcta = modzcta_data[0]  # modzcta (string)
            population = float(modzcta_data[5])  # population (...decimal)
            modzcta_pop_dict[modzcta] = population
    return modzcta_pop_dict

def get_feature_sum(network, feature):
    feature_total = 0
    for n in network.nodes():
        feature_total += network.nodes[n][feature]
    return feature_total

def estimate_feature_from_nn(network, feature, node, ignore_zeros=True):
    neighbors = list(nx.Graph.neighbors(network, node))
    total_feature_value = 0
    total_neighbors_counted = 0
    for nn in neighbors:
        feature_value = network.nodes[nn][feature]
        if feature_value == 0 and ignore_zeros:
            total_neighbors_counted -= 1  # discounts the counted neighbor TODO: kluuudgy
        total_neighbors_counted += 1
        total_feature_value += feature_value
    return total_feature_value / total_neighbors_counted

def generate_simple_triangle_map():
    """A fake subway. We'll need a naming convention for stations in the real one"""
    routes_and_stations = {}
    subway_map = nx.Graph()
    subway_map.add_nodes_from([1, 2, 3])

    subway_map.add_edge(1, 2)
    subway_map.add_edge(2, 3)
    subway_map.add_edge(3, 1)

    subway_map.nodes[1]['routes'] = [1, 3]
    subway_map.nodes[2]['routes'] = [1, 2]
    subway_map.nodes[3]['routes'] = [2, 3]

    routes_and_stations[1] = [1, 2]
    routes_and_stations[2] = [2, 3]
    routes_and_stations[3] = [3, 1]

    nx.set_node_attributes(subway_map, EnvParams.NODE_TYPE_STATION, 'type')
    nx.set_node_attributes(subway_map, 0, 'exposure')
    nx.set_node_attributes(subway_map, 0, 'flow')

    return subway_map, routes_and_stations


def get_subway_map(map_type):
    """main wrapper to return different maps. the below should really be an enum."""
    # TODO: This is the crappiest way of updating abstraction I ever did see.
    # TODO: It's high time *everyone* returned an OurGraph
    subway_map = nx.Graph()
    if map_type == SimulationParams.MAP_TYPE_TEST:
        return generate_simple_triangle_map()
    if map_type == SimulationParams.MAP_TYPE_NYC:
        return generate_NYC_subway_map()
    if map_type == SimulationParams.MAP_TYPE_LONDON:
        return generate_LON_subway_map()
    if map_type == SimulationParams.MAP_TYPE_GEOMETRIC_SIERPINSKI:
        return generate_geometric_map('sierpinski')
    if map_type == SimulationParams.MAP_TYPE_GEOMETRIC_CIRCULAR:
        return generate_geometric_map('moscow')
    if map_type == SimulationParams.MAP_TYPE_GEOMETRIC_GRID:
        return generate_geometric_map('grid')
    if map_type == SimulationParams.MAP_TYPE_MOSCOW:
        return generate_moskva_subway_map()
    if map_type == SimulationParams.MAP_TYPE_TREN_MADRID:
        return generate_cercanias_map()

    return subway_map

def generate_fake_world_map():
    air_graph = nx.Graph()
    air_graph.add_nodes_from([1, 2, 3])

    air_graph.add_edge(1, 2)
    air_graph.add_edge(2, 3)
    air_graph.add_edge(3, 1)

    air_graph.nodes[1]['flow'] = 100
    air_graph.nodes[2]['flow'] = 100
    air_graph.nodes[3]['flow'] = 100

    nx.set_node_attributes(air_graph, EnvParams.NODE_TYPE_STATION, 'type') #LOL?
    nx.set_node_attributes(air_graph, 0, 'exposure')

    return AirGraph(air_graph, 300)

def generate_wan_map():
    """1,"Goroka Airport","Goroka","Papua New Guinea","GKA","AYGA",-6.081689834590001,145.391998291,5282,10,"U","Pacific/Port_Moresby","airport","OurAirports"""
    airway_map = nx.Graph()
    # Build Nodes
    file_to_open = Path('Data/World/Air_Routes/airports.dat')
    with codecs.open(file_to_open, 'r', encoding='utf8') as f:
        csv_reader = csv.reader(f, delimiter=',', quotechar='"') #TODO, really this should be done everywhere
        for wan_data in csv_reader:
            airport_id = int(wan_data[0])  # airport uid (for open flights)
            airport_name = wan_data[1]  # airport name
            _ = wan_data[2]  # airport region??
            _ = wan_data[3]  # airport country
            airport_iata_code = wan_data[4]  # airport IATA code
            _ = wan_data[5]  # other airport code
            airport_lat_y = float(wan_data[6])  # airport latitude
            airport_long_x = float(wan_data[7])  # airport longtitude
            # bunch of other fields i don't care about

            airway_map.add_node(airport_id)
            airway_map.nodes[airport_id]['x'] = airport_long_x
            airway_map.nodes[airport_id]['y'] = airport_lat_y
            airway_map.nodes[airport_id]['pos'] = (airport_long_x, airport_lat_y)
            airway_map.nodes[airport_id]['name'] = airport_name
            airway_map.nodes[airport_id]['IATA'] = airport_iata_code

    # Build Edges (without weights)
    file_to_open = Path('Data/World/Air_Routes/routes.dat')
    with codecs.open(file_to_open, 'r', encoding='utf8') as f:
        """2B,410,AER,2965,KZN,2990,,0,CR2"""
        for row in f:
            route_data = row.split(',')
            _ = route_data[0]
            _ = route_data[1]
            src_iata_code = route_data[2]  # source name
            src_id = route_data[3]  # source uid
            dst_iata_code = route_data[4]  # destination name
            dst_id = route_data[5]  # destination uid
            # TODO: omg... in the routing data, HYD is given no id, despite it having one in airports.dat...
            # convert all IST routes to ISL routes. 1701 is labelled ISL and yet there are 1701,IST routes... whatever.
            # HYD - 12087
            # IST = 1701, ISL = 13696
            if 'HYD' in src_iata_code:
                src_id = 12087
            if 'HYD' in dst_iata_code:
                dst_id = 12087
            if 'IST' in src_iata_code or 'ISL' in src_iata_code or src_id == '1701':
                src_id = 13696
            if 'IST' in dst_iata_code or 'ISL' in dst_iata_code or dst_id == '1701':
                dst_id = 13696

            if dst_id != r'\N' and src_id != r'\N' and \
                airway_map.has_node(int(src_id)) and airway_map.has_node(int(dst_id)): # TODO: wow...

                airway_map.add_edge(int(src_id), int(dst_id))
            #bunch of other fields i don't care about

    nx.set_node_attributes(airway_map, 0, 'flow')
    nx.set_node_attributes(airway_map, EnvParams.NODE_TYPE_STATION, 'type')  # LOL?
    nx.set_node_attributes(airway_map, 0, 'exposure')

    return AirGraph(airway_map)

def generate_curated_airway_map():
    """IATA Code,Passengers,Municipality,Comments"""
    """Really, if it doesn't have an IATA code, is it that important?"""

    # TODO: this is also kind of a waste?
    airway_map = generate_wan_map()
    nx_graph = airway_map.graph
    top_n_airports = 999  # TODO: this is a param

    nodes_to_keep = []
    #pare down the airports (nodes)
    file_to_open = Path('Data/World/Air_Routes/Airports_curated_HLC.csv')
    with codecs.open(file_to_open, 'r', encoding='utf8') as f:
        next(f)
        i = 0
        iata_to_id_reverse_lookup = {}
        for row in f:
            if i >= top_n_airports:
                break
            i += 1

            airport_data = row.split(',')
            airport_iata_code = airport_data[0]  # IATA Code
            airport_flow = airport_data[1]  # Passengers
            airport_city = airport_data[2]  # Municipality (City)

            # TODO: this would have been better if you had made an id <> IATA dict
            for node_id in nx_graph.nodes():
                node = nx_graph.nodes[node_id]
                if node['IATA'] == airport_iata_code:
                    nodes_to_keep.append(node_id)
                    node['flow'] = int(airport_flow)
                    node['city'] = airport_city
                    iata_to_id_reverse_lookup[airport_iata_code] = node_id
                    break

    curated_nx_graph = nx.Graph.copy(nx_graph.subgraph(nodes_to_keep))

    # determine whether the flight is domestic
    nx.set_edge_attributes(curated_nx_graph, False, 'domestic')
    for u, v in curated_nx_graph.edges:
        coordinates_u = tuple(reversed(curated_nx_graph.nodes[u]['pos']))
        coordinates_v = tuple(reversed(curated_nx_graph.nodes[v]['pos']))
        curated_nx_graph.edges[u, v]['domestic'] = flight_is_domestic(coordinates_u, coordinates_v)


    # estimate all edge flows
    file_to_open = Path('Data/World/Air_Routes/Airport_pairs_curated_HLC.csv')
    with codecs.open(file_to_open, 'r', encoding='utf8') as f:
        '''IATA Airport 1,IATA Airport 2,,,Edge Flow,Comments'''
        next(f)

        nx.set_edge_attributes(curated_nx_graph, 0, 'pair_flow')
        for row in f:
            route_data = row.split(',')
            src_iata_code = route_data[0]  # IATA 1
            dst_iata_code = route_data[1]  # IATA 2
            edge_flow = route_data[4]  # edge data

            if src_iata_code in iata_to_id_reverse_lookup:
                src_id = iata_to_id_reverse_lookup[src_iata_code]
                if dst_iata_code in iata_to_id_reverse_lookup:
                    dst_id = iata_to_id_reverse_lookup[dst_iata_code]
                    # comment: man. I made this file. edge_flow is filled out for sure
                    if src_id in curated_nx_graph.nodes and dst_id in curated_nx_graph.nodes:
                        curated_nx_graph.add_edge(src_id, dst_id, pair_flow=int(edge_flow))

        for u, v, flow in curated_nx_graph.edges.data('pair_flow'):
            if flow == 0: #just take a random guess based on number of neighbors of both nodes
                domestic_multiplier = 5 #TODO: a param I guess


                #For u
                neighbors_u = list(nx.neighbors(curated_nx_graph, u))
                remaining_flow_u = curated_nx_graph.nodes[u]['flow']
                remaining_neighbors_u = len(neighbors_u)  #remaining _empty_ neighbors
                for neighbor_id in neighbors_u:
                    flow_to_neighbor = curated_nx_graph[u][neighbor_id]['pair_flow']
                    remaining_flow_u -= flow_to_neighbor
                    if flow_to_neighbor > 0:
                        remaining_neighbors_u -= 1
                    else: #if the neighbor also has to be weighted
                        if curated_nx_graph.edges[u, neighbor_id]['domestic']:
                            remaining_neighbors_u += domestic_multiplier - 1

                #For v TODO: copypasta
                neighbors_v = list(nx.neighbors(curated_nx_graph, v))
                remaining_flow_v = curated_nx_graph.nodes[v]['flow']
                remaining_neighbors_v = len(neighbors_v)
                for neighbor_id in neighbors_v:
                    flow_to_neighbor = curated_nx_graph[v][neighbor_id]['pair_flow']
                    remaining_flow_v -= flow_to_neighbor
                    if flow_to_neighbor > 0:
                        remaining_neighbors_v -= 1
                    else: #if the neighbor also has to be weighted
                        coordinates_n = tuple(reversed(curated_nx_graph.nodes[neighbor_id]['pos']))
                        if curated_nx_graph.edges[v, neighbor_id]['domestic']:
                            remaining_neighbors_v += domestic_multiplier - 1

                #The actual flow estimating
                if curated_nx_graph.edges[u, v]['domestic']: #your flight also has a multiplier of 5
                    flow_estimate = min(5*remaining_flow_u/remaining_neighbors_u, 5*remaining_flow_v/remaining_neighbors_v)
                else:
                    flow_estimate = min(remaining_flow_u/remaining_neighbors_u, remaining_flow_v/remaining_neighbors_v)
                if False: #TODO: some debug code to look at flow
                    if u == 3376 or v == 3376:
                        print('u:', u, remaining_flow_u, remaining_neighbors_u)
                        print('v:', v, remaining_flow_v, remaining_neighbors_v)
                        print('domestic:', curated_nx_graph.edges[u, v]['domestic'])
                        print('assigning flow', flow_estimate, 'to', u,v)
                if flow_estimate < 10000:
                    print('warning! low flow between', u, v, flow_estimate, 'automatically setting to 10k')
                    flow_estimate = 10000
                curated_nx_graph.edges[u, v]['pair_flow'] = flow_estimate

    return AirGraph(curated_nx_graph)

def flight_is_domestic(coordinates_u, coordinates_v):
    coordinates = coordinates_u,coordinates_v
    coord_data = reverse_geocoder.search(coordinates, mode=1)
    if coord_data[0]['cc'] == coord_data[1]['cc']:
        return True
    return False


def get_airway_map(map_type):
    airway_map = nx.Graph()
    if map_type == SimulationParams.MAP_TYPE_WORLD:
        return generate_wan_map()
    if map_type == SimulationParams.MAP_TYPE_FAKE_WORLD:
        return generate_fake_world_map()
    if map_type == SimulationParams.MAP_TYPE_HLC_CURATED_WAN:
        return generate_curated_airway_map()
    return AirGraph(airway_map)

def make_exit_nodes(subway_map):
    """Given a subway map, add a street-level exit node.
    27.05.2020: With no attributes (actual location), this is pretty trivial for now"""
    subway_with_exits = nx.Graph.copy(subway_map)
    node_index = len(subway_map.nodes()) + 1000 #TODO:  This is a dubious way to index
    for node in subway_map.nodes():
        subway_with_exits.add_node(node_index)
        #TODO: is there a way to do this in one line?
        subway_with_exits.nodes[node_index]['type'] = EnvParams.NODE_TYPE_STREET
        subway_with_exits.nodes[node_index]['routes'] = ""
        #TODO: probably not the best way to create a shadow
        subway_with_exits.nodes[node_index]['x'] = subway_map.nodes[node]['x'] + 0.01 #create a 'shadow'
        subway_with_exits.nodes[node_index]['y'] = subway_map.nodes[node]['y'] + 0.01 #create a 'shadow'
        subway_with_exits.nodes[node_index]['pos'] = \
            (subway_with_exits.nodes[node_index]['x'], subway_with_exits.nodes[node_index]['y'])
        subway_with_exits.nodes[node_index]['flow'] = 0

        subway_with_exits.add_edge(node_index, node)
        node_index += 1

    return subway_with_exits

