from mesa import Agent


from .utils import State


def number_infected_passengers(model, state='INFECTED'):
    return sum([1 for a in model.grid.get_all_cell_contents() if type(a) == Passenger and  a.state is state])


def number_of_passengers(model):
    return sum([1 for a in model.grid.get_all_cell_contents() if type(a) == Passenger])


class Hub(Agent):
    def __init__(
        self,
        unique_id,
        model,
        initial_state,
        virus_spread_chance,
        preventive_measures,
    ):
        super().__init__(unique_id, model)

        self.state = initial_state

        self.virus_spread_chance = virus_spread_chance
        self.preventive_measures = preventive_measures

        # Increase or decrease spread based on travel time and population at any point in time
        # factor in virus spread chance and preventive measures



class Passenger(Agent):
    def __init__(self, unique_id, model, initial_state='SUSCEPTIBLE', moore=False, threshold=3):
        super().__init__(unique_id, model)
        self.moore = moore
        self.state = initial_state
        self.threshold = threshold
        self.number_trips = 0

    def random_move(self):
      
        next_moves = self.model.grid.get_neighbors(self.pos, include_center=False)
        next_move = self.random.choice(next_moves)
        self.model.grid.move_agent(self, next_move)
        agents = self.model.grid.get_cell_list_contents([next_move])
        for agent in agents:
            if type(agent) == Passenger and agent.state == 'INFECTED':
                # Add percentage likelyhood
                # Percentage likelyhood can be computed as ratio of population at node (population density at hub)
                self.state =  'INFECTED'
            if type(agent) == Hub and agent.state == State.INFECTED:
                # Add percentage likelyhood
                # Likelyhood can be computed based on likelyhood of virus spreading and preventive measures
                self.state =  'INFECTED'
            elif type(agent) == Hub and self.state == 'INFECTED':
                # Add percentage likelyhood (I don't know :))
                agent.state = State.INFECTED

    def step(self):
        self.random_move()
        # Must limit moves to 3, then exit metro
        # Must remove node from metro if infected
