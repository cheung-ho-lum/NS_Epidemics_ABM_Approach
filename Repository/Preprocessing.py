import networkx as nx
from Parameters import SubwayParams
from pathlib import Path
# TODO: we need to refactor out the graph/map level things into a different file.


def generate_NYC_subway_map():
    """This is pretty straightforward as NYC keeps station data in a csv. In principle, we should probably
    make this a general import, but in reality, who is going to format their station data like NYC MTA?"""
    # TODO: NYC Subway stations have a bunch of features (ID, Complex ID, etc.) we need to make node features
    # TODO: add to docstring the tsv meanings
    """Station ID,Complex ID,GTFS Stop ID,Division,Line,Stop Name,Borough,Daytime Routes,Structure,GTFS Latitude,GTFS Longitude,North Direction Label,South Direction Label"""
    subway_map = nx.Graph()
    file_to_open = Path('Data/Stations.csv')
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

            #TODO: We're not counting Staten Island. I already duplicated Stations.csv in expectation of removing this trolly data
            if routes == 'SIR':
                continue

            #Adding Station
            subway_map.add_node(station_id)
            subway_map.nodes[station_id]['routes'] = routes
            subway_map.nodes[station_id]['x'] = station_long_x
            subway_map.nodes[station_id]['y'] = station_lat_y
            subway_map.nodes[station_id]['pos'] = (station_long_x, station_lat_y) #something weird, let's normalize

            #Adding any transfers
            if complex_id in complex_dict:
                for transfer_station_id in complex_dict[complex_id]:
                    subway_map.add_edge(transfer_station_id, station_id)
                complex_dict[complex_id].append(station_id)
            else:
                complex_dict[complex_id] = [station_id]
            #Adding edges between stations
            # TODO: this is crappy programming, but, besides geolocation, there's no good way to discover direct connections
            # Between two stations. My proposal is that we build these edges with the assumption that
            # the station connects to the station of the same line last on the list before it.
            # ex. station 6 = line A. station 2 = last station before it on line A
            # make edge 2<->6. undirected.
            # (it's not even clear we want direct connections to represent our edges)
            for route in routes.split():
                idx = int(station_id) - 1
                predecessor_found = False
                while idx > 0 and not predecessor_found:
                    if subway_map.has_node(idx):
                        if route in subway_map.nodes[idx]['routes']:
                            subway_map.add_edge(station_id, idx)
                            predecessor_found = True
                    idx -= 1

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

