import math
import os
from random import randrange

import networkx as nx
import pandas as pd
from mesa import Agent, Model
from mesa.datacollection import DataCollector
from mesa.space import NetworkGrid
from mesa.time import RandomActivation

from .agent import Passenger, Hub
from .utils import State, number_state, number_infected, number_susceptible, number_eradicated


folder_path = os.path.dirname(os.getcwd())


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
        self.number_daily_passengers=number_daily_passengers

        # change how data is being collected
        
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
