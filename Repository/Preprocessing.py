import datetime

import networkx as nx
from Parameters import SubwayParams
from pathlib import Path
# TODO: we need to refactor out the graph/map level things into a different file.
import itertools as it
import math

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
    """Station ID,Complex ID,GTFS Stop ID,Division,Line,Stop Name,Borough,Daytime Routes,Structure,GTFS Latitude,GTFS Longitude,North Direction Label,South Direction Label"""
    subway_map = nx.Graph()
    file_to_open = Path('Data/Stations.csv')
    routes_and_stations = {}
    complex_to_station_dict = {}
    with open(file_to_open, 'r') as f:
        next(f) #skip header row
        complex_dict = {} #dictionary of complexes. values = stations at that complex
        for row in f:
            station_data = row.split(',')
            station_id = int(station_data[0])  # TODO: We're making this an int as early as possible!
            complex_id = station_data[1]  # Complex ID. A string! If stations are part of the same complex, they need to be connected
            _ = station_data[2]  # GTFS Stop ID
            division_id = station_data[3]  # Division. These are not ints!
            _ = station_data[4]  # Line Caution!! Lines != Routes, not what you think it is!
            stop_name = station_data[5]  # Stop Name
            _ = station_data[6]  # Borough
            routes = station_data[7] # daytime(?) Routes
            _ = station_data[8]  #
            station_lat_y = float(station_data[9])  # Latitude
            station_long_x = float(station_data[10])  # Longtitude

            complex_to_station_dict[(complex_id, division_id)] = station_id

            # We're not counting Staten Island. I already duplicated Stations.csv in expectation of removing this trolly data
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
                if route not in routes_and_stations:
                    routes_and_stations[route] = [station_id]
                else:
                    routes_and_stations[route].append(station_id)

    build_edges_from_file = True
    # Builds the edges between stations based on our own listing of correct edges between stations
    # The first column in each row is the route name or a fake route name
    # successor columns are consecutive stations. just link em up
    #TODO: note that in ods, racepark or aqueduct or something is not fixed.
    if build_edges_from_file:
        file_fixed_routings = Path('Data/Fixed_Routings.csv')
        with open(file_fixed_routings, 'r') as f_routes:
            for row in f_routes:
                route_data = row.split(',')[1:]
                previous_station = -1
                for station in route_data:
                    if previous_station != -1:
                        subway_map.add_edge(int(previous_station), int(station))
                    previous_station = station


    make_best_guess_routes = False
    if make_best_guess_routes:
        "Adding Edges, a more logical approach (but still possibly crap, also might not matter)"
        "Best theoretical mathy approach would be to find the shortest hamiltonian path. but i am lazy"
        file_routing_by_id = Path('Data/Our_Routing_By_Id.csv')
        file_routing_by_name = Path('Data/Our_Routing_By_Name.csv')
        f_route_ids = open(file_routing_by_id, 'w')
        f_route_names = open(file_routing_by_name, 'w')

        for route in routes_and_stations:
            minX = -70
            maxX = -75
            minY = 42
            maxY = 38
            # TODO after thinking some more, just do something readable and logical and make an actual edge list later if needed.
            # TODO after writing this and still having to hack in some lines, I 100% approve of that idea.
            for station in routes_and_stations[route]:
                x_coord = subway_map.nodes[station]['x']
                y_coord = subway_map.nodes[station]['y']

                if x_coord < minX:
                    minX = x_coord
                if x_coord > maxX:
                    maxX = x_coord
                if y_coord < minY:
                    minY = y_coord
                if y_coord > maxY:
                    maxY = y_coord

            terminal_station = -1
            for station in routes_and_stations[route]:
                x_coord = subway_map.nodes[station]['x']
                y_coord = subway_map.nodes[station]['y']
                if (x_coord == minX and y_coord == minY) or (x_coord == minX and y_coord == maxY) or \
                    (x_coord == maxX and y_coord == minY) or(x_coord == maxX and y_coord == maxY):
                    terminal_station = station
                    break
            if route == 'F':
                terminal_station = 58
            if route == 'J':
                terminal_station = 278
            if route == 'Z':
                terminal_station = 278
            if route == 'M':
                terminal_station = 108
            if route == 'A':
                terminal_station = 203
            if route == 'C':
                terminal_station = 188
            if route == 'E':
                terminal_station = 278
            if route == '3':
                terminal_station = 436
            if route == '5':
                terminal_station = 359

            if terminal_station == -1:
                print('HACK WAS UNABLE TO FIND TERMINAL STATION FOR ROUTE', route)

            uncombined_stations = routes_and_stations[route].copy()
            last_station = terminal_station
            # TODO: we don't really need to rewrite (to validate every time)
            station_list = [terminal_station]
            station_list_names = [subway_map.nodes[terminal_station]['name']]
            x_coord_last = subway_map.nodes[last_station]['x']
            y_coord_last = subway_map.nodes[last_station]['y']
            uncombined_stations.remove(terminal_station)

            while(len(uncombined_stations) > 0):
                best_distance = 100
                best_candidate = -1
                #Find the closest station to our current endpoint
                for station_candidate in uncombined_stations:
                    candidate_distance = math.hypot(
                        x_coord_last - subway_map.nodes[station_candidate]['x'],
                        y_coord_last - subway_map.nodes[station_candidate]['y']
                    )
                    if candidate_distance < best_distance:
                        best_distance = candidate_distance
                        best_candidate = station_candidate

                #Add the edge
                subway_map.add_edge(last_station, best_candidate)

                #Make the new endpoint
                x_coord_last = subway_map.nodes[best_candidate]['x']
                y_coord_last = subway_map.nodes[best_candidate]['y']
                uncombined_stations.remove(best_candidate)
                last_station = best_candidate

                #Update the route list for validation
                station_list.append(last_station)
                station_list_names.append(subway_map.nodes[last_station]['name'])

            ids_as_csv = ','.join(map(str, station_list))
            names_as_csv = ','.join(map(str, station_list_names))

            f_route_ids.write(route + ',' + ids_as_csv + '\n')
            f_route_names.write(route + ',' + names_as_csv + '\n')

        f_route_ids.close()
        f_route_names.close()

    nx.set_node_attributes(subway_map, SubwayParams.NODE_TYPE_STATION, 'type')
    nx.set_node_attributes(subway_map, 0, 'viral_load')
    #Adding flowrate
    """this will look substantially different from our geographically/train based map.
    we will look at the turnstile data from Mar 1 - Mar 21 when the pandemic was starting
    so... maybe this function should eventually take unix time etc., but we'll hardcode it for now"""
    #Protip: you can get station id from complex id + division and referencing stations.csv
    """stop_name,daytime_routes,division,line,borough,structure,gtfs_longitude,gtfs_latitude,complex_id,date,entries,exits"""
    """Astoria - Ditmars Blvd,N W,BMT,Astoria,Q,Elevated,-73.912034,40.775036,1,2020-01-01,7024,7060"""
    #So we filter down by date, sum up the entrance and exits, and call it 'passenger flow' node attribute.
    #Remember that complex id and div id are strings!
    file_to_open = Path('Data/Turnstile_Data.csv')
    #TODO: Of course these should be model params, but we haven't the least  idea how to use them yet.
    date_start = datetime.datetime(2020, 3, 1, 0, 0) #inclusive
    date_end = datetime.datetime(2020, 3, 21, 0, 0)  #inclusive
    nx.set_node_attributes(subway_map, 0, 'flow')
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
            flow_date = datetime.datetime.strptime(flow_data[9], '%Y-%m-%d')  #date
            flow_in = int(flow_data[10])  # entries
            flow_out = int(flow_data[11])  # exits
            if date_end >= flow_date >= date_start:
                if (flow_complex_id, flow_division) in complex_to_station_dict:
                    station_id = complex_to_station_dict[(flow_complex_id, flow_division)]
                    if station_id in subway_map.nodes():  # we may have removed some stations (cough, staten island)
                        subway_map.nodes[station_id]['flow'] += flow_in + flow_out

    return subway_map, routes_and_stations

def generate_simple_triangle_map():
    """A fake subway. We'll need a naming convention for stations in the real one"""
    subway_map = nx.Graph()
    subway_map.add_nodes_from([1,2,3])

    subway_map.add_edge(1, 2)
    subway_map.add_edge(2, 3)
    subway_map.add_edge(3, 1)

    nx.set_node_attributes(subway_map, SubwayParams.NODE_TYPE_STATION, 'type')

    return subway_map

def get_subway_map(map_type):
    subway_map = nx.Graph()
    if map_type == 'TEST':
        return generate_simple_triangle_map()
    if map_type == 'NYC':
        return generate_NYC_subway_map()
    return subway_map


def make_exit_nodes(subway_map):
    """Given a subway map, add a street-level exit node.
    27.05.2020: With no attributes (actual location), this is pretty trivial for now"""
    subway_with_exits = nx.Graph.copy(subway_map)
    node_index = len(subway_map.nodes()) + 1000 #TODO:  This is a dubious way to index
    for node in subway_map.nodes():
        subway_with_exits.add_node(node_index)
        #TODO: is there a way to do this in one line?
        subway_with_exits.nodes[node_index]['type'] = SubwayParams.NODE_TYPE_STREET
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

