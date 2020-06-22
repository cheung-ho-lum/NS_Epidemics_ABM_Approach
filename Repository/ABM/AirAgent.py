from ABM.SEIR_Agent import SEIR_Agent
from Parameters import AgentParams


class AirAgent(SEIR_Agent):
    """This guy's constructor should probably have a few more params"""
    def __init__(self, unique_id, model, location=-1, population=0,
                 epi_characteristics=None):
        super().__init__(unique_id, model, location, population, epi_characteristics)

    def move(self):
        # For now, agents do not move!
        return None

    def infect(self):
        # Infected people now infect their current location with viral load +100 (total = 100)
        # Neighboring stations get +20
        nx_graph = self.model.airway_graph.graph
        current_node = nx_graph.nodes[self._location]
        passenger_flow = current_node['flow']
        num_infected = self._population[AgentParams.STATUS_INFECTED]
        if num_infected > 0:
            # current_node['viral_load'] += 10 * num_infected
            # TODO: don't ask, but in this model, viral load only updated from outside
            for nn in nx_graph.neighbors(self._location):
                pair_flow = nx_graph[self._location][nn]['pair_flow']
                nx_graph.nodes[nn]['viral_load'] += num_infected * pair_flow/passenger_flow  # TODO: also crap I made up

    def update_agent_health(self):
        # update beta based on viral load
        viral_load = self.model.airway_graph.graph.nodes[self._location]['viral_load']
        # self._epi_characteristics['beta'] = min(2, viral_load / 100)  # TODO: this is also just some crap I made up

        # also give a chance to convert purely based on viral load
        susceptible = self._population[AgentParams.STATUS_SUSCEPTIBLE]
        if viral_load >= 10:  # 10 people 'travelled' to this place
            # print('now rolling:', self._location, self.model.airway_graph.graph.nodes[self._location]['name'],
            #      self.model.airway_graph.graph.nodes[self._location]['IATA'])
            outside_infection_chance_roll = viral_load / 1e9  # TODO: just some random crap I made up
            self._population[AgentParams.STATUS_SUSCEPTIBLE] -= susceptible * outside_infection_chance_roll
            self._population[AgentParams.STATUS_EXPOSED] += susceptible * outside_infection_chance_roll

        super().update_agent_health()

    def step(self):
        self.move()
        self.update_agent_health()
