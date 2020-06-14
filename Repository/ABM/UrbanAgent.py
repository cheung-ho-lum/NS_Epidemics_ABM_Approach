from ABM.SEIR_Agent import SEIR_Agent
from Parameters import AgentParams
from Parameters import EnvParams
PRINT_DEBUG = False


class SubwayAgent(SEIR_Agent):
    """This guy's constructor should probably have a few more params"""
    def __init__(self, unique_id, model, location=-1, population=0, epi_characteristics=None):
        super().__init__(unique_id, model, location, population, epi_characteristics)

    def infect(self):
        # Infected people now infect their current location with viral load +10 (total = 100)
        # Neighboring stations get +2
        # Stations on the same route get a viral load of +2 (regardless of distance)
        # Everyone else gets +1
        # viral load modified by distance from center (commute time).
        current_node = self.model.subway_graph.graph.nodes[self._location]
        commute_time = current_node['commute_time']
        num_infected = self._population[AgentParams.STATUS_INFECTED]
        if num_infected > 0:
            current_node['viral_load'] += 70 * num_infected * commute_time
            for nn in self.model.subway_graph.graph.neighbors(self._location):
                commute_time = self.model.subway_graph.graph.nodes[nn]['commute_time']
                self.model.subway_graph.graph.nodes[nn]['viral_load'] += 10 * num_infected * commute_time
            routes_affected = current_node['routes']
            for route in routes_affected:
                stations_affected = self.model.subway_graph.routing_dict[route]
                for station in stations_affected:
                    if station != self._location:
                        commute_time = self.model.subway_graph.graph.nodes[station]['commute_time']
                        self.model.subway_graph.graph.nodes[station]['viral_load'] += 10 * num_infected * commute_time
            for n in self.model.subway_graph.graph.nodes():
                #TODO: this spread should really be based on (inverse) distance to station
                self.model.subway_graph.graph.nodes[n]['viral_load'] += num_infected * 2
        return None

    def update_agent_health(self):
        viral_load = self.model.subway_graph.graph.nodes[self._location]['viral_load']
        # beta is increased by viral load
        # self._epi_characteristics['beta'] #TODO... think we need something later like a beta_initial
        # (TODO: in order to model countermeasures)
        if EnvParams.ISOLATION_COUNTERMEASURE in self.model.countermeasures and False:
            self._epi_characteristics['beta'] = AgentParams.DEFAULT_BETA / 3  # People are infected slower
            self._epi_characteristics['gamma'] = AgentParams.DEFAULT_GAMMA * 3  # People are found faster
        elif EnvParams.RECOMMENDATION_COUNTERMEASURE in self.model.countermeasures and False:
            self._epi_characteristics['beta'] = AgentParams.DEFAULT_BETA / 1.5  # People are infected slower
            self._epi_characteristics['gamma'] = AgentParams.DEFAULT_GAMMA * 1.5  # People are found faster
        else:
        #if EnvParams.ISOLATION_COUNTERMEASURE not in self.model.countermeasures:
            beta = AgentParams.DEFAULT_BETA + viral_load / 1e7 #100 sick people ~= viral load 5000
            self._epi_characteristics['beta'] = min(8, beta) #limit beta to 8

            # give a chance to convert purely based on viral load
            susceptible = self._population[AgentParams.STATUS_SUSCEPTIBLE]
            if viral_load >= 1e5:
                outside_infection_chance_roll = (viral_load - 1e5) / 1e9  # TODO: also made up stuff
                self._population[AgentParams.STATUS_SUSCEPTIBLE] -= susceptible * outside_infection_chance_roll
                self._population[AgentParams.STATUS_EXPOSED] += susceptible * outside_infection_chance_roll


        super().update_agent_health()


    def step(self):
        self.move()
        self.update_agent_health()