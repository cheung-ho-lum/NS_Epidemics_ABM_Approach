"""
Configure visualization elements and instantiate a server
"""

from .model import CovidABMModel, CovidABMAgent  # noqa

from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, ChartModule


def circle_portrayal_example(agent):
    if agent is None:
        return

    portrayal = {
        "Shape": "circle",
        "Filled": "true",
        "Layer": 0,
        "r": 0.5,
        "Color": "Pink",
    }
    return portrayal


canvas_element = CanvasGrid(circle_portrayal_example, 20, 20, 500, 500)
chart_element = ChartModule([{"Label": "CovidABM", "Color": "Pink"}])

model_kwargs = {"num_agents": 10, "width": 10, "height": 10}

server = ModularServer(
    CovidABMModel,
    [canvas_element, chart_element],
    "CovidABM",
    model_kwargs,
)
