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
        #FTry to place an appropriate number of agents at each location
        if self.airway_graph.passenger_flow > 0:
            agents_placed = 0
            for loc in list(self.airway_graph.graph.nodes()):
                loc_agents_placed = 0
                loc_passenger_flow = self.airway_graph.graph.nodes[loc]['flow']
                loc_flow_percentage = loc_passenger_flow / self.airway_graph.passenger_flow
                num_agents_to_place = round(loc_flow_percentage * self.num_agents)
                while loc_agents_placed < num_agents_to_place and agents_placed < self.num_agents:
                    a = AirAgent(agents_placed, self, location=loc)
                    if a.location in self._agent_loc_dictionary:
                        self._agent_loc_dictionary[a.location].append(a)
                    else:
                        self._agent_loc_dictionary[a.location] = [a]
                    self.schedule.add(a)
                    loc_agents_placed += 1
                    agents_placed += 1
        else:
            node_list = list(self._air_graph.graph.nodes())
            for i in range(self.num_agents):
                start_location = random.choice(node_list)
                a = AirAgent(i, self, location=start_location)
                if a.location in self._agent_loc_dictionary:
                    self._agent_loc_dictionary[a.location].append(a)
                else:
                    self._agent_loc_dictionary[a.location] = [a]
                self.schedule.add(a)

    #Decay the viral loads in the environment. just wipes them for now.
    def decay_viral_loads(self):
        nx.set_node_attributes(self.airway_graph.graph, 0, 'viral_load')
        return None

    def step(self):
        self.decay_viral_loads()
        self.schedule.step()
        self.airway_graph.update_hotspots(self.schedule.agents)

    def calculate_SEIR(self, print_results = False):
        sick, exposed, infected, recovered = 0, 0, 0, 0
        for a in self.schedule.agents:
            if a.infection_status == AgentParams.STATUS_SUSCEPTIBLE:
                sick += 1
            if a.infection_status == AgentParams.STATUS_EXPOSED:
                exposed += 1
            if a.infection_status == AgentParams.STATUS_INFECTED:
                infected += 1
            if a.infection_status == AgentParams.STATUS_RECOVERED:
                recovered += 1
        print('S,E,I,R:', sick, exposed, infected, recovered)
        return [sick, exposed, infected, recovered]

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