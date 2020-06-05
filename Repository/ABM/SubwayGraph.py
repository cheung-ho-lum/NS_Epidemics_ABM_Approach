import math
import networkx as nx
from networkx import Graph
import matplotlib.pyplot as plt
from itertools import count
from Parameters import AgentParams, SimulationParams
from ABM.TransportationGraph import TransportationGraph


class SubwayGraph(TransportationGraph):
    """Basically nx graph wrapper with some subway-specific characteristics"""
    def __init__(self, orig=None, route_dict=None):
        super().__init__(orig)

        if route_dict is not None:
            self._routing_dict = route_dict
        else:
            print('Warning, missing route dict currently not supported!')


    #TODO: belongs in model. maybe under graphics.
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
            #print("max ",node_attr,":", max(colors))  # print this to find appropriate vmin and vmax
            pos = nx.get_node_attributes(self._graph, 'pos')
            if len(pos) == 0:
                pos = nx.spring_layout(self._graph, seed=SimulationParams.GRAPH_SEED)
            nx.draw_networkx(self._graph, node_size=node_sizes, with_labels=False, width=0.5, node_color=colors, pos=pos,
                             cmap=plt.cm.jet, vmin=50, vmax=400) #TODO: some vmin max hack to get the drawing right
            if len(timestamp) > 0:
                plt.title(node_attr + ' t=' + timestamp)

    @property
    def routing_dict(self):
        return self._routing_dict

    @routing_dict.setter
    def routing_dict(self, value):
        self._routing_dict = value

