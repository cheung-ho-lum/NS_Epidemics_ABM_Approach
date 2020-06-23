import datetime
from decimal import Decimal as D

class Platform():
    def __init__(self, network, line, station, direction, timetable):
        self.network = network
        self.line = line
        self.station = station
        self.direction = direction
        self.MAX_WAIT = 30
        
        # Weight of the platform based on the weight of the next stations
        line_name = line.get_name()
        
        w_in = D(0)
        w_out = D(0)
        
        for st_name, st_w in station.get_weight(line_name=line_name, direction=direction).items():
            w_in = w_in + st_w[0]
            w_out = w_out + st_w[0]
        
        w_out = w_out if station.has_next_stations(line_name, direction) else D(0)
        
        self.weight = (w_in, w_out)
        
        st_name = station.get_name()
        self.open_time, self.close_time = network.get_open_close_times(line_name, st_name, direction)
        
        # Get times of trains which stop in the station
        routes = timetable.reset_index(level=['LINE', 'STATION_NAME'])
        routes = routes.loc[(routes['LINE'] == line.get_name()) &
                            (routes['STATION_NAME'] == station.get_name()) &
                            (routes['DIRECTION'] == direction)]
        self.arrival_times = routes['ARRIVAL_TIME'].tolist()
        self.departure_times = routes.loc[routes['IS_END'] != 1]['DEPARTURE_TIME'].tolist()
        self.arrival_times.sort()
        self.departure_times.sort()
        
        if self.network.open_time > self.network.close_time:
            if len(self.arrival_times) > 0 and self.arrival_times[0] < self.network.close_time and self.arrival_times[-1] > self.network.close_time:
                while self.arrival_times[0] < self.network.close_time:
                    t_arrival = self.arrival_times.pop(0)
                    self.arrival_times.append(t_arrival)
            if len(self.departure_times) > 0 and self.departure_times[0] < self.network.close_time and self.departure_times[-1] > self.network.close_time:
                while self.departure_times[0] < self.network.close_time:
                    t_departure = self.departure_times.pop(0)
                    self.departure_times.append(t_departure)
        
        self.reset()
    
    def get_weight(self):
        """
        Returns the weight of the platform. Recall that the weight is based on the
        stations in the direction of this one, so it might be greater than 1
        """
        return self.weight
    
    def get_station(self):
        return self.station

    def get_line(self):
        return self.line
    
    def get_direction(self):
        return self.direction
    
    def add_passengers(self, passengers):
        self.count_in = self.count_in + len(passengers)
        if self.train is None:
            self.count_wait_in_platform = self.count_wait_in_platform + len(passengers)
            self.passengers = self.passengers + passengers
            for p in passengers:
                p.set_current_place(self)
        else:
            self.train.add_passengers(passengers)
    
    def get_passengers(self):
        return self.passengers
    
    def pop_passengers(self):
        """Returns the passengers in the station and remove them from the queue"""
        passengers = self.passengers
        self.passengers = []
        return passengers
    
    def get_n_passengers(self, count_train=False):
        n_passengers = len(self.passengers)
        if count_train and self.train is not None:
            n_passengers = n_passengers + self.train.get_n_passengers()
        return n_passengers
    
    def is_closed(self):
        """If the platform does not admit more passengers, this function returns True"""
        if self.close_time is None:
            return False
        
        time = self.network.get_time()
        if self.close_time > self.open_time:
            return time < self.open_time or time >= self.close_time
        else:
            return time < self.open_time and time >= self.close_time
    
    def allow_passengers(self):
        if len(self.departure_times) > self.next_departure:
            delta = datetime.timedelta(minutes=self.MAX_WAIT)
            
            time_departure = self.departure_times[self.next_departure]
            time_departure = datetime.datetime(100, 1, 1, time_departure.hour, time_departure.minute, 0)
            
            outcoming_train = (time_departure + delta).time() > self.network.get_time()
        else:
            outcoming_train = False
        
        return not self.is_closed() and outcoming_train

    def get_time_infections(self):
        return self.time_infections

    def get_n_infections(self):
        return len(self.time_infections)
    
    def get_count_wait_in_platform(self):
        """Returns the number of passengers who have been waiting for a train in a platform of the station"""
        return self.count_wait_in_platform

    def get_count_in(self):
        return self.count_in
    
    def get_count_out(self):
        return self.count_out

    def add_infection(self):
        self.time_infections.append(self.network.get_time())
        return self

    def notify_arrived_passengers(self, passengers):
        self.count_out = self.count_out + len(passengers)
        self.network.notify_arrived_passengers(self.station, passengers)

    def notify_train_arrival(self, train):
        self.next_arrival = self.next_arrival + 1
        
        self.train = train
        passengers = self.pop_passengers()
        self.train.add_passengers(passengers)
        
        return self
    
    def notify_train_departure(self):
        self.next_departure = self.next_departure + 1
        self.train = None
    
    def reset(self):
        self.train = None
        self.passengers = []
        self.next_arrival = 0
        self.next_departure = 0
        self.time_infections = []
        self.count_in = 0
        self.count_out = 0
        self.count_wait_in_platform = 0
