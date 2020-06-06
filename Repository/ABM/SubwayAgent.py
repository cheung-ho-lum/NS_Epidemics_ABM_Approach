from ABM.SEIR_Agent import SEIR_Agent
from Parameters import AgentParams
from Parameters import EnvParams
PRINT_DEBUG = False


class SubwayAgent(SEIR_Agent):
    """This guy's constructor should probably have a few more params"""
    def __init__(self, unique_id, model, location=-1, population=0, epi_characteristics=None):
        super().__init__(unique_id, model, location, population, epi_characteristics)

    def infect(self):
        # Infected people now infect their current location with viral load +100 (total = 100)
        # Neighboring stations get +20
        # Stations on the same route get a viral load of +20 (regardless of distance)
        current_node = self.model.subway_graph.graph.nodes[self._location]
        num_infected = self._population[AgentParams.STATUS_INFECTED]
        if num_infected > 0:
            current_node['viral_load'] += 8 * num_infected
            for nn in self.model.subway_graph.graph.neighbors(self._location):
                self.model.subway_graph.graph.nodes[nn]['viral_load'] += 2 * num_infected
            routes_affected = current_node['routes']
            for route in routes_affected:
                stations_affected = self.model.subway_graph.routing_dict[route]
                for station in stations_affected:
                    if station != self._location:
                        self.model.subway_graph.graph.nodes[station]['viral_load'] += 2 * num_infected
        return None

    def update_agent_health(self):
        # update beta based on viral load
        viral_load = self.model.subway_graph.graph.nodes[self._location]['viral_load']
        self._epi_characteristics['beta'] += \
            max(2, viral_load / 100)  # TODO: this is also just some crap I made up

        # also give a chance to convert purely based on viral load
        susceptible = self._population[AgentParams.STATUS_SUSCEPTIBLE]
        if viral_load >= 20:
            outside_infection_chance_roll = (viral_load - 20) / 1e9 # TODO: just some random crap I made up
            self._population[AgentParams.STATUS_SUSCEPTIBLE] -= susceptible * outside_infection_chance_roll
            self._population[AgentParams.STATUS_EXPOSED] += susceptible * outside_infection_chance_roll

        super().update_agent_health()

    def step(self):
        self.move()
        self.update_agent_health()