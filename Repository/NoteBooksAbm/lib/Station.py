import random
from decimal import Decimal as D
from .Platform import Platform

class Station():
    def __init__(self, network, name, w_stations):
        # Arguments
        self.network = network
        self.name = name
        
        self.platforms = {}
        self.next_stations = {}
        self.lines = {}
        
        # Save weights for this station
        self.w_station = w_stations.reset_index()
        self.w_station = self.w_station.loc[self.w_station['STATION_NAME'] == name]
        self.w_station_line = self.w_station.groupby('LINE').sum() # Precompute to speed-up
    
    def init_connections(self, next_stations):
        self.next_stations = next_stations
    
    def init_station(self, timetable, lines, directions=2):
        self.lines = lines
        
        # Create platforms
        for line_name, line in self.lines.items():
            self.platforms[line_name] = {}
            for d in range(directions):
                p = Platform(self.network, line, self, d, timetable)
                self.platforms[line_name][d] = p
    
    def get_lines(self):
        return self.lines
    
    def add_passengers(self, passengers):
        n_passengers = len(passengers)
        platforms = [p for _, platforms in self.platforms.items() for _, p in platforms.items()]
        platforms = [p for p in platforms if p.allow_passengers()]
        
        p_weights = [float(p.get_weight()[0]) for p in platforms]
        
        p_random = random.choices(platforms, weights=p_weights, k=n_passengers)
        
        for i in range(len(p_random)):
            p_random[i].add_passengers([passengers[i]])
            i = i + 1
            
        return self
    
    def pop_passengers(self):
        passengers = []
        for _, platforms in self.platforms.items():
            for _, p in platforms.items():
                passengers = passengers + p.pop_passengers()
        return passengers

    def get_time_infections(self):
        time_infections = []
        for _, platforms in self.platforms.items():
            for _, p in platforms.items():
                time_infections = time_infections + p.get_time_infections()
        return time_infections

    def get_n_infections(self):
        n_infections = 0
        for _, platforms in self.platforms.items():
            for _, p in platforms.items():
                n_infections = n_infections + p.get_n_infections()
        return n_infections

    def has_next_stations(self, line_name, direction):
        if direction not in self.next_stations[line_name]:
            return False
        elif len(self.next_stations[line_name][direction]) == 0:
            return False
        return True
    
    def get_weight(self, line_name=None, time=None, direction=None, step=0, max_steps=2):
        """
        Returns the weight of the station as an integer and, if add_directions given, then it returns
        the weights of all stations in the given direction as a dictionary.
        If time is None, it returns the weight of the station regardless the time.
        """
        if time is None:
            # Use pre-computed table if no time is required
            if line_name is None:
                w = self.w_station_line.sum()
                w_in = w['WEIGHT_IN']
                w_out = w['WEIGHT_OUT']
            else:
                w_in = self.w_station_line.at[line_name, 'WEIGHT_IN']
                w_out = self.w_station_line.at[line_name, 'WEIGHT_OUT']
        
        else:
            # If time is given, search in table of weights
            conditions = self.w_station['STATION_NAME'] == self.name
            if line_name is not None:
                conditions = conditions & (self.w_station['LINE'] == line_name)
            if time is not None:
                conditions = conditions & (self.w_station['TIME'] == time)

            w_in = self.w_station.loc[conditions]
            w_out = self.w_station.loc[conditions]
        
            if w_in.size == 0:
                w_in = D(0)
                w_out = D(0)
            else:
                w_in = w_in.sum()['WEIGHT_IN']
                w_out = w_out.sum()['WEIGHT_OUT']
        
        # If a direction is given, returns weights as a dictionary
        if direction is not None:
            weights = {self.name: (w_in, w_out)}
            step = step + 1
            
            if direction not in self.next_stations[line_name] or step >= max_steps:
                return weights

            next_stations = self.next_stations[line_name][direction]
            for _, s in next_stations.items():
                weights_next = s.get_weight(line_name, time, direction, step, max_steps)
                for next_st_name, next_w in weights_next.items():
                    weights[next_st_name] = next_w

            return weights
        else:
            return (w_in, w_out)
    
    def get_name(self):
        return self.name
    
    def get_platform(self, line_name, direction):
        return self.platforms[line_name][direction]
    
    def get_count_in(self):
        count_in = 0
        for _, platforms in self.platforms.items():
            for _, platform in platforms.items():
                count_in = count_in + platform.get_count_in()
        
        return count_in
    
    def get_n_passengers(self, count_train=True):
        n_passengers = 0
        for _, platforms in self.platforms.items():
            for _, platform in platforms.items():
                n_passengers = n_passengers + platform.get_n_passengers(count_train=count_train)
        
        return n_passengers
    
    def is_closed(self):
        """If the station does not admit more passengers, this function returns True"""
        closed = True
        for _, platforms in self.platforms.items():
            for _, platform in platforms.items():
                closed = closed and platform.is_closed()
        return closed
    
    def allow_passengers(self):
        allow_in_platform = False
        for _, platforms in self.platforms.items():
            for _, platform in platforms.items():
                allow_in_platform = allow_in_platform or platform.allow_passengers()
        return allow_in_platform
    
    def notify_train_arrival(self, train, train_line_name, train_direction):
        train_platform = self.platforms[train_line_name][train_direction]
        
        train_platform.notify_train_arrival(train)
        
        # Compute weights of staying/leaving the train based on the weights of the lines
        weight_stay = self.lines[train_line_name].get_weight()[0]
        weight_drop = D(0)
        
        for line_name, line in self.lines.items():
            if line.allow_passengers():
                weight_drop = weight_drop + line.get_weight()[0]
        
        # Compute weights of platforms in the station (except the current line) and transfer passengers
        change_platforms = []
        change_weights = []
        for platform_line_name, platforms in self.platforms.items():
            if platform_line_name == line_name:
                continue
            else:
                change_platforms = change_platforms + [p for _, p in platforms.items() if p.allow_passengers()]
                change_weights = change_weights + [p.get_weight()[0] for _, p in platforms.items() if p.allow_passengers()]
        
        # Transfer passengers to other platforms (if possible)
        passengers = train.pop_passengers(weight_stay, weight_drop)
        if len(passengers) == 0 or len(change_platforms) == 0:
            return

        change_weights = [float(w) for w in change_weights] # Cast to float
        p_random = random.choices(change_platforms, weights=change_weights, k=len(passengers))
        for i, p in enumerate(passengers):
            p_random[i].add_passengers([p])
    
    def notify_train_departure(self, train, line_name, direction):
        train_platform = self.platforms[line_name][direction]
        train_platform.notify_train_departure()
    
    def reset(self):
        for _, platforms in self.platforms.items():
            for _, platform in platforms.items():
                platform.reset()

    def __del__(self):
        all_platforms = []
        for _, platforms in self.platforms.items():
            for _, platform in platforms.items():
                all_platforms.append(platform)

        while len(all_platforms) > 0:
            p = all_platforms.pop(0)
            del p
