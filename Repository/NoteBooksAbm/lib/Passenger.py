import random
from mesa import Agent

"""
status:
  0: waiting - not assigned to any place yet
  1: moving
  2: arrived - already at the destination
infected_status:
  0: susceptible
  1: exposed
  2: infected
  3: recovered
"""

class Passenger(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.reset()
    
    def set_origin(self, station):
        self.origin = station
        return self
    
    def get_origin(self):
        return self.origin

    def set_destination(self, station):
        self.destination = station
        return self
    
    def get_destination(self, station):
        return self.destination
    
    def set_current_place(self, place):
        """The current place of a passenger might be a Platform or a Train"""
        self.current_place = place
    
    def get_current_place(self):
        return self.current_place
    
    def get_id(self):
        return self.unique_id
    
    def set_status(self, status):
        self.status = status
        return self
    
    def get_status(self):
        return self.status
    
    def set_infected_status(self, status=None, infected_by=None):
        if status is not None:
            self.infected_status = status
        if infected_by is not None:
            self.infected_by = infected_by
        return self
    
    def get_infected_status(self):
        return self.infected_status
    
    def set_infection_p(self, p):
        self.infection_p = p
        return self
    
    def get_infection_p(self):
        return self.infection_p

    def add_transfer(self):
        self.n_transfers = self.n_transfers + 1
        return self
    
    def has_max_transfers(self):
        return self.n_transfers == self.MAX_TRANSFERS

    def get_n_infections(self):
        return self.n_infections
    
    def add_infection(self):
        self.n_infections = self.n_infections + 1
        return self
    
    def get_r0(self):
        if len(self.seen_passengers) == 0:
            return 0
        else:
            return self.n_infections / len(self.seen_passengers)
    
    def step(self):
        """Activates the agent and stages any necessary changes, but does not apply them yet"""
        if self.get_infected_status() == 2 and self.get_status() == 1:
            # If the passenger is infected, let's infect to more people >:D
            self.step_infection()
    
    def step_infection(self):
        place = self.get_current_place()
        other_passengers = [p for p in place.get_passengers() if p.get_id() != self.get_id()]

        # Make random infections (note that they may already be infected, thus those cases will be just ignored)
        p_random = random.choices([True, False], weights=[self.infection_p, 1 - self.infection_p], k=len(other_passengers))
        
        for i, p in enumerate(other_passengers):
            # Notify as passenger seen
            p.notify_passenger_seen(self)
            self.notify_passenger_seen(p)

            # Infect passenger
            if p.get_infected_status() == 0 and p_random[i]:
                p.set_infected_status(1, self)
                self.add_infection()
                place.add_infection()

    def advance(self):
        """Applies the changes of step()"""
        pass

    def notify_passenger_seen(self, passenger):
        self.seen_passengers[passenger.get_id()] = passenger
        return self
    
    def reset(self):
        self.origin = None
        self.destination = None
        self.current_place = None
        self.status = 0
        self.n_transfers = 0
        self.MAX_TRANSFERS = 1
        self.infected_status = 0
        self.n_infections = 0
        self.infection_p = 0
        self.seen_passengers = {}
    
    def __eq__(self, other):
        """Checks if this agent is the same as other"""
        return self.get_id() == other.get_id()
