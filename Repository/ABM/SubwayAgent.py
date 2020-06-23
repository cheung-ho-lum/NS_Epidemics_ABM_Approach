import math

import networkx as nx

from ABM.SEIR_Agent import SEIR_Agent
from Parameters import AgentParams, DisplayParams
from Parameters import EnvParams
PRINT_DEBUG = False


class SubwayAgent(SEIR_Agent):
    """This guy's constructor should probably have a few more params"""
    def __init__(self, unique_id, model, location=-1, population=0, epi_characteristics=None):
        super().__init__(unique_id, model, location, population, epi_characteristics)

    def infect(self):
        # Commuters infect their location by bringing extra "viral load" (exposure) home.
        # There is high exposure from other commuters who use this station
        ## + the distance that they travel together (commute time)
        # There is some exposure from stations on the same route
        ## + the distance that they travel together (commute time, distance between stations)
        # And there is general exposure from the number of total infected commuters
        total_exposure = 0

        subway_map = self.model.subway_graph.graph
        current_node = subway_map.nodes[self.location]
        commute_time = current_node['commute_time']
        num_infected = self._population[AgentParams.STATUS_INFECTED]
        # Same station
        total_exposure += 10 * num_infected * commute_time

        # Same route (find stations)
        routes_affected = current_node['routes']
        stations_affected = []  # TODO: this should be a set. but I forgot how make set ops
        for route in routes_affected:
            stations_on_route = self.model.subway_graph.routing_dict[route]
            for station in stations_on_route:
                if station not in stations_affected and station != self.location:
                    stations_affected.append(station)

        # Same route (find number of infected)
        for station in stations_affected:
            distance_from_origin = nx.algorithms.shortest_path_length(subway_map, self.location, station)
            costation_commute_time = subway_map.nodes[station]['commute_time']
            costation_infected = subway_map.nodes[station]['infected']
            geometric_mean = math.sqrt(costation_commute_time * commute_time)
            additional_exposure = geometric_mean / distance_from_origin
            additional_exposure *= additional_exposure
            total_exposure += 200 * additional_exposure * costation_infected

        # General Exposure
        total_exposure += 10 * commute_time

        current_node['viral_load'] = total_exposure

        return None

    def update_agent_health(self):
        viral_load = self.model.subway_graph.graph.nodes[self._location]['viral_load']
        beta = AgentParams.DEFAULT_BETA  # Eventually, we should reference node beta
        gamma = AgentParams.DEFAULT_GAMMA

        #Modify beta based on subway ridership
        beta_subway_commuters = min(8, beta + viral_load / 1e6) #limit beta to 8 from princess cruise number
        subway_map = self.model.subway_graph.graph
        commuter_ratio = subway_map.nodes[self.location]['commuter_ratio']
        weighted_beta = beta * (1 - commuter_ratio) + beta_subway_commuters * commuter_ratio

        #Modify beta based on citywide measures
        #infected used temporarily to model non-compliance or self initiative
        infected_percent = self.population[AgentParams.STATUS_INFECTED] / sum(self.population.values())
        if EnvParams.ISOLATION_COUNTERMEASURE in self.model.countermeasures.keys() and infected_percent > 0.001 \
                or infected_percent > 0.01:
            self._epi_characteristics['beta'] = weighted_beta / 4  # People are infected slower
            self._epi_characteristics['gamma'] = gamma * 2  # People are found faster
        elif EnvParams.RECOMMENDATION_COUNTERMEASURE in self.model.countermeasures.keys() and infected_percent > 0.0001 \
                or infected_percent > 0.001:
            self._epi_characteristics['beta'] = weighted_beta / 1.5  # People are infected slower
            self._epi_characteristics['gamma'] = gamma * 1.5  # People are found faster
        else:
            self._epi_characteristics['beta'] = weighted_beta
            self._epi_characteristics['gamma'] = gamma

        awareness_modifier = 1
        if EnvParams.AWARENESS_COUNTERMEASURE in self.model.countermeasures.keys():
            elapsed_time = self.model.schedule.time - self.model.countermeasures[EnvParams.AWARENESS_COUNTERMEASURE]
            """ (1/(1+exp(-kx))^a """
            param_k = 0.16  # Bigger = faster, shallower?
            param_a = 1.5  # Smaller = more shallow
            param_cap = 0.77
            awareness_modifier = 1 - param_cap * pow((1 / (1 + math.exp(- param_k * elapsed_time))), param_a)
            # print(elapsed_time, awareness_modifier)
            self._epi_characteristics['beta'] *= awareness_modifier  # And yet more random params from me

        susceptible = self.population[AgentParams.STATUS_SUSCEPTIBLE]
        SEIR_numbers = self.model.calculate_SEIR()
        outside_infected = SEIR_numbers[2] - self.population[AgentParams.STATUS_INFECTED]
        normalization_factor = sum(SEIR_numbers)

        # Subway rider spread
        susceptible_commuters = susceptible * commuter_ratio
        beta_subway_commuters *= awareness_modifier
        self.population[AgentParams.STATUS_SUSCEPTIBLE] -= awareness_modifier * \
            susceptible_commuters * beta_subway_commuters * outside_infected / normalization_factor
        self.population[AgentParams.STATUS_EXPOSED] += awareness_modifier * \
            susceptible_commuters * beta_subway_commuters * outside_infected / normalization_factor

        # Global spread TODO: this currently just acts as beta * 1.7 modifier
        self.population[AgentParams.STATUS_SUSCEPTIBLE] -= AgentParams.GLOBAL_FACTOR_NYC_SUBWAY * \
            self._epi_characteristics['beta'] * susceptible * outside_infected / normalization_factor
        self.population[AgentParams.STATUS_EXPOSED] += AgentParams.GLOBAL_FACTOR_NYC_SUBWAY * \
            self._epi_characteristics['beta'] * susceptible * outside_infected / normalization_factor

        super().update_agent_health()
        if DisplayParams.PRINT_DEBUG:
            if self.location == AgentParams.MAP_LOCATION_98_BEACH \
                    or self.location == AgentParams.MAP_LOCATION_55_ST \
                    or self.location == AgentParams.MAP_LOCATION_JUNCTION_BLVD:
                print(self.location, self.population, beta_subway_commuters,  self._epi_characteristics['beta'], awareness_modifier)

    def step(self):
        self.move()
        self.update_agent_health()
