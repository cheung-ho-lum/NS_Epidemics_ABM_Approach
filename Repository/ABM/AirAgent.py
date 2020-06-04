from ABM import SEIR_Agent
from Parameters import AgentParams
from Parameters import SubwayParams
import random

DEBUG_SEIR_INFECTED_INITIALIZATION = [1] #Agents here start out infected.
PRINT_DEBUG = False


class AirAgent(SEIR_Agent.SEIR_Agent):
    """This guy's constructor should probably have a few more params"""
    def __init__(self, unique_id, model, location=-1, population=0,
                 epi_characteristics={'alpha': AgentParams.DEFAULT_ALPHA}):
        super().__init__(unique_id, model, location)
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
        if self._infection_status == AgentParams.STATUS_INFECTED:
            self.model.airway_graph.graph.nodes[self._location]['viral_load'] += 100
            for nn in self.model.airway_graph.graph.neighbors(self._location):
                self.model.airway_graph.graph.nodes[nn]['viral_load'] += 20
        return None

        # TODO: Obviously we should be checking time of first exposure
        # And possibly rolling dice against it.
        # But let's just say it takes 1 unit of time.
    def update_agent_health(self):
        #If susceptible, roll based on current location (currently arbitrarily set by me)
        if self._infection_status == AgentParams.STATUS_SUSCEPTIBLE:
            viral_load = self.model.airway_graph.graph.nodes[self._location]['viral_load']
            if viral_load >= 100:
                if random.randint(0, viral_load) > 50: #have a chance to dodge based on 'natural immunity'
                    self._infection_status = AgentParams.STATUS_EXPOSED
                    self._time_first_exposure = self.model.schedule.time
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
