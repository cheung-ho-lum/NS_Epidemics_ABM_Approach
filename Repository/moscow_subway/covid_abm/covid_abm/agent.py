from mesa import Agent


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

    def step(self):
        self.random_move()
        # Must limit moves to 3, then exit metro
        # if self.number_trips <= self.threshold:
        #     self.number_trips += 1
        # else:
        #     self.model.grid._remove_agent(self.pos, self)
        #     self.model.schedule.remove(self)
