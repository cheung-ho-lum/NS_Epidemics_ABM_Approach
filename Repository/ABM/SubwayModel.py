from mesa import Model
from ABM import SubwayAgent
from mesa.time import RandomActivation
from ABM import SubwayGraph
import random
from Parameters import AgentParams
import networkx as nx

DEBUG_START_LOCATIONS = [4, 5, 6] #these are the street locations for the debug scenario

class SEIR_Subway_Model(Model):
    """This guy's constructor should probably have a few more params."""
    def __init__(self, n, subway_map, routing_dict, passenger_flow=0):
        self.num_agents = n
        self._our_graph = SubwayGraph.OurGraph(subway_map, routing_dict, passenger_flow)
        self._agent_loc_dictionary = {}  # a dictionary of locations with lists of agents at each location
        self.schedule = RandomActivation(self)
        # Create agents
        # Should create agents, and (for now) place them in random street locations
        #TODO: It would be cool if we were able to roll agents independently.
        #For now, let's just place an appropriate number of agents at each location
        if self.our_graph.passenger_flow > 0:
            agents_placed = 0
            for loc in list(self.our_graph.graph.nodes()):
                loc_agents_placed = 0
                loc_passenger_flow = self.our_graph.graph.nodes[loc]['flow']
                loc_flow_percentage = loc_passenger_flow / self.our_graph.passenger_flow
                num_agents_to_place = round(loc_flow_percentage * self.num_agents)
                while loc_agents_placed < num_agents_to_place and agents_placed < self.num_agents:
                    a = SubwayAgent.SEIRAgent(agents_placed, self, location=loc)
                    if a.location in self._agent_loc_dictionary:
                        self._agent_loc_dictionary[a.location].append(a)
                    else:
                        self._agent_loc_dictionary[a.location] = [a]
                    self.schedule.add(a)
                    loc_agents_placed += 1
                    agents_placed += 1
                # debug print(loc, loc_agents_placed)
        else:
            for i in range(self.num_agents):
                start_location = random.choice(list(self._our_graph.graph.nodes()))
                a = SubwayAgent.SEIRAgent(i, self, location=start_location)
                if a.location in self._agent_loc_dictionary:
                    self._agent_loc_dictionary[a.location].append(a)
                else:
                    self._agent_loc_dictionary[a.location] = [a]
                self.schedule.add(a)

    #Decay the viral loads in the environment. just wipes them for now.
    def decay_viral_loads(self):
        nx.set_node_attributes(self.our_graph.graph, 0, 'viral_load')
        return None

    def step(self):
        self.decay_viral_loads()
        self.schedule.step()

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
    def our_graph(self):
        return self._our_graph

    @our_graph.setter
    def our_graph(self, value):
        self._our_graph = value


    @property
    def agent_loc_dictionary(self):
        return self._agent_loc_dictionary

    @agent_loc_dictionary.setter
    def agent_loc_dictionary(self, value):
        self._agent_loc_dictionary = value