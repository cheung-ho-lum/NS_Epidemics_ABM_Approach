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
        #Infects routes based on how many commuters and infected commuters there are.
        subway_map_wrapper = self.model.subway_graph
        subway_map = subway_map_wrapper.graph
        routes = subway_map.nodes[self.location]['routes']

        commuter_ratio = subway_map.nodes[self.location]['commuter_ratio']
        # TODO: This copy pasta is here because I don't save off a default commuter ratio
        if EnvParams.ISOLATION_COUNTERMEASURE in self.model.countermeasures.keys():
            elapsed_time = self.model.schedule.time - self.model.countermeasures[EnvParams.ISOLATION_COUNTERMEASURE]
            commuter_ratio -= commuter_ratio * 0.9 * (min(1, elapsed_time / 7))

        num_commuters = sum(self._population.values()) * commuter_ratio
        num_infected_commuters = self._population[AgentParams.STATUS_INFECTED] * commuter_ratio
        num_routes = len(routes)

        for route in routes:
            subway_map_wrapper.commuters_by_route_dict[route] += num_commuters / num_routes
            subway_map_wrapper.infected_by_route_dict[route] += num_infected_commuters / num_routes

        # Old code based on individual station exposure.
        # for station in subway_map.nodes():
        #     if station != self.location:
        #         shared_commute = self.model.subway_graph.calculate_commute_similarity(self._location, station)
        #
        #         subway_map.nodes[station]['exposure'] += \
        #             number_of_infected_commuters * shared_commute * AgentParams.CONTACT_MODIFIER

        return None


    def update_agent_health(self):
        # *HLC 30.06.20 - Simplifying this to the following:
        # We'll only have 1 countermeasure for now. ISOLATION.
        ## ISOLATION - Kicks in linearly over a week:
        ### Lowers commuter ratio by 90% (reflects subway shutdown)
        # We'll still let the super-class handle regular fully mixing SEIR
        # This class will add exposure from the outside to susceptible commuters based on viral load
        # Finally, this is calculated here and not at the model level because... well, adjustments originally made
        # Based on location.

        beta = AgentParams.DEFAULT_BETA  # Eventually, we should reference node beta
        gamma = AgentParams.DEFAULT_GAMMA
        subway_map_wrapper = self.model.subway_graph
        current_node = subway_map_wrapper.graph.nodes[self._location]
        commuter_ratio = current_node['commuter_ratio']
        commute_time = current_node['commute_time']
        routes = current_node['routes']

        # A quick experiment turning off exposure in 10003
        # if self.location in [15, 16, 17, 18, 20, 117, 118, 406, 407, 413, 414]:
        #    exposure = 0

        if EnvParams.ISOLATION_COUNTERMEASURE in self.model.countermeasures.keys():
            elapsed_time = self.model.schedule.time - self.model.countermeasures[EnvParams.ISOLATION_COUNTERMEASURE]
            emergency_reduction = AgentParams.INITIAL_REDUCTION_TGT
            emergency_time = AgentParams.INITIAL_REDUCTION_TIME
            full_reduction = AgentParams.FULL_REDUCTION_TGT
            full_time = AgentParams.FULL_REDUCTION_TIME

            #distribute reductions evenly between beta and gamma
            if elapsed_time <= emergency_time:
                actual_r0 = emergency_reduction + \
                            (beta / gamma - emergency_reduction) * (emergency_time - elapsed_time) / emergency_time
            else:
                actual_r0 = full_reduction + \
                            (emergency_reduction - full_reduction) * \
                            max(0, (full_time - emergency_time - elapsed_time)) / \
                            (full_time - emergency_time)

            reduction_ratio = actual_r0 / (beta/gamma)
            beta *= math.sqrt(reduction_ratio)
            gamma /= math.sqrt(reduction_ratio)

            commuter_ratio -= commuter_ratio * 0.9 * (min(1, elapsed_time / 7))  # 90% drop in commuters

        self._epi_characteristics['beta'] = beta
        self._epi_characteristics['gamma'] = gamma

        # Subway rider spread
        susceptible = self.population[AgentParams.STATUS_SUSCEPTIBLE]
        susceptible_commuters = susceptible * commuter_ratio

        num_routes = len(routes)
        total_rate = 0
        for route in routes:
            infected = subway_map_wrapper.infected_by_route_dict[route]
            total = subway_map_wrapper.commuters_by_route_dict[route]
            average_contact_rate = infected/total
            total_rate += average_contact_rate

        weighted_contact_rate = total_rate / num_routes

        exposure_mu = AgentParams.CONTACT_MODIFIER * weighted_contact_rate * commute_time


        self.population[AgentParams.STATUS_SUSCEPTIBLE] -= susceptible_commuters * exposure_mu
        self.population[AgentParams.STATUS_EXPOSED] += susceptible_commuters * exposure_mu


        super().update_agent_health()
        if DisplayParams.PRINT_DEBUG:
            if self.location in [21, 105, 106, 170, 171, 172, 331, 411]: #AgentParams.MAP_LOCATION_98_BEACH \
                    #or self.location == AgentParams.MAP_LOCATION_55_ST \
                    #or self.location == AgentParams.MAP_LOCATION_JUNCTION_BLVD: \
                    #or 50 <= self.location <= 55:
                r_0 = "{:.2f}".format(beta/gamma)
                print(self.location, self.population, exposure_mu, susceptible_commuters, susceptible_commuters * exposure_mu, r_0)

    def step(self):
        self.move()
        self.update_agent_health()
