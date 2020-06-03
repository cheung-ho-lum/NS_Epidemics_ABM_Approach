import datetime
import networkx as nx
from Parameters import SubwayParams, SimulationParams
from pathlib import Path
import math
from transliterate import translit
import codecs

def generate_geometric_map(type="sierpinski"):
    file_to_open = Path('Data/ss_' + type + '.csv')
    #TODO: catch in case of stupidity?
    #Our simplified subway has no complexes. Routes and stations only.
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

    nx.set_node_attributes(subway_map, SubwayParams.NODE_TYPE_STATION, 'type')
    nx.set_node_attributes(subway_map, 0, 'viral_load')
    nx.set_node_attributes(subway_map, 0, 'flow')
    return subway_map, routes_and_stations, 0

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
    file_to_open = Path('Data/list_of_moscow_metro_stations.csv')
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


            if(subway_map.has_node(station_id)):
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

    nx.set_node_attributes(subway_map, SubwayParams.NODE_TYPE_STATION, 'type')
    nx.set_node_attributes(subway_map, 0, 'viral_load')
    nx.set_node_attributes(subway_map, 0, 'flow')

    return subway_map, routes_and_stations, 0


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

            #TODO: turns out complexID + divid is not a unique identifier! see 467, 468
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
    nx.set_node_attributes(subway_map, 0, 'flow')

    # TODO: Of course these should be model params, but we haven't the least  idea how to use them yet.
    date_start = datetime.datetime(2020, 3, 1, 0, 0)  # inclusive
    date_end = datetime.datetime(2020, 3, 21, 0, 0)  # inclusive

    #I suppose the nice thing about python is I don't have too much to update if I need to return something new.
    total_flow = update_flow_data(subway_map, 'Turnstile_Data.csv', complex_to_station_dict, date_start, date_end)

    return subway_map, routes_and_stations, total_flow

#for NYC, total passenger flow was about 124975642
def update_flow_data(subway_map, flow_files, complex_to_station_dict, date_start, date_end):
    """this will look substantially different from our geographically/train based map.
    we will look at the turnstile data from Mar 1 - Mar 21 when the pandemic was starting
    so... maybe this function should eventually take unix time etc., but we'll hardcode it for now"""
    # Protip: you can get station id from complex id + division and referencing stations.csv
    """stop_name,daytime_routes,division,line,borough,structure,gtfs_longitude,gtfs_latitude,complex_id,date,entries,exits"""
    """Astoria - Ditmars Blvd,N W,BMT,Astoria,Q,Elevated,-73.912034,40.775036,1,2020-01-01,7024,7060"""
    # So we filter down by date, sum up the entrance and exits, and call it 'passenger flow' node attribute.
    # Remember that complex id and div id are strings!
    file_to_open = Path('Data/' + flow_files)
    total_flow = 0

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
                        subway_map.nodes[station_id]['flow'] += flow_in + flow_out
                        total_flow += flow_in + flow_out

    #TODO: HACK ALERT! DUE TO ISSUES WITH COMPLEX/STATION DATA. REFERENCE COMPLEX_TO_STATION_DICT TODO:
    for station_id in subway_map.nodes():
        if subway_map.nodes[station_id]['flow'] == 0:
            subway_map.nodes[station_id]['flow'] = 600000
            total_flow += 600000
    return total_flow

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

    nx.set_node_attributes(subway_map, SubwayParams.NODE_TYPE_STATION, 'type')
    nx.set_node_attributes(subway_map, 0, 'viral_load')
    nx.set_node_attributes(subway_map, 0, 'flow')

    return subway_map, routes_and_stations, 0


def get_subway_map(map_type):
    """main wrapper to return different maps. the below should really be an enum."""
    # TODO: This is the crappiest way of updating abstraction I ever did see.
    # TODO: It's high time *everyone* returned an OurGraph
    subway_map = nx.Graph()
    if map_type == SimulationParams.MAP_TYPE_TEST:
        return generate_simple_triangle_map()
    if map_type == SimulationParams.MAP_TYPE_NYC:
        return generate_NYC_subway_map()
    if map_type == SimulationParams.MAP_TYPE_GEOMETRIC_SIERPINSKI:
        return generate_geometric_map('sierpinski')
    if map_type == SimulationParams.MAP_TYPE_GEOMETRIC_CIRCULAR:
        return generate_geometric_map('moscow')
    if map_type == SimulationParams.MAP_TYPE_GEOMETRIC_GRID:
        return generate_geometric_map('grid')
    if map_type == SimulationParams.MAP_TYPE_MOSCOW:
        return generate_moskva_subway_map()
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

