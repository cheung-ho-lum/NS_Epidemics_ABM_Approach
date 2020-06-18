from ABM.SubwayAgent import SubwayAgent
from mesa.time import RandomActivation
from ABM.SubwayGraph import SubwayGraph
from Parameters import AgentParams, EnvParams
import networkx as nx
from ABM.TransportationModel import TransportationModel


class SubwayModel(TransportationModel):
    """This guy's constructor should probably have a few more params."""
    def __init__(self, subway_map, routing_dict):
        self._subway_graph = SubwayGraph(subway_map, routing_dict)
        self._agent_loc_dictionary = {}  # a dictionary of locations with lists of agents at each location
        self.countermeasures = {}
        self.schedule = RandomActivation(self)
        # Create agents
        agent_id = 0
        for loc in list(self.subway_graph.graph.nodes()):
            agent_id += 1  # we will keep agent ids different from location for now.
            population = subway_map.nodes[loc]['population']
            a = SubwayAgent(agent_id, self, loc, population)
            if loc == AgentParams.MAP_LOCATION_JUNCTION_BLVD or \
                loc == AgentParams.MAP_LOCATION_55_ST or \
                loc == AgentParams.MAP_LOCATION_98_BEACH: #TODO: this method of seeding is actually quite bad.
                a.population[AgentParams.STATUS_EXPOSED] += 18
                a.population[AgentParams.STATUS_INFECTED] += 2
                a.population[AgentParams.STATUS_RECOVERED] += 0
                a.population[AgentParams.STATUS_SUSCEPTIBLE] -= 20

            self.schedule.add(a)

    # Decay the viral loads in the environment. just wipes them for now.
    def decay_viral_loads(self):
        nx.set_node_attributes(self.subway_graph.graph, 0, 'viral_load')
        return None

    def increment_viral_loads(self):
        for a in self.schedule.agents:
            a.infect()
        return None

    def step(self):
        self.decay_viral_loads() #TODO: yes, this belongs at the end of a step. but i need my snapshot to be mid-day
        self.increment_viral_loads()
        self.schedule.step()
        self.subway_graph.update_hotspots(self.schedule.agents) #TODO: repair this later
        self.update_countermeasures()

    def update_countermeasures(self):
        active = self.countermeasures
        infected = 0
        for a in self.schedule.agents:
            infected += a.population[AgentParams.STATUS_INFECTED]
        if EnvParams.ISOLATION_COUNTERMEASURE not in active.keys():
            if infected >= 5000:  # we have 20x the size of NYC atm
                active[EnvParams.ISOLATION_COUNTERMEASURE] = self.schedule.time
                print('isolation countermeasure taken!')
        if EnvParams.RECOMMENDATION_COUNTERMEASURE not in active.keys():
            if infected >= 500:  # we have 20x the size of NYC atm
                active[EnvParams.RECOMMENDATION_COUNTERMEASURE] = self.schedule.time
                print('recommendation countermeasure taken!')
        if EnvParams.AWARENESS_COUNTERMEASURE not in active.keys():
            if infected >= 500:  # start awareness campaign
                active[EnvParams.AWARENESS_COUNTERMEASURE] = self.schedule.time
                print('awareness countermeasure taken!')

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

