import random
from mesa import Agent
from decimal import Decimal as D

class Train(Agent):
    def __init__(self, unique_id, model, network, route):
        super().__init__(unique_id, model)
        self.network = network
        self.route = route
        
        self.route_id = route.iloc[0]['ID']
        self.line_name = route.iloc[0]['LINE']
        self.direction = route.iloc[0]['DIRECTION']

        self.reset()

    def step(self):
        """Activates the agent and stages any necessary changes, but does not apply them yet"""
        if self.has_finished:
            return

        try:
            current = self.route.iloc[self.station_number]
            station = self.network.get_stations()[current['STATION_NAME']]
            platform = station.get_platform(self.line_name, self.direction)
        except Exception as e:
            print('number: ', self.station_number)
            print(self.route)
            raise e
        
        arrival_time = current['ARRIVAL_TIME']
        departure_time = current['ARRIVAL_TIME']
        is_end = current['IS_END']
        
        network_time = self.network.get_time()
        if arrival_time <= network_time and network_time <= departure_time:
            if arrival_time == network_time:
                # Based on the weight of the station, drop passengers
                weight_current = station.get_weight(self.line_name, network_time)[1]
                weight_next = D(0)
                for st_name, w_next in station.get_weight(self.line_name, network_time, self.direction).items():
                    if st_name == station.get_name():
                        continue
                    else:
                        weight_next = weight_next + w_next[1]
                
                # Do N random choices for the N passengers where 1 means that the passenger has arrived
                p_random = random.choices([0,1],
                                          weights=[float(weight_next), float(weight_current)],
                                          k=len(self.passengers))
                drop_passengers = [p for i, p in enumerate(self.passengers) if p_random[i] == 1]
                self.passengers = [p for i, p in enumerate(self.passengers) if p_random[i] == 0]
                
                platform.notify_arrived_passengers(drop_passengers)
                
                # Notify train arrival to the station
                station.notify_train_arrival(self, self.line_name, self.direction)
            
            if is_end:
                # Drop all passengers since it is the end of the route
                passengers = self.pop_passengers()
                platform.notify_arrived_passengers(passengers)
                
                # Notify to the network that the train has finished the route
                self.network.notify_finish_route(self)
                self.has_finished = True
            elif network_time == departure_time:
                station.notify_train_departure(self, self.line_name, self.direction)
                self.station_number = self.station_number + 1
    
    def advance(self):
        """Applies the changes of step()"""
        pass
    
    def add_passengers(self, passengers):
        self.passengers = self.passengers + passengers
        for p in passengers:
            p.set_current_place(self)
        return self
    
    def get_passengers(self):
        return self.passengers

    def pop_passengers(self, weight_stay=None, weight_drop=None):
        """
        Returns the passengers in the train. If weight_stay and weight_drop are given,
        then it computes the probability that a passenger leaves the train or stay in it (if
        they did not reach the max number of transfers yet)
        """
        if weight_stay is not None and weight_drop is not None:
            passengers = [p.add_transfer() for p in self.passengers if not p.has_max_transfers()]
            p_random = random.choices([0,1],
                                      weights=[float(weight_stay), float(weight_drop)],
                                      k=len(passengers))
            drop_passengers = [p for i, p in enumerate(passengers) if p_random[i] == 1]
            
            # Update list of passengers which stay in the train
            stay_passengers_ids = [p.get_id() for i, p in enumerate(passengers) if p_random[i] == 0]
            self.passengers = [p for p in self.passengers if p.has_max_transfers() or p.get_id() in stay_passengers_ids]
        else:
            drop_passengers = self.passengers
            self.passengers = []
        return drop_passengers
    
    def get_route_id(self):
        return self.route_id
    
    def get_n_passengers(self):
        return len(self.passengers)

    def get_time_infections(self):
        return self.time_infections

    def get_n_infections(self):
        return len(self.time_infections)
    
    def add_infection(self):
        self.time_infections.append(self.network.get_time())
        return self

    def reset(self):
        self.passengers = []
        self.station_number = 0
        self.has_finished = False
        self.time_infections = []
