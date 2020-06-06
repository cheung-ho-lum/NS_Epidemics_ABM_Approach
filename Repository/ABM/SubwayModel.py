from ABM.SubwayAgent import SubwayAgent
from mesa.time import RandomActivation
from ABM.SubwayGraph import SubwayGraph
from Parameters import AgentParams
import networkx as nx
from ABM.TransportationModel import TransportationModel


class SubwayModel(TransportationModel):
    """This guy's constructor should probably have a few more params."""
    def __init__(self, subway_map, routing_dict):
        self._subway_graph = SubwayGraph(subway_map, routing_dict)
        self._agent_loc_dictionary = {}  # a dictionary of locations with lists of agents at each location
        self.schedule = RandomActivation(self)
        # Create agents
        agent_id = 0
        for loc in list(self.subway_graph.graph.nodes()):
            agent_id += 1  # we will keep agent ids different from location for now.
            loc_passenger_flow = self.subway_graph.graph.nodes[loc]['flow']
            if loc_passenger_flow == 0:
                print('making up passenger flow (10000) for location', loc)
                loc_passenger_flow = 10000
            a = SubwayAgent(agent_id, self, loc, loc_passenger_flow)
            if loc == AgentParams.MAP_LOCATION_JUNCTION_BLVD: #TODO: this method of seeding is actually quite bad.
                a.population[AgentParams.STATUS_INFECTED] += 1
                a.population[AgentParams.STATUS_SUSCEPTIBLE] -= 1
            self.schedule.add(a)

    # Decay the viral loads in the environment. just wipes them for now.
    def decay_viral_loads(self):
        nx.set_node_attributes(self.subway_graph.graph, 0, 'viral_load')
        return None

    def increment_viral_loads(self):
        for a in self.schedule.agents:
            a.infect()
        for loc in list(self.subway_graph.graph.nodes()):
            viral_load = self.subway_graph.graph.nodes[loc]['viral_load']
            self.subway_graph.graph.nodes[loc]['viral_load'] = min(viral_load, 1e6) #Let's top it out at 1e6
        return None

    def step(self):
        self.decay_viral_loads() #TODO: yes, this belongs at the end of a step. but i need my snapshot to be mid-day
        self.increment_viral_loads()
        self.schedule.step()
        self.subway_graph.update_hotspots(self.schedule.agents) #TODO: repair this later

    def calculate_SEIR(self, print_results=False):
        sick, exposed, infected, recovered = 0, 0, 0, 0
        for a in self.schedule.agents:
            sick += a.population[AgentParams.STATUS_SUSCEPTIBLE]
            exposed += a.population[AgentParams.STATUS_EXPOSED]
            infected += a.population[AgentParams.STATUS_INFECTED]
            recovered += a.population[AgentParams.STATUS_RECOVERED]
        if print_results:
            print('S,E,I,R:', sick, exposed, infected, recovered)
        return [sick, exposed, infected, recovered]

    @property
    def subway_graph(self):
        return self._subway_graph

    @subway_graph.setter
    def subway_graph(self, value):
        self._subway_graph = value