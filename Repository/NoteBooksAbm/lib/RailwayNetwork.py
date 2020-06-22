import datetime
import random
from decimal import Decimal as D
from decimal import ROUND_DOWN
from mesa import Model
from mesa.time import SimultaneousActivation
from .Passenger import Passenger
from .Train import Train

class RailwayNetwork(Model):
    def __init__(self,
                 n_passengers,
                 open_time,
                 close_time,
                 w_times,
                 w_lines,
                 w_stations,
                 timetable,
                 connections,
                 n_initial_infected=0,
                 infection_p=0,
                 auto_reset=True):

        # Arguments
        self.n_passengers = n_passengers
        self.open_time = open_time
        self.close_time = close_time
        self.w_times = w_times
        self.w_lines = w_lines
        self.w_stations = w_stations
        self.timetable = timetable
        self.connections = connections
        self.n_initial_infected = n_initial_infected
        self.infection_p = infection_p
        self.auto_reset = auto_reset
        
        # Initialize vars
        self.lines = {}
        self.stations = {}
        self.trains = []
        self.passengers = []
        self.initial_state = True
        
        # Simulate the simultaneous activation of all the agents
        self.schedule_passengers = SimultaneousActivation(self)
        self.schedule_trains = SimultaneousActivation(self)

        # Create passengers
        for i in range(self.n_passengers):
            p = Passenger(i, self, self)
            self.passengers.append(p)
            self.schedule_passengers.add(p)
        
        # Create trains
        routes = timetable.reset_index(level=['LINE', 'STATION_NAME'])
        route_ids = routes['ID'].unique().tolist()
        for route_id in route_ids:
            train_id = len(self.trains)
            train_route = routes.loc[(routes['ID'] == route_id)]
            train = Train(train_id, self, self, train_route)
            self.trains.append(train)
            self.schedule_trains.add(train)
        
        # Initialize vars
        self.reset()
    
    def init_network(self, lines, stations, debug=False):
        self.lines = lines
        self.stations = stations
        
        # Build dictionaries:
        # - Next station to each one depending on the direction
        # - Lines which are in a station
        # - Stations which are in a line
        stations_in_line = {line_name:{} for line_name, line in lines.items()}
        lines_in_station = {st_name:{} for st_name, station in stations.items()}
        stations_connections = {st_name:{} for st_name, station in stations.items()}
        
        debug_i = 0
        for st_name, station in stations.items():
            if debug:
                debug_i = debug_i + 1
                print('\rBuilding dictionary of %s (%d of %d)' % (st_name, debug_i, len(stations)), ' '*20, end='')
            
            lines_in_station[st_name] = {}
            
            g_connections = self.connections.reset_index()
            station_connections = g_connections.loc[(g_connections['FROM_STATION'] == st_name)]
            next_stations = {}
            for i, row in station_connections.iterrows():
                d = row['DIRECTION']
                line_name = row['LINE']
                to_station = row['TO_STATION']
                
                lines_in_station[st_name][line_name] = self.get_lines()[line_name]
                stations_in_line[line_name][st_name] = self.get_stations()[to_station]
                
                if line_name not in next_stations:
                    next_stations[line_name] = {}
                if d not in next_stations[line_name]:
                    next_stations[line_name][d] = {}
                next_stations[line_name][d][to_station] = self.get_stations()[to_station]
            
            stations_connections[st_name] = next_stations
        
        # Finish set-up of stations and lines
        debug_i = 0
        for line_name, line in lines.items():
            if debug:
                debug_i = debug_i + 1
                print('\rInit line %s (%d of %d)' % (line_name, debug_i, len(lines)), ' '*20, end='')
            line.init_line(stations_in_line[line_name])
        
        for st_name, station in stations.items():
            station.init_connections(stations_connections[st_name])
            
        debug_i = 0
        for st_name, station in stations.items():
            if debug:
                debug_i = debug_i + 1
                print('\rInit station %s (%d of %d)' % (st_name, debug_i, len(stations)), ' '*20, end='')
            station.init_station(self.timetable, lines_in_station[st_name])
        
        if debug:
            print('\rNetwork is ready!', ' '*30)
    
    def is_closed(self):
        """Checks if the network is closed"""
        if self.close_time is None:
            return False
        
        time = self.get_time()
        if self.open_time < self.close_time:
            return time < self.open_time or time >= self.close_time
        else:
            return time < self.open_time and time >= self.close_time
    
    def get_time(self):
        return self.timer
    
    def get_stations(self):
        return self.stations
    
    def get_lines(self):
        return self.lines
    
    def get_passengers(self, status=None):
        if status is None:
            return self.passengers
        else:
            return [p for p in self.passengers if p.get_status() == status]
    
    def get_trains(self):
        return self.trains
    
    def get_open_close_times(self, line_name=None, station_name=None, direction=None):
        open_time = None
        close_time = None
        
        specific_time = line_name is not None or station_name is not None or direction is not None
        
        if self.open_time is not None and self.close_time is not None and specific_time:
            through_midnight = self.close_time < self.open_time
            
            _, time_ref = self.get_open_close_times()
            
            g_timetable = self.timetable.reset_index(level=['LINE', 'STATION_NAME'])
            
            conditions = (g_timetable['IS_END'] != 1)
            if line_name is not None:
                conditions = conditions & (g_timetable['LINE'] == line_name)
            if station_name is not None:
                conditions = conditions & (g_timetable['STATION_NAME'] == station_name)
            if direction is not None:
                conditions = conditions & (g_timetable['DIRECTION'] == direction)
            
            raw_open_times = g_timetable.loc[conditions]['ARRIVAL_TIME'].tolist()
            raw_close_times = g_timetable.loc[conditions]['DEPARTURE_TIME'].tolist()
            
            for raw_open_time in raw_open_times:
                if (open_time is None or open_time > raw_open_time) and raw_open_time > self.open_time:
                    open_time = raw_open_time
            
            for raw_close_time in raw_close_times:
                # To make comparisons with the close time, we must take into account the midnight
                if through_midnight:
                    if close_time is None:
                        close_time = raw_close_time
                    elif time_ref is not None and raw_close_time < time_ref and close_time < time_ref and raw_close_time > close_time:
                        close_time = raw_close_time
                    elif time_ref is not None and raw_close_time > time_ref and close_time > time_ref and raw_close_time > close_time:
                        close_time = raw_close_time
                    elif time_ref is not None and raw_close_time < time_ref and close_time > time_ref:
                        close_time = raw_close_time
                else:
                    if close_time is None or close_time < raw_close_time:
                        close_time = raw_close_time
            
            return open_time, close_time
        else:
            return self.open_time, self.close_time
    
    def step(self):
        """Advance the model by one step"""
        self.step_minute()
        
        if self.is_closed():
            if self.auto_reset:
                self.reset()
                self.initial_state = True
        else:
            self.initial_state = False
            self.step_in_passengers()

            self.schedule_passengers.step()
            self.schedule_trains.step()
    
    def step_minute(self):
        """Add one minute to the current time"""
        self.k_minute = self.k_minute + 1
        self.k_minute = self.k_minute if self.k_minute < 1440 else 0
        
        delta = datetime.timedelta(minutes=self.k_minute)
        
        self.timer = (self.time_ref + delta).time()
        return self
    
    def step_in_passengers(self):
        # Compute the number of IN passengers (depending on the current time)
        in_passengers = self.n_passengers * self.w_times.at[self.timer, 'WEIGHT_IN'] + self.in_residual
        self.in_residual = in_passengers - in_passengers.quantize(D('1.'), rounding=ROUND_DOWN)
        in_passengers = in_passengers.quantize(D('1.'), rounding=ROUND_DOWN)
        
        # Get some random passengers and change their status
        passengers = random.sample(self.get_passengers(status=0), int(in_passengers))
        n_passengers = len(passengers)
        
        # Assing a specific number of passengers to a station
        stations = [s for s in list(self.stations.values()) if s.allow_passengers()]
        if len(stations) == 0:
            return
        
        weights = [float(s.get_weight(time=self.timer)[0]) for s in stations]
        p_random = random.choices(stations, weights=weights, k=n_passengers)
        
        for i in range(n_passengers):
            p_random[i].add_passengers([passengers[i]])
            passengers[i].set_status(1).set_origin(p_random[i])

    def notify_arrived_passengers(self, station, passengers):
        for p in passengers:
            p.set_status(2)
            p.set_destination(station)
            p.set_current_place(None)
    
    def notify_finish_route(self, train):
        pass
    
    def reset(self):
        # Init timer
        if self.open_time is not None:
            self.time_ref = datetime.datetime(100, 1, 1, self.open_time.hour, self.open_time.minute, 0)
        else:
            self.time_ref = datetime.datetime(100, 1, 1, 5, 0, 0) # 5:00h
        self.timer = self.time_ref.time()
        self.k_minute = 0
        
        # Reset objects
        for t in self.trains:
            t.reset()
        for p in self.passengers:
            p.reset()
        for _, l in self.lines.items():
            l.reset()

        self.in_residual = D(0)

        # Infect some initial passengers
        self.infection_simulation = self.n_initial_infected > 0 and self.infection_p > 0
        for i in range(self.n_initial_infected):
            self.passengers[i].set_infected_status(2).set_infection_p(self.infection_p)

    def __del__(self):
        del self.passengers[:]
        del self.trains[:]
        del self.stations
        del self.lines
