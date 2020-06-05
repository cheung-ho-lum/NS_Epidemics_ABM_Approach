import math
import networkx as nx
from networkx import Graph
import matplotlib.pyplot as plt
from itertools import count
from Parameters import AgentParams, SimulationParams


class TransportationGraph(Graph):
    """Basically nx graph wrapper with some subway-specific characteristics"""
    def __init__(self, orig=None):
        if orig is None:
            super().__init__(Graph)
            self._graph = None
        else:
            self._graph = nx.Graph.copy(orig)

    def update_hotspots(self, agents):
        nx.set_node_attributes(self._graph, 0, 'hotspot')
        for agent in agents: #TODO: flooring this so it actually drops to 0.
            self._graph.nodes[agent.location]['hotspot'] = math.floor(agent.population[AgentParams.STATUS_INFECTED])

    @property
    def graph(self):
        return self._graph

    @graph.setter
    def graph(self, value):
        self._graph = value

    @property
    def passenger_flow(self):
        return self._passenger_flow

    @passenger_flow.setter
    def passenger_flow(self, value):
        self._passenger_flow = value
