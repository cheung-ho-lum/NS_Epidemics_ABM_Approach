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
        # Adds exposure to a node.
        # Exposure is equivalent to I in terms of its eventual effect.
        # There is exposure from the same station
        # some base 'wait time' at the same platform + the distance that they travel together (commute time)
        # There is some exposure from stations on the same route
        # + the distance that they travel together (commute time, distance between stations)
        # And there is (NO) general exposure from the number of total infected commuters
        total_exposure = 0
        infected_count = 0

        subway_map = self.model.subway_graph.graph
        current_node = subway_map.nodes[self.location]
        commute_time = current_node['commute_time']
        commuter_ratio = current_node['commuter_ratio']
        num_infected = self._population[AgentParams.STATUS_INFECTED]
        # Same station
        # On second thought... let's not double-count same-station exposure
        #total_exposure += num_infected * commuter_ratio * commute_time #TODO: commute time should be some fraction of day
        infected_count += num_infected

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
            distance_to_costation = nx.algorithms.shortest_path_length(subway_map, self.location, station)
            costation_commute_time = subway_map.nodes[station]['commute_time']
            costation_infected = subway_map.nodes[station]['infected']
            costation_commuter_ratio = subway_map.nodes[station]['commuter_ratio']

            # TODO: ok 2 stations on opposite ends of the line will expose each other a lot. fix this.
            # Why not just calculate the shared commute time of each node pair?
            if distance_to_costation < 10:
                shared_commute = min(costation_commute_time, commute_time) / max(costation_commute_time, commute_time)
            else:
                shared_commute = 0
            total_exposure += costation_infected * costation_commuter_ratio * shared_commute
            infected_count += costation_infected

        # General Exposure
        total_infected = self.model.calculate_SEIR()[2]
        other_infected = total_infected - infected_count
        total_exposure += other_infected * 0.30 * 0.00001  # average commuter ratio and a very small shared commute
        #TODO: hmm... this is not adjusted by reduced ridership countermeasure.

        current_node['exposure'] = total_exposure * 100

        return None


    def update_agent_health(self):
        # *HLC 30.06.20 - Simplifying this to the following:
        # We'll only have 1 countermeasure for now. ISOLATION.
        ## ISOLATION - Kicks in linearly over a week:
        ### Lowers general contact rate by... 50%?
        ### Increases removal rate by 250% (2 day average after not feeling well)
        ### Lowers commuter ratio by 90% (reflects subway shutdown)
        # We'll still let the super-class handle regular fully mixing SEIR
        # This class will add exposure from the outside to susceptible commuters based on viral load
        # This class will hold off on gloabl mixing (~0.3) until later.
        exposure = self.model.subway_graph.graph.nodes[self._location]['exposure']
        beta = AgentParams.DEFAULT_BETA  # Eventually, we should reference node beta
        gamma = AgentParams.DEFAULT_GAMMA
        commuter_ratio = self.model.subway_graph.graph.nodes[self._location]['commuter_ratio']

        if EnvParams.ISOLATION_COUNTERMEASURE in self.model.countermeasures.keys():
            elapsed_time = self.model.schedule.time - self.model.countermeasures[EnvParams.ISOLATION_COUNTERMEASURE]
            beta -= beta * 0.6 * (min(1, elapsed_time / 7))
            gamma += gamma * 4.0 * (min(1, elapsed_time / 7))
            commuter_ratio -= commuter_ratio * 0.9 * (min(1, elapsed_time / 7))

        self._epi_characteristics['beta'] = beta  # And yet more random params from me
        self._epi_characteristics['gamma'] = gamma
        self._epi_characteristics['commuter_ratio'] = commuter_ratio

        susceptible = self.population[AgentParams.STATUS_SUSCEPTIBLE]
        seir_numbers = self.model.calculate_SEIR()
        normalization_factor = sum(seir_numbers)

        # Subway rider spread
        susceptible_commuters = susceptible * commuter_ratio

        self.population[AgentParams.STATUS_SUSCEPTIBLE] -= susceptible_commuters * beta * exposure / normalization_factor
        self.population[AgentParams.STATUS_EXPOSED] += susceptible_commuters * beta * exposure / normalization_factor

        # Global spread TODO: NOT USED!
        # Really if this didn't have a commute time factor, then it would mean spread OUTSIDE of the subway system.

        super().update_agent_health()
        if DisplayParams.PRINT_DEBUG:
            if self.location == AgentParams.MAP_LOCATION_98_BEACH \
                    or self.location == AgentParams.MAP_LOCATION_55_ST \
                    or self.location == AgentParams.MAP_LOCATION_JUNCTION_BLVD:
                print(self.location, self.population,
                      susceptible_commuters * beta * exposure / normalization_factor,
                      self._epi_characteristics['beta'])

    def step(self):
        self.move()
        self.update_agent_health()
