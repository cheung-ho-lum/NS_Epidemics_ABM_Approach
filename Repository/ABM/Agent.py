from mesa import Agent
STATUS_SUSCEPTIBLE = 'Susceptible'
STATUS_EXPOSED = 'Exposed'
STATUS_INFECTED = 'Infected'
STATUS_RECOVERED = 'Recovered'


class SEIRAgent(Agent):
    """This guy's constructor should probably have a few more params"""
    def __init__(self, unique_id, model, location=-1):
        super().__init__(unique_id, model)
        self._infection_status = STATUS_SUSCEPTIBLE
        self._location = location

    #For now, move to any adjacent node in the graph
    #A reminder that while in the subway, they should move from src to destination instead of station to station
    def move(self):
        possible_moves = list(self.model.graph.neighbors(self._location))
        if len(possible_moves) > 0:
            self._location = self.random.choice(possible_moves)
        else:
            #Do nothing, but actually...
            print('odd, agent', self.unique_id, 'stuck at', self._location)

    def step(self):
        self.move()

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
