from mesa import Agent
from Parameters import AgentParams
from Parameters import SubwayParams


DEBUG_SEIR_INFECTED_INITIALIZATION = [1] #Agents here start out infected.
PRINT_DEBUG = False

class SEIRAgent(Agent):
    """This guy's constructor should probably have a few more params"""
    def __init__(self, unique_id, model, location=-1):
        super().__init__(unique_id, model)
        self._infection_status = AgentParams.STATUS_SUSCEPTIBLE
        if unique_id in DEBUG_SEIR_INFECTED_INITIALIZATION:
            self._infection_status = AgentParams.STATUS_INFECTED
        self._location = location
        self._time_first_exposure = -1
        self._time_first_infection = -1

    def move(self):
        # For now, move to any adjacent node in the graph
        # A reminder that while in the subway, they should move from src to destination instead of station to station
        possible_moves = list(self.model.our_graph.graph.neighbors(self._location))
        if len(possible_moves) > 0:
            new_location = self.random.choice(possible_moves)
            if PRINT_DEBUG:
                print('Agent', self.unique_id, self._infection_status, 'moved from', self._location, 'to', new_location)
            self.model.update_agent_location(self, self._location, new_location) #Also update the model
            self._location = new_location
        else:
            #Do nothing, but actually...
            if PRINT_DEBUG:
                print('ERR?!: agent', self.unique_id, 'stuck at', self._location)


    def find_victims(self, map_location):
        """TODO: BELONGS IN A GRAPH WRAPPER!! but it's 3pm so I write here
        This function assumes you already checked the node location and everything.
        All it does is find peeople at the same location"""
        victim_list = []
        for a in self.model.agent_loc_dictionary[self._location]:
            if a is not self:
                if a.infection_status == AgentParams.STATUS_SUSCEPTIBLE:
                    victim_list.append(a)
        return victim_list

    def infect(self):
        # I an imagining different behavior if a person is asymptomatic, but let's just KISS rn
        # Infected (and infected_asymptomatic) people are allowed to infect susceptible ppl w/ probability 0.05
        # But only if they are in the subway!
        if self._infection_status == AgentParams.STATUS_INFECTED or \
                self._infection_status == AgentParams.STATUS_INFECTED_ASYMPTOMATIC:
            if self.model.our_graph.graph.nodes[self._location]['type'] == SubwayParams.NODE_TYPE_STATION:
                #TODO: There is a massive performance hit here finding the victims
                #TODO: Probably best to have a dictionary of locations and agents.
                #TODO: Also, it's high time you created your graph wrapper class
                victim_agents = self.find_victims(self._location)
                for a in victim_agents:
                    if a.infection_status == AgentParams.STATUS_SUSCEPTIBLE:
                        a.infection_status = AgentParams.STATUS_EXPOSED #TODO: and this should be in a method
                        if PRINT_DEBUG:
                            print('Agent', self.unique_id, '(', self._infection_status, ') exposed',
                                a.unique_id, 'at', a.location)
        return None

        # TODO: Obviously we should be checking time of first exposure
        # And possibly rolling dice against it.
        # But let's just say it takes 1 unit of time.
    def update_agent_health(self):
        if(self._infection_status == AgentParams.STATUS_EXPOSED):
            self._infection_status = AgentParams.STATUS_INFECTED
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
