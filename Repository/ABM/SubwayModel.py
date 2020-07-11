from ABM.SubwayAgent import SubwayAgent
from mesa.time import RandomActivation
from ABM.SubwayGraph import SubwayGraph
from Parameters import AgentParams, EnvParams
import networkx as nx
from ABM.TransportationModel import TransportationModel
from datetime import datetime

class SubwayModel(TransportationModel):
    """This guy's constructor should probably have a few more params."""
    def __init__(self, subway_map, routing_dict):
        self._subway_graph = SubwayGraph(subway_map, routing_dict)
        self._agent_loc_dictionary = {}  # a dictionary of locations with lists of agents at each location
        self._zip_to_station_dictionary = {}
        self.countermeasures = {}
        self.schedule = RandomActivation(self)
        # Create agents
        agent_id = 0
        for loc in list(self.subway_graph.graph.nodes()):
            # Add Agents
            agent_id += 1  # we will keep agent ids different from location for now.
            population = subway_map.nodes[loc]['population']
            a = SubwayAgent(agent_id, self, loc, population)
            starting_infected_percentage = AgentParams.STARTING_PERCENTAGE
            starting_exposed_percentage = AgentParams.STARTING_PERCENTAGE * AgentParams.STARTING_RATIO
            # TODO: we'll omit considering start locations for now
            if loc == AgentParams.MAP_LOCATION_JUNCTION_BLVD \
                    or loc == AgentParams.MAP_LOCATION_55_ST \
                    or loc == AgentParams.MAP_LOCATION_98_BEACH:
                a.population[AgentParams.STATUS_EXPOSED] += population * starting_exposed_percentage
                a.population[AgentParams.STATUS_INFECTED] += population * starting_infected_percentage
                a.population[AgentParams.STATUS_RECOVERED] += 0
                a.population[AgentParams.STATUS_SUSCEPTIBLE] -= \
                    population * (starting_exposed_percentage + starting_infected_percentage)

            elif loc == AgentParams.MAP_LOCATION_COLMENAR_VIEJO:
                a.population[AgentParams.STATUS_EXPOSED] += population * starting_exposed_percentage
                a.population[AgentParams.STATUS_INFECTED] += population * starting_infected_percentage
                a.population[AgentParams.STATUS_RECOVERED] += 0
                a.population[AgentParams.STATUS_SUSCEPTIBLE] -= \
                    population * (starting_exposed_percentage + starting_infected_percentage)

            else:
                a.population[AgentParams.STATUS_EXPOSED] += population * starting_exposed_percentage
                a.population[AgentParams.STATUS_INFECTED] += population * starting_infected_percentage
                a.population[AgentParams.STATUS_RECOVERED] += 0
                a.population[AgentParams.STATUS_SUSCEPTIBLE] -= \
                    population * (starting_exposed_percentage + starting_infected_percentage)

            self.schedule.add(a)

            # Fill Zip-to-station dictionary
            station_zip = subway_map.nodes[loc]['zip']
            self.zip_to_station_dictionary.setdefault(station_zip, []).append(loc)

        # Prints zips and corresponding stations
        #for key in self.zip_to_station_dictionary:
        #    print(key, self.zip_to_station_dictionary[key])


    # Decay the viral loads in the environment. just wipes them for now.
    def decay_viral_loads(self):
        for a in self.schedule.agents:
            self.subway_graph.graph.nodes[a.location]['infected'] = a.population[AgentParams.STATUS_INFECTED]
        nx.set_node_attributes(self.subway_graph.graph, 0, 'exposure')
        for route in self.subway_graph.commuters_by_route_dict:
            self.subway_graph.commuters_by_route_dict[route] = 0
            self.subway_graph.infected_by_route_dict[route] = 0
        return None

    def increment_viral_loads(self):
        for a in self.schedule.agents:
            a.infect()  # Really, the model could do all this itself, but calling agents keeps with ABM philosophy
        return None

    def step(self):
        self.decay_viral_loads() #TODO: yes, this belongs at the end of a step. but i need my snapshot to be mid-day
        #print('increment_start', datetime.now())
        self.increment_viral_loads()
        #print('step_start', datetime.now())
        self.schedule.step()
        self.subway_graph.update_hotspots(self.schedule.agents) #TODO: repair this later
        self.update_countermeasures()
        #print('step_end', datetime.now())

    def update_countermeasures(self):
        active = self.countermeasures
        infected = 0
        for a in self.schedule.agents:
            infected += a.population[AgentParams.STATUS_INFECTED]
        if EnvParams.ISOLATION_COUNTERMEASURE not in active.keys():
            if infected >= EnvParams.ISOLATION_COUNTERMEASURE_START:
                active[EnvParams.ISOLATION_COUNTERMEASURE] = self.schedule.time
                print('isolation countermeasure taken!')
        # if EnvParams.RECOMMENDATION_COUNTERMEASURE not in active.keys():
        #     if infected >= 500:
        #         active[EnvParams.RECOMMENDATION_COUNTERMEASURE] = self.schedule.time
        #         print('recommendation countermeasure taken!')
        # if EnvParams.AWARENESS_COUNTERMEASURE not in active.keys():
        #     if infected >= 500:  # start awareness campaign
        #         active[EnvParams.AWARENESS_COUNTERMEASURE] = self.schedule.time
        #         print('awareness countermeasure taken!')


    def calculate_SEIR(self, print_results=False):
        sick, exposed, infected, recovered = 0, 0, 0, 0
        for a in self.schedule.agents:
            sick += a.population[AgentParams.STATUS_SUSCEPTIBLE]
            exposed += a.population[AgentParams.STATUS_EXPOSED]
            infected += a.population[AgentParams.STATUS_INFECTED]
            recovered += a.population[AgentParams.STATUS_RECOVERED]
        if print_results:
            print('S,E,I,R:', sick, exposed, infected, recovered)
        return [sick, exposed, infected, recovered]


    def calculate_modzcta_case_rate(self, case_rates_dict, iteration):
        #for now this calculates cumulative case rate by modzcta and returns a dictionary of those values
        #TODO: per usual we're totally ignoring that multiple stations are in one zip.
        cases_by_zip = {}
        population_by_zip = {}
        # Calculate case rate by zip
        for a in self.schedule.agents:
            loc = a.location
            loc_case_numbers = a.population[AgentParams.STATUS_INFECTED] + a.population[AgentParams.STATUS_RECOVERED]
            loc_population = sum(a.population.values())
            station_zip = self.subway_graph.graph.nodes[loc]['zip']

            cases_by_zip.setdefault(station_zip, 0)
            cases_by_zip[station_zip] += loc_case_numbers
            #TODO: why are you always recalculating population_by_zip among other things.
            population_by_zip.setdefault(station_zip, 0)
            population_by_zip[station_zip] += loc_population

        # Add to main dictionary
        for station_zip in cases_by_zip:
            case_rate = cases_by_zip[station_zip] / population_by_zip[station_zip]
            #on iteration 1, it is ok to add if <= 1 entries
            if station_zip in case_rates_dict.keys():
                if len(case_rates_dict[station_zip]) <= iteration:
                    case_rates_dict[station_zip].append(case_rate)
            else:
                case_rates_dict[station_zip] = [case_rate]

        return case_rates_dict

    @property
    def subway_graph(self):
        return self._subway_graph

    @subway_graph.setter
    def subway_graph(self, value):
        self._subway_graph = value

    # TODO: I think this might actually be better at the graph level.
    @property
    def zip_to_station_dictionary(self):
        return self._zip_to_station_dictionary

    @zip_to_station_dictionary.setter
    def zip_to_station_dictionary(self, value):
        self._zip_to_station_dictionary = value

