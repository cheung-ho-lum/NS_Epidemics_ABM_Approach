from ABM import SEIR_Agent
from Parameters import AgentParams
from Parameters import SubwayParams
import random

DEBUG_SEIR_INFECTED_INITIALIZATION = [1] #Agents here start out infected.
PRINT_DEBUG = False


class AirAgent(SEIR_Agent.SEIR_Agent):
    """This guy's constructor should probably have a few more params"""
    def __init__(self, unique_id, model, location=-1, population=0,
                 epi_characteristics=None):
        super().__init__(unique_id, model, location, population, epi_characteristics)
        self._infection_status = AgentParams.STATUS_SUSCEPTIBLE
        if unique_id in DEBUG_SEIR_INFECTED_INITIALIZATION:
            self._infection_status = AgentParams.STATUS_INFECTED
            if self.model.airway_graph.graph.has_node(3376):  # 3376 - Wuhan Tianhe
                self._location = 3376
            else:
                self._location = list(self.model.airway_graph.graph.nodes())[0]
            print('patient 0 initialized at', self._location)

    def move(self):
        # For now, agents do not move!
        return None

    def infect(self):
        # Infected people now infect their current location with viral load +100 (total = 100)
        # Neighboring stations get +20
        current_node = self.model.airway_graph.graph.nodes[self._location]
        num_infected = self._population[AgentParams.STATUS_INFECTED]
        if num_infected > 0:
            current_node['viral_load'] += 10 * num_infected
            for nn in self.model.airway_graph.graph.neighbors(self._location):
                self.model.airway_graph.graph.nodes[nn]['viral_load'] += 2 * num_infected

    def update_agent_health(self):
        #update beta based on viral load
        viral_load = self.model.airway_graph.graph.nodes[self._location]['viral_load']
        self._epi_characteristics['beta'] += \
            max(2, viral_load / 100)  # TODO: this is also just some crap I made up

        #also give a chance to convert purely based on viral load
        susceptible = self._population[AgentParams.STATUS_SUSCEPTIBLE]
        if viral_load >= 20:
            outside_infection_chance_roll = (viral_load - 20) / 1e9 # TODO: just some random crap I made up
            self._population[AgentParams.STATUS_SUSCEPTIBLE] -= susceptible * outside_infection_chance_roll
            self._population[AgentParams.STATUS_EXPOSED] += susceptible * outside_infection_chance_roll

        super().update_agent_health()

    def step(self):
        self.move()
        self.update_agent_health()
