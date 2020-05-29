import Preprocessing
import Parameters
from ABM import Agent
from ABM import Model
from ABM import OurGraph
from Parameters import SimulationParams
from itertools import count
import networkx as nx
from Parameters import SubwayParams
import matplotlib.pyplot as plt
import math
import numpy as np

# Stage 1:
# Just the map and people
# Create station map
# Add an above-ground node for people in the zip. These people don't interact (for now)
# Use MESA to make our Model
# Have people move around the subway
# End stage 1
# Stage 2:
# Introduce SEIR and add some numbers
# Introduce the NYC Subway map and add attributes
# Stage 3:

def draw_SEIR_curve(statistics):
    """It's questionable to keep statistics in a non-descript matrix because we might want more, but for now:
    rows = timestamp, cols(5) = t,S,E,I,R"""
    time_span = np.shape(statistics)[1] #should match run timespan

    fig = plt.figure(facecolor='w')
    ax = fig.add_subplot(111, facecolor='#dddddd', axisbelow=True)
    ax.plot(statistics[..., 0], statistics[..., 1], 'blue', alpha=0.5, lw=2, label='Susceptible')
    ax.plot(statistics[..., 0], statistics[..., 2], 'orange', alpha=0.5, lw=2, label='Exposed')
    ax.plot(statistics[..., 0], statistics[..., 3], 'red', alpha=0.5, lw=2, label='Infected')
    ax.plot(statistics[..., 0], statistics[..., 4], 'green', alpha=0.5, lw=2, label='Recovered')
    ax.set_xlabel('Time')
    ax.set_ylabel('Patients')
    ax.set_ylim(0, SimulationParams.TOTAL_POPULATION)
    ax.yaxis.set_tick_params(length=0)
    ax.xaxis.set_tick_params(length=0)
    ax.grid(b=True, which='major', c='w', lw=2, ls='-')
    legend = ax.legend()
    legend.get_frame().set_alpha(0.5)
    for spine in ('top', 'right', 'bottom', 'left'):
        ax.spines[spine].set_visible(False)
    plt.show()

G_subway_map = Preprocessing.get_subway_map('NYC')
G_full_map = G_subway_map #Preprocessing.make_exit_nodes(G_subway_map)
# Let's say that ticks are approximately 30 minutes.
# And that agents have a chance of infecting anyone between their source and destination while in subway
print('Num stations:', len(G_subway_map.nodes()))
print('Total order:', len(G_full_map.nodes()))
print('NCC:', nx.algorithms.components.number_connected_components(G_full_map)) #if this is >1, we have a problem
#cc_list = sorted(nx.connected_components(G_full_map), key=len, reverse=True) #largest first, for further debugging


model = Model.SEIR_Subway_Model(SimulationParams.TOTAL_POPULATION, G_full_map)

always_show_graph = False
show_every_2x = True
SEIR_Statistics = np.zeros(shape=(SimulationParams.RUN_SPAN + 1, 5)) #reminder: np is zero indexed
subway_map = model.our_graph
SEIR_Statistics[0, 0] = 0
print(model.calculate_SEIR(True))
SEIR_Statistics[0, 1:5] = model.calculate_SEIR(True)  #reminder: but ranges are exclusive or something.

for i in range(1, SimulationParams.RUN_SPAN + 1):
    print('TIME', i)
    SEIR_Statistics[i, 0] = i
    SEIR_Statistics[i, 1:5] = model.calculate_SEIR(True)
    model.step()
    subway_map = model.our_graph
    if i == 1:
        subway_map.draw_graph()
        plt.show()
    if always_show_graph or (math.log2(i).is_integer() and show_every_2x) or i == SimulationParams.RUN_SPAN:
        subway_map.update_hotspots(model.schedule.agents)
        subway_map.draw_graph('hotspot')
    plt.show()

draw_SEIR_curve(SEIR_Statistics) #TODO: Figure out what class this belongs in

