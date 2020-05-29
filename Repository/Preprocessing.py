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
    """Station ID,Complex ID,GTFS Stop ID,Division,Line,Stop Name,Borough,Daytime Routes,Structure,GTFS Latitude,GTFS Longitude,North Direction Label,South Direction Label"""
    subway_map = nx.Graph()
    file_to_open = Path('Data/Stations.csv')
    routes_and_stations = {}
    with open(file_to_open, 'r') as f:
        next(f) #skip header row
        complex_dict = {} #dictionary of complexes. values = stations at that complex
        for row in f:
            station_data = row.split(',')
            station_id = int(station_data[0])  # TODO: We're making this an int as early as possible!
            complex_id = station_data[1]  # Complex ID. If stations are part of the same complex, they need to be connected
            _ = station_data[2]  # GTFS Stop ID
            _ = station_data[3]  # Division
            _ = station_data[4]  # Line Caution!! Lines != Routes, not what you think it is!
            _ = station_data[5]  # Stop Name
            _ = station_data[6]  # Borough
            routes = station_data[7] # daytime(?) Routes
            _ = station_data[8]  #
            station_lat_y = float(station_data[9])  # Latitude
            station_long_x = float(station_data[10])  # Longtitude

            # We're not counting Staten Island. I already duplicated Stations.csv in expectation of removing this trolly data
            if routes == 'SIR':
                continue

            #Adding Station
            subway_map.add_node(station_id)
            subway_map.nodes[station_id]['routes'] = routes
            subway_map.nodes[station_id]['x'] = station_long_x
            subway_map.nodes[station_id]['y'] = station_lat_y
            subway_map.nodes[station_id]['pos'] = (station_long_x, station_lat_y)

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

    "Adding Edges, a more logical approach (but still possibly crap, also might not matter)"
    "Best theoretical mathy approach would be to find the shortest hamiltonian path. but i am lazy"
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
        x_coord_last = subway_map.nodes[last_station]['x']
        y_coord_last = subway_map.nodes[last_station]['y']
        uncombined_stations.remove(terminal_station)
        x_coord_next = -80
        y_coord_next = 50

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

    nx.set_node_attributes(subway_map, SubwayParams.NODE_TYPE_STATION, 'type')
    return subway_map

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

        subway_with_exits.add_edge(node_index, node)
        print(node_index,node, 'added')
        node_index += 1

    return subway_with_exits

