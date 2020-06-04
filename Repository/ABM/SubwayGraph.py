import math
import networkx as nx
from networkx import Graph
import matplotlib.pyplot as plt
from itertools import count
from Parameters import AgentParams, SimulationParams


class SubwayGraph(Graph):
    """Basically nx graph wrapper with some subway-specific characteristics"""
    def __init__(self, orig=None, route_dict=None, passenger_flow=0):
        if orig is None:
            super().__init__(Graph)
            self._graph = None
        else:
            self._graph = nx.Graph.copy(orig)
        if route_dict is not None:
            self._routing_dict = route_dict
        else:
            print('Warning, missing route dict currently not supported!')

        if passenger_flow == 0:
            print('Warning, missing passenger flow data. Also not really supported!')
        self._passenger_flow = passenger_flow

    def update_hotspots(self, agents):
        nx.set_node_attributes(self._graph, 0, 'hotspot')
        for agent in agents:
            if agent.infection_status == AgentParams.STATUS_INFECTED:
                self._graph.nodes[agent.location]['hotspot'] += 1

    #Maybe this actually belongs in a graphics class
    #TODO: timestamp the graph, add node label options, do colors right.
    def draw_graph(self, node_attr="type", timestamp=""):
        if len(node_attr) > 0:
            groups = set(nx.get_node_attributes(self._graph, node_attr).values())
            mapping = dict(zip(sorted(groups), count()))
            nodes = self._graph.nodes()
            node_sizes = []
            for n in nodes:
                size_of_n = math.sqrt(self._graph.nodes[n]['flow'] / 500)
                node_sizes.append(max(25, size_of_n))  # or the default value of 25
            colors = [mapping[self._graph.nodes[n][node_attr]] for n in nodes]
            pos = nx.get_node_attributes(self._graph, 'pos')
            if len(pos) == 0:
                pos = nx.spring_layout(self._graph, seed=SimulationParams.GRAPH_SEED)
            nx.draw_networkx(self._graph, node_size=node_sizes, with_labels=False, width=0.5, node_color=colors, pos=pos,
                             cmap=plt.cm.jet)
            if len(timestamp) > 0:
                plt.title(node_attr + ' t=' + timestamp)

    @property
    def graph(self):
        return self._graph

    @graph.setter
    def graph(self, value):
        self._graph = value

    @property
    def routing_dict(self):
        return self._routing_dict

    @routing_dict.setter
    def routing_dict(self, value):
        self._routing_dict = value

    @property
    def passenger_flow(self):
        return self._passenger_flow

    @passenger_flow.setter
    def passenger_flow(self, value):
        self._passenger_flow = value
