from mesa import Model
from ABM.AirAgent import AirAgent
from mesa.time import RandomActivation
import random
from Parameters import AgentParams
import networkx as nx

class Air_Model(Model):
    """This guy's constructor should probably have a few more params."""
    def __init__(self, n, air_graph, passenger_flow=0):
        self.num_agents = n
        self._air_graph = air_graph
        self._agent_loc_dictionary = {}  # a dictionary of locations with lists of agents at each location
        self.schedule = RandomActivation(self)
        # Create agents
        agent_id = 0
        for loc in list(self.airway_graph.graph.nodes()):
            agent_id += 1  # we will keep agent ids different from location for now.
            loc_passenger_flow = self.airway_graph.graph.nodes[loc]['flow']
            if loc_passenger_flow == 0:
                print('making up passenger flow (10000) for location', loc)
                loc_passenger_flow = 10000
            a = AirAgent(agent_id, self, loc, loc_passenger_flow)
            if loc == AgentParams.MAP_LOCATION_WUHAN_TIANHE:
                a.population[AgentParams.STATUS_INFECTED] += 1
            self.schedule.add(a)

    #Decay the viral loads in the environment. just wipes them for now.
    def decay_viral_loads(self):
        nx.set_node_attributes(self.airway_graph.graph, 0, 'viral_load')
        return None

    def increment_viral_loads(self):
        for a in self.schedule.agents:
            a.infect()
        for loc in list(self.airway_graph.graph.nodes()):
            viral_load = self.airway_graph.graph.nodes[loc]['viral_load']
            self.airway_graph.graph.nodes[loc]['viral_load'] = min(viral_load, 1e6) #Let's top it out at 1e6
        return None

    def step(self):
        self.decay_viral_loads()
        self.increment_viral_loads()
        self.schedule.step()
        self.airway_graph.update_hotspots(self.schedule.agents)

    #TODO: I guess there is a need for generic transportation model. Or maybe calculate_SEIR shouldn't even be here.
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

    #TODO: this can be removed. or moved to TransportationModel.
    #Called by the agent class to update itself in the agent dictionary
    def update_agent_location(self, agent, old_location, new_location):
        self._agent_loc_dictionary[old_location].remove(agent)
        self._agent_loc_dictionary[new_location].append(agent)

    @property
    def airway_graph(self):
        return self._air_graph

    @airway_graph.setter
    def airway_graph(self, value):
        self._air_graph = value


    @property
    def agent_loc_dictionary(self):
        return self._agent_loc_dictionary

    @agent_loc_dictionary.setter
    def agent_loc_dictionary(self, value):
        self._agent_loc_dictionary = value