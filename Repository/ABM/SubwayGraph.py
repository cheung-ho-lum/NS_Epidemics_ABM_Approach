import networkx as nx

from ABM.TransportationGraph import TransportationGraph


class SubwayGraph(TransportationGraph):
    """Basically nx graph wrapper with some subway-specific characteristics"""
    def __init__(self, orig=None, route_dict=None):
        super().__init__(orig)

        if route_dict is not None:
            self._routing_dict = route_dict
        else:
            print('Warning, missing route dict currently not supported!')

        self._path_dict = {}


        self._infected_by_route_dict = {}
        self._commuters_by_route_dict = {}
        for route in route_dict:
            self._infected_by_route_dict[route] = 0
            self._commuters_by_route_dict[route] = 0

        #TODO: deprecate this
        nx_graph = self.graph
        for node_1 in nx_graph.nodes():
            for node_2 in nx_graph.nodes():
                #distance_between_nodes = nx.algorithms.shortest_path_length(nx_graph, node_1, node_2)
                distance_between_nodes = 1
                self._path_dict[(node_1, node_2)] = distance_between_nodes



    def calculate_commute_similarity(self, node_1, node_2):
        # Similarity score factors:
        # Number of common routes / total number of routes (0 if no common routes)
        # If the distance from the station is less than 5 than:
        #   Commute time (minimum of two)
        # If more than 5, give them some minimum commute time together

        route_similarity, shared_commute = 0, 0
        nx_graph = self.graph
        node1_commute = nx_graph.nodes[node_1]['commute_time']
        node2_commute = nx_graph.nodes[node_2]['commute_time']

        #TODO: minor regret not making them sets in the first place.
        routes_1 = set(nx_graph.nodes[node_1]['routes'])
        routes_2 = set(nx_graph.nodes[node_2]['routes'])
        route_similarity = len(routes_1.intersection(routes_2)) / len(routes_1.union(routes_2))

        if route_similarity > 0:
            distance_between_nodes = self._path_dict[(node_1, node_2)]
            if distance_between_nodes < 5: #TODO: this is a hack to make stations at opposite ends of line not interact
                shared_commute = min(node1_commute, node2_commute)
            else:
                shared_commute = 0

        return route_similarity * shared_commute

    @property
    def routing_dict(self):
        return self._routing_dict

    @routing_dict.setter
    def routing_dict(self, value):
        self._routing_dict = value

    @property
    def path_dict(self):
        return self._path_dict

    @path_dict.setter
    def path_dict(self, value):
        self._path_dict = value

    @property
    def commuters_by_route_dict(self):
        return self._commuters_by_route_dict

    @commuters_by_route_dict.setter
    def commuters_by_route_dict(self, value):
        self._commuters_by_route_dict = value

    @property
    def infected_by_route_dict(self):
        return self._infected_by_route_dict

    @infected_by_route_dict.setter
    def infected_by_route_dict(self, value):
        self._infected_by_route_dict = value
