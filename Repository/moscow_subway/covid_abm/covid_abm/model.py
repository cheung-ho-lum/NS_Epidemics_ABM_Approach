import math
import os
from enum import Enum
from random import randrange

import networkx as nx
import pandas as pd
from mesa import Agent, Model
from mesa.datacollection import DataCollector
from mesa.space import NetworkGrid
from mesa.time import RandomActivation

from .agent import Passenger


folder_path = os.path.dirname(os.getcwd())


class State(Enum):
    SUSCEPTIBLE = 0
    INFECTED = 1
    ERADICATED = 2


def number_infected_passengers(model, state='INFECTED'):
    return sum([1 for a in model.grid.get_all_cell_contents() if type(a) == Passenger and  a.state is state])

def number_of_passengers(model):
    return sum([1 for a in model.grid.get_all_cell_contents() if type(a) == Passenger])

def number_state(model, state):
    return sum([1 for a in model.grid.get_all_cell_contents() if a.state is state])


def number_infected(model):
    return number_state(model, State.INFECTED)


def number_susceptible(model):
    return number_state(model, State.SUSCEPTIBLE)


def number_eradicated(model):
    return number_state(model, State.ERADICATED)


class CustomNetworkGrid(NetworkGrid):
    def get_egde_data(self, node_a, node_b):
        return self.G.get_edge_data(node_a, node_b, default=0)


number_daily_passengers = 100


class VirusOnNetwork(Model):
    """A virus model with some number of agents"""

    def __init__(
        self,
        num_hubs=194,
        initial_outbreak_size=1,
        virus_spread_chance=0.4,  # to be computed by agent interactions (people)
        preventive_measures=0.4,
        minimiation_likelyhood=0.3,  # must depend on preventive measures
        eradication_likelyhood=0.5,  # must depend on preventive measures and eradication likelyhood
        number_daily_passengers=100,
    ):
        self._set_graph()
        self.grid = CustomNetworkGrid(self.G)
        self.schedule = RandomActivation(self)
        self.initial_outbreak_size = (
            initial_outbreak_size if initial_outbreak_size <= num_hubs else num_hubs
        )
        self.virus_spread_chance = virus_spread_chance
        self.preventive_measures = preventive_measures
        self.minimiation_likelyhood = minimiation_likelyhood
        self.eradication_likelyhood = eradication_likelyhood
        self.number_daily_passengers = number_daily_passengers

        self.datacollector = DataCollector(
            {
                "Infected": number_infected,
                "Susceptible": number_susceptible,
                "Eradicated": number_eradicated,
            }
        )

        # Create hub
        for i, node in enumerate(self.G.nodes()):
            a = Hub(
                i,
                self,
                State.SUSCEPTIBLE,
                self.virus_spread_chance,
                self.preventive_measures,
                self.minimiation_likelyhood,
                self.eradication_likelyhood,
            )
            self.schedule.add(a)
            # Add the agent to the node
            self.grid.place_agent(a, node)

        # Infect some nodes
        infected_nodes = self.random.sample(self.G.nodes(), self.initial_outbreak_size)
        for a in self.grid.get_cell_list_contents(infected_nodes):
            a.state = State.INFECTED
            for i in range(self.initial_outbreak_size):
                passenger = Passenger(unique_id=i, model=self, initial_state='INFECTED', moore=False)
                self.grid.place_agent(passenger, a.unique_id)

        for i in range(self.number_daily_passengers-self.initial_outbreak_size):
            initial_state = 'SUSCEPTIBLE'
            passenger = Passenger(unique_id=i, model=self, initial_state=initial_state, moore=False)
            self.grid.place_agent(passenger, node)
            self.schedule.add(passenger)

        self.running = True
        self.datacollector.collect(self)

    def eradicated_susceptible_ratio(self):
        try:
            return number_state(self, State.ERADICATED) / number_state(
                self, State.SUSCEPTIBLE
            )
        except ZeroDivisionError:
            return math.inf

    # def number_infected_passengers(self):

    def step(self):
        self.schedule.step()
        # collect data
        self.datacollector.collect(self)

    def run_model(self, n):
        for i in range(n):
            self.step()

    def _set_graph(self, path_file=None):
        if not path_file:
            path_file = folder_path + "/covid_abm/data/routes_data.tsv"
        routes_df = pd.read_csv(path_file, sep="\t")
        self.G = nx.nx.from_pandas_edgelist(
            routes_df, "id_from", "id_to", ["delay", "station_from", "station_from"]
        )


class Hub(Agent):
    def __init__(
        self,
        unique_id,
        model,
        initial_state,
        virus_spread_chance,
        preventive_measures,
        minimiation_likelyhood,
        eradication_likelyhood,
    ):
        super().__init__(unique_id, model)

        self.state = initial_state

        self.virus_spread_chance = virus_spread_chance
        self.preventive_measures = preventive_measures
        self.minimiation_likelyhood = minimiation_likelyhood
        self.eradication_likelyhood = eradication_likelyhood

    def try_to_infect_neighbors(self):
        neighbors_nodes = self.model.grid.get_neighbors(self.pos, include_center=False)
        susceptible_neighbors = [
            agent
            for agent in self.model.grid.get_cell_list_contents(neighbors_nodes)
            if agent.state is State.SUSCEPTIBLE
        ]
        for a in susceptible_neighbors:
            if self.random.random() < self.virus_spread_chance:
                a.state = State.INFECTED

    def try_minimiation_likelyhood(self):
        if self.random.random() < self.minimiation_likelyhood:
            self.state = State.ERADICATED

    def try_remove_infection(self):
        # Try to remove
        if self.random.random() < self.eradication_likelyhood:
            # Success
            self.state = State.SUSCEPTIBLE
            self.try_minimiation_likelyhood()
        else:
            # Failed
            self.state = State.INFECTED

    def try_check_situation(self):
        if self.random.random() < self.preventive_measures:
            # Checking...
            if self.state is State.INFECTED:
                self.try_remove_infection()

    def step(self):
        if self.state is State.INFECTED:
            self.try_to_infect_neighbors()
        self.try_check_situation()
