import math

from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule, NetworkModule, TextElement
from mesa.visualization.UserParam import UserSettableParameter

from .model import State, VirusOnNetwork, number_infected, number_infected_passengers, number_of_passengers
from .agent import Passenger


def network_portrayal(G):
    # The model ensures there is always 1 agent per node

    def node_color(agent):
        return {State.INFECTED: "#FF0000", State.SUSCEPTIBLE: "#008000"}.get(
            agent.state, "#808080"
        )

    def edge_color(agent1, agent2):
        if State.ERADICATED in (agent1.state, agent2.state):
            return "#000000"
        return "#e8e8e8"

    def edge_width(agent1, agent2):
        if State.ERADICATED in (agent1.state, agent2.state):
            return 3
        return 2

    def get_agents(source, target):
        return G.nodes[source]["agent"][0], G.nodes[target]["agent"][0]

    def get_node_size(agents):
        size = 6
        for agent in agents:
            if type(agent) == Passenger:
                size += 1 / 250000
        return size

    portrayal = dict()
    portrayal["nodes"] = [
        {
            "size": get_node_size(agents),
            "color": node_color(agents[0]),
            "tooltip": "id: {}<br>state: {}".format(
                agents[0].unique_id, agents[0].state.name
            ),
        }
        for (_, agents) in G.nodes.data("agent")
    ]

    portrayal["edges"] = [
        {
            "source": source,
            "target": target,
            "color": edge_color(*get_agents(source, target)),
            "width": edge_width(*get_agents(source, target)),
        }
        for (source, target) in G.edges
    ]

    return portrayal


network = NetworkModule(network_portrayal, 500, 500, library="d3")
chart = ChartModule(
    [
        {"Label": "Infected", "Color": "#FF0000"},
        {"Label": "Susceptible", "Color": "#008000"},
        {"Label": "Eradicated", "Color": "#808080"},
    ]
)


class MyTextElement(TextElement):
    def render(self, model):
        ratio = model.eradicated_susceptible_ratio()
        ratio_text = "&infin;" if ratio is math.inf else "{0:.2f}".format(ratio)
        infected_stations = str(number_infected(model))
        infected_passengers = str(number_infected_passengers(model))
        passengers = str(number_of_passengers(model))

        return "Eradicated/Susceptible Ratio: {}<br>Infected Stations: {} <br>Infected Passengers: {} <br>Total Number of Passengers: {}".format(
            ratio_text, infected_stations, infected_passengers, passengers   
        )


model_params = {
    "num_hubs": UserSettableParameter(
        "slider",
        "Number of hubs",
        194,
        2,
        194,
        2,
        description="Choose how many hubs to include in the model",
    ),
    "number_daily_passengers": UserSettableParameter(
        "slider",
        "Number of daily passengers",
        100,
        100,
        50000,
        100,
        description="Choose how many passengers use the transport netwrok",
    ),
}

server = ModularServer(
    VirusOnNetwork, [network, MyTextElement(), chart], "Virus Model", model_params
)
server.port = 8521
