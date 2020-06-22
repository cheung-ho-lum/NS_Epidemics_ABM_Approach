import random
from mesa import Model
from ABM.SEIR_Agent import SEIR_Agent
from mesa.time import RandomActivation
from Parameters import AgentParams, SimulationParams
import networkx as nx


class TransportationModel(Model):
    """The base model"""
    def __init__(self, transportation_graph):
        self.schedule = RandomActivation(self)
        self._transportation_graph = transportation_graph
        self._countermeasures = []  # a list of active countermeasures. tp model will not update this.
        # Create agents
        agent_id = 0
        # TODO: Seeding..., if not known, is random for now
        seed_location = random.choice(list(self._transportation_graph.graph.nodes()))
        self._transportation_graph = transportation_graph
        for loc in list(self._transportation_graph.graph.nodes()):
            agent_id += 1  # we will keep agent ids different from location for now.
            loc_passenger_flow = self._transportation_graph.graph.nodes[loc]['flow']
            if loc_passenger_flow == 0:
                print('making up passenger flow (10000) for location', loc)
                loc_passenger_flow = 10000
            a = SEIR_Agent(agent_id, self, loc, loc_passenger_flow)
            if loc == seed_location:
                a.population[AgentParams.STATUS_INFECTED] += 1
                a.population[AgentParams.STATUS_SUSCEPTIBLE] -= 1
            self.schedule.add(a)

    def update_countermeasures(self):
        return None

    # Decay the viral loads in the environment. just wipes them for now.
    def decay_viral_loads(self):
        nx.set_node_attributes(self._transportation_graph.graph, 0, 'viral_load')
        for a in self.schedule.agents:
            self._transportation_graph.graph.nodes[a.location]['infected'] = a.population[AgentParams.STATUS_INFECTED]
        return None

    def increment_viral_loads(self):
        for a in self.schedule.agents:
            a.infect()
        return None

    def step(self):
        self.decay_viral_loads() #TODO: yes, this belongs at the end of a step. but i need my snapshot to be mid-day
        self.increment_viral_loads()
        self.schedule.step()
        self._transportation_graph.update_hotspots(self.schedule.agents) #TODO: repair this later
        self.update_countermeasures()

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
    def transportation_graph(self):
        return self._transportation_graph

    @transportation_graph.setter
    def transportation_graph(self, value):
        self._transportation_graph = value

    @property
    def countermeasures(self):
        return self._countermeasures

    @countermeasures.setter
    def countermeasures(self, value):
        self._countermeasures = value
