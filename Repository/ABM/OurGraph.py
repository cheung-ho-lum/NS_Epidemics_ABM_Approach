import math

import networkx as nx
from networkx import Graph
#Basically networkx graph wrapper with some helpers
import matplotlib.pyplot as plt
from itertools import count
from ABM import Agent
from Parameters import AgentParams


class OurGraph(Graph):
    def __init__(self, orig=None):
        if orig is None:
            super().__init__(Graph)
            self._graph = None
        else:
            self._graph = nx.Graph.copy(orig)

    def update_hotspots(self, agents):
        nx.set_node_attributes(self._graph, 0, 'hotspot')
        for agent in agents:
            if agent.infection_status == AgentParams.STATUS_INFECTED:
                self._graph.nodes[agent.location]['hotspot'] += 1

    #Maybe this actually belongs in a graphics class
    def draw_graph(self, node_attr="type"):
        if len(node_attr) > 0:
            groups = set(nx.get_node_attributes(self._graph, node_attr).values())
            mapping = dict(zip(sorted(groups), count()))
            nodes = self._graph.nodes()
            node_sizes = []
            for n in nodes:
                size_of_n = math.sqrt(self._graph.nodes[n]['flow'] / 500)
                node_sizes.append(max(25, size_of_n))  # or the default value of 50
            colors = [mapping[self._graph.nodes[n][node_attr]] for n in nodes]
            pos = nx.get_node_attributes(self._graph, 'pos')
            nx.draw_networkx(self._graph, node_size= node_sizes, with_labels=False, width=0.5, node_color=colors, pos=pos,
                             cmap=plt.cm.jet)

    @property
    def graph(self):
        return self._graph

    @graph.setter
    def graph(self, value):
        self._graph = value