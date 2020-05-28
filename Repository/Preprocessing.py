import networkx as nx
from Parameters import SubwayParams
# TODO: we need to refactor out the graph/map level things into a different file.


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
    return subway_map


def make_exit_nodes(subway_map):
    """Given a subway map, add a street-level exit node.
    27.05.2020: With no attributes (actual location), this is pretty trivial for now"""
    subway_with_exits = nx.Graph.copy(subway_map)
    node_index = len(subway_map.nodes()) + 1
    for node in subway_map.nodes():
        subway_with_exits.add_node(node_index)
        subway_with_exits.nodes[node_index]['type'] = SubwayParams.NODE_TYPE_STREET
        subway_with_exits.add_edge(node_index, node)
        node_index += 1

    return subway_with_exits

