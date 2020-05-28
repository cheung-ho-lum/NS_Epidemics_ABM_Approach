from mesa import Model
from ABM import Agent
from mesa.time import RandomActivation
import random

DEBUG_START_LOCATIONS = [4, 5, 6] #these are the street locations for the debug scenario


class SEIR_Subway_Model(Model):
    """This guy's constructor should probably have a few more params."""
    def __init__(self, n, subway_map):
        self.num_agents = n
        self._graph = subway_map
        self.schedule = RandomActivation(self)
        # Create agents
        # Should create agents, and (for now) place them in random street locations
        for i in range(self.num_agents):
            start_location = random.choice(DEBUG_START_LOCATIONS)
            a = Agent.SEIRAgent(i, self, location=start_location)
            self.schedule.add(a)

    def step(self):
        self.schedule.step()

    @property
    def graph(self):
        return self._graph

    @graph.setter
    def graph(self, value):
        self._graph = value
