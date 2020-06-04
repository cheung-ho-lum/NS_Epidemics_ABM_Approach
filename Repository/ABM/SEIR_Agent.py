from Parameters import AgentParams
import random
from mesa import Agent

class SEIR_Agent(Agent):
    """Base Agent type"""
    def __init__(self, unique_id, model, location=-1):
        super().__init__(unique_id, model)
        self._infection_status = AgentParams.STATUS_SUSCEPTIBLE
        self._location = location
        self._time_first_exposure = -1
        self._time_first_infection = -1

    def move(self):
        # For now, agents do not move!
        return None

    def infect(self):
        # Default infection behavior
        if self._infection_status == AgentParams.STATUS_INFECTED:
            return None

    def update_agent_health(self):
        # Default agent behavior
        #If exposed, move to next stage given enough time has passed
        if self._infection_status == AgentParams.STATUS_EXPOSED:
            if self.model.schedule.time > AgentParams.TIME_TO_INFECTION + self._time_first_exposure:
                if random.randint(0, 100) > 50:
                    self._infection_status = AgentParams.STATUS_INFECTED
                    self._time_first_infection = self.model.schedule.time

        #If infected, move to recovered given enough time has passed
        if self._infection_status == AgentParams.STATUS_INFECTED:
            if self.model.schedule.time > AgentParams.TIME_TO_RECOVER + self._time_first_infection:
                if random.randint(0, 100) > 50:
                    self._infection_status = AgentParams.STATUS_RECOVERED
        return None

    def step(self):
        self.move()
        self.infect()
        self.update_agent_health()

    @property
    def infection_status(self):
        return self._infection_status

    @infection_status.setter
    def infection_status(self, value):
        self._infection_status = value

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        self._location = value

    @property
    def infection_status(self):
        return self._infection_status

    @infection_status.setter
    def infection_status(self, value):
        self._infection_status = value

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        self._location = value