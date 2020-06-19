class Line():
    def __init__(self, network, name, w_lines):
        self.network = network
        self.name = name
        self.stations = {}
        
        w_in = w_lines.at[name, 'WEIGHT_IN']
        w_out = w_lines.at[name, 'WEIGHT_OUT']
        self.weight = (w_in, w_out)
    
    def init_line(self, stations):
        self.stations = stations
    
    def get_name(self):
        return self.name

    def get_weight(self):
        return self.weight
    
    def is_closed(self):
        """If the line does not admit more passengers, this function returns True"""
        closed = True
        for _, s in self.stations.items():
            closed = closed and s.is_closed()
        return closed
    
    def allow_passengers(self):
        allow_in_stations = False
        for _, s in self.stations.items():
            allow_in_stations = allow_in_stations or s.allow_passengers()
        return allow_in_stations
    
    def get_stations(self):
        return self.stations

    def get_n_infections(self):
        n_infections = 0
        for _, s in self.stations.items():
            n_infections = n_infections + s.get_n_infections()
        return n_infections

    def reset(self):
        for _, s in self.stations.items():
            s.reset()
