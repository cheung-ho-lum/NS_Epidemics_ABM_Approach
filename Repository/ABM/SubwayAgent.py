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
            current_node['viral_load'] += 10 * num_infected * commute_time
            for nn in self.model.subway_graph.graph.neighbors(self._location):
                commute_time = self.model.subway_graph.graph.nodes[nn]['commute_time']
                self.model.subway_graph.graph.nodes[nn]['viral_load'] += 10 * num_infected * commute_time
            routes_affected = current_node['routes']
            for route in routes_affected:
                stations_affected = self.model.subway_graph.routing_dict[route]
                for station in stations_affected:
                    if station != self._location:
                        commute_time = self.model.subway_graph.graph.nodes[station]['commute_time']
                        self.model.subway_graph.graph.nodes[station]['viral_load'] += 90 * num_infected * commute_time
            for n in self.model.subway_graph.graph.nodes():
                #TODO: this spread should really be based on (inverse) distance to station
                self.model.subway_graph.graph.nodes[n]['viral_load'] += num_infected * 1
        return None

    def update_agent_health(self):
        viral_load = self.model.subway_graph.graph.nodes[self._location]['viral_load']
        # beta is increased by viral load
        # self._epi_characteristics['beta'] #TODO... think we need something later like a beta_initial
        # (TODO: in order to model countermeasures)
        infected = self._population[AgentParams.STATUS_INFECTED]
        #infected used temporarily to model non-compliance or self initiative
        if EnvParams.ISOLATION_COUNTERMEASURE in self.model.countermeasures and infected > 10 or infected > 20:
            self._epi_characteristics['beta'] = AgentParams.DEFAULT_BETA / 4  # People are infected slower
            self._epi_characteristics['gamma'] = AgentParams.DEFAULT_GAMMA * 2  # People are found faster
        elif EnvParams.RECOMMENDATION_COUNTERMEASURE in self.model.countermeasures and infected > 1 or infected > 2:
            self._epi_characteristics['beta'] = AgentParams.DEFAULT_BETA / 1.4  # People are infected slower
            self._epi_characteristics['gamma'] = AgentParams.DEFAULT_GAMMA * 1.4  # People are found faster
        else:
        #if EnvParams.ISOLATION_COUNTERMEASURE not in self.model.countermeasures:
            beta = AgentParams.DEFAULT_BETA + viral_load / 1e4  #
            self._epi_characteristics['beta'] = min(10, beta)  # limit beta to 10. This one should be from princess cruise number.

        # TODO: instead of commenting this section in and out, build it into an urban agent
        # complete exposure to outside world!
        FULL_SPREAD_FACTOR = 0.7

        susceptible = self._population[AgentParams.STATUS_SUSCEPTIBLE]
        SEIR_numbers = self.model.calculate_SEIR()
        outside_infected = SEIR_numbers[2] - self.population[AgentParams.STATUS_INFECTED]
        normalization_factor = sum(SEIR_numbers)

        self._population[AgentParams.STATUS_SUSCEPTIBLE] -= FULL_SPREAD_FACTOR * \
            self._epi_characteristics['beta'] * susceptible * outside_infected / normalization_factor
        self._population[AgentParams.STATUS_EXPOSED] += FULL_SPREAD_FACTOR * \
            self._epi_characteristics['beta'] * susceptible * outside_infected / normalization_factor

        super().update_agent_health()

    def step(self):
        self.move()
        self.update_agent_health()
