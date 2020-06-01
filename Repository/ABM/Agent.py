from mesa import Agent
from Parameters import AgentParams
from Parameters import SubwayParams
import random

DEBUG_SEIR_INFECTED_INITIALIZATION = [1] #Agents here start out infected.
PRINT_DEBUG = False

class SEIRAgent(Agent):
    """This guy's constructor should probably have a few more params"""
    def __init__(self, unique_id, model, location=-1, home_addr=-1, work_addr=-1):
        super().__init__(unique_id, model)
        self._infection_status = AgentParams.STATUS_SUSCEPTIBLE
        self._location = location
        self._time_first_exposure = -1
        self._time_first_infection = -1
        self._home_addr = home_addr
        self._work_addr = work_addr
        self._subway_commuter = True  # Envisioning some non subway riders in this system eventually.
        if unique_id in DEBUG_SEIR_INFECTED_INITIALIZATION:
            self._infection_status = AgentParams.STATUS_INFECTED
            if self.model.our_graph.graph.has_node(451):  # 451 - Junction blvd. 55 - Brighton beach
                self._location = 451
                self._home_addr = 451
            else:
                self._location = 1
                self._home_addr = 1
            print('patient 0 initialized at', self._location)

    def move(self):
        # For now, agents do not move!
        return None
        # A reminder that while in the subway, they should move from src to destination instead of station to station
        #possible_moves = list(self.model.our_graph.graph.neighbors(self._location))
        #if len(possible_moves) > 0:
        #    new_location = self.random.choice(possible_moves)
        #    if PRINT_DEBUG:
        #        print('Agent', self.unique_id, self._infection_status, 'moved from', self._location, 'to', new_location)
        #    self.model.update_agent_location(self, self._location, new_location) #Also update the model
        #    self._location = new_location
        #else:
        #    #Do nothing, but actually, for now:
        #    if PRINT_DEBUG:
        #        print('ERR?!: agent', self.unique_id, 'stuck at', self._location)


    # def find_victims(self, map_location):
    #     """This function assumes you already checked the node location and everything.
    #     All it does is find peeople at the same location"""
    #     victim_list = []
    #     for a in self.model.agent_loc_dictionary[self._location]:
    #         if a is not self:
    #             if a.infection_status == AgentParams.STATUS_SUSCEPTIBLE:
    #                 victim_list.append(a)
    #     return victim_list

    def infect(self):
        # Agents now infect their current location with viral load +100 (total = 100)
        # Nearest neighbors get +30 (total, if on same line = 50)
        # Stations on the same route get a viral load of +20 (regardless of distance)
        if self._infection_status == AgentParams.STATUS_INFECTED or \
                self._infection_status == AgentParams.STATUS_INFECTED_ASYMPTOMATIC:
            current_node = self.model.our_graph.graph.nodes[self._location]
            if current_node['type'] == SubwayParams.NODE_TYPE_STATION:
                current_node['viral_load'] += 100
                for nn in self.model.our_graph.graph.neighbors(self._location):
                    self.model.our_graph.graph.nodes[nn]['viral_load'] += 20
                routes_affected = current_node['routes']
                for route in routes_affected:
                    stations_affected = self.model.our_graph.routing_dict[route]
                    for station in stations_affected:
                        if station != self._location:
                            self.model.our_graph.graph.nodes[station]['viral_load'] += 10
        return None

        # TODO: Obviously we should be checking time of first exposure
        # And possibly rolling dice against it.
        # But let's just say it takes 1 unit of time.
    def update_agent_health(self):
        #If susceptible, roll based on current location (currently arbitrarily set by me)
        if self._infection_status == AgentParams.STATUS_SUSCEPTIBLE:
            viral_load = self.model.our_graph.graph.nodes[self._location]['viral_load']
            if viral_load >= 100:
                if random.randint(0, viral_load) > 50: #have a chance to dodge based on 'natural immunity'
                    self._infection_status = AgentParams.STATUS_EXPOSED
                    self._time_first_exposure = self.model.schedule.time
        #If exposed, move to next stage given enough time has passed
        if self._infection_status == AgentParams.STATUS_EXPOSED:
            if self.model.schedule.time > AgentParams.TIME_TO_INFECTION + self._time_first_exposure:
                if random.randint(0,100) > 50:
                    self._infection_status = AgentParams.STATUS_INFECTED
                    self._time_first_infection = self.model.schedule.time
        #If infected, move to recovered given enough time has passed
        if self._infection_status == AgentParams.STATUS_INFECTED:
            if self.model.schedule.time > AgentParams.TIME_TO_RECOVER + self._time_first_infection:
                if random.randint(0,100) > 50:
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
    def home_addr(self):
        return self._home_addr

    @home_addr.setter
    def home_addr(self, value):
        self._home_addr = value

    @property
    def work_addr(self):
        return self._work_addr

    @work_addr.setter
    def work_addr(self, value):
        self._work_addr = value

    @property
    def time_first_exposure(self):
        return self._time_first_exposure

    @time_first_exposure.setter
    def time_first_exposure(self, value):
        self._time_first_exposure = value

    @property
    def time_first_infection(self):
        return self._time_first_infection

    @time_first_infection.setter
    def time_first_infection(self, value):
        self._time_first_infection = value
