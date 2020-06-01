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
from mpl_toolkits.basemap import Basemap as Basemap
import imageio

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
# Stage 2a:
# Introduce a secondary mapping of weighted edges based on ridership
# A sidenote that turnstiles don't count transfers. t.e. while we map ridership between nodes
# They almost always take some specific path through the network
# Although... the gridlike structure of nyc subway may make multiple choices viable. TBD
# Stage 3:
# make agents move based on commuting (give them a home)
# make agents infect *stations* for an amount of time, and not directly infect other agents
# fix the line data
# Stage 3.5:
# build some other subway maps.
# Stage 4
# Spawn agents at home based on ridership numbers.
# Give agents some work data

#TODO: it would be good if we outline NYC in the background
#TODO: but it seems a little trickier than I previously thought.
#TODO: this belongs in a graphics class.
def nyc_map_test():
    print('nyc map test')
    west, south, east, north = -74.26, 40.50, -73.70, 40.92
    m = Basemap(resolution='f', # c, l, i, h, f or None
                projection='merc',
                area_thresh=50,
                lat_0=(west + south)/2, lon_0=(east + north)/2,
                llcrnrlon= west, llcrnrlat= south, urcrnrlon= east, urcrnrlat= north)

    m.drawmapboundary(fill_color='#46bcec')
    m.fillcontinents(color='#f2f2f2',lake_color='#46bcec')
    m.drawcoastlines()
    m.drawrivers()

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

g_subway_map, routing_dict = Preprocessing.get_subway_map('MOSCOW')
ADD_SHADOW = False
if ADD_SHADOW:
    g_full_map = Preprocessing.make_exit_nodes(g_subway_map)
else:
    g_full_map = g_subway_map

print('Num stations:', len(g_subway_map.nodes()))
print('Total order:', len(g_full_map.nodes()))
num_connected_components = nx.algorithms.components.number_connected_components(g_full_map)
print('NCC:', num_connected_components ) #if this is >1, we have a problem

if num_connected_components > 1:
    print("Warning: graph not connected. Picking GCC")
    cc_list = sorted(nx.connected_components(g_full_map), key=len, reverse=True)  # largest first, for further debugging
    g_full_map = g_full_map.subgraph((cc_list[0]))

model = Model.SEIR_Subway_Model(SimulationParams.TOTAL_POPULATION, g_full_map, routing_dict)


SEIR_Statistics = np.zeros(shape=(SimulationParams.RUN_SPAN + 1, 5)) #reminder: np is zero indexed
subway_map = model.our_graph
SEIR_Statistics[0, 0] = 0
SEIR_Statistics[0, 1:5] = model.calculate_SEIR(True)  #reminder: but ranges are exclusive or something.

# TODO: put constants in right folder. DisplayParams?
ALWAYS_SHOW_GRAPH = False
SHOW_EVERY_2X = False
GRAPH_BY_FEATURE = 'viral_load'  # best options are hotspot, viral_load
GIF_DELAY = 0.4
for i in range(1, SimulationParams.RUN_SPAN + 1):
    model.step()
    print('TIME', model.schedule.time)
    SEIR_Statistics[i, 0] = model.schedule.time
    SEIR_Statistics[i, 1:5] = model.calculate_SEIR(True)
    subway_map = model.our_graph

    subway_map.update_hotspots(model.schedule.agents)
    f = plt.figure()
    subway_map.draw_graph(GRAPH_BY_FEATURE, timestamp=str(i)) #by number of agents (unnormalized)
    f.savefig("Visualizations/time" + f'{i:03}')
    if ALWAYS_SHOW_GRAPH or (math.log2(i).is_integer() and SHOW_EVERY_2X) or i == SimulationParams.RUN_SPAN:
        plt.show()
    plt.close(f)
draw_SEIR_curve(SEIR_Statistics) #TODO: Figure out what class this belongs in
images = []
for i in range(1, SimulationParams.RUN_SPAN + 1):
    images.append(imageio.imread("Visualizations/time" + f'{i:03}.png'))
imageio.mimsave('Visualizations/infection_timelapse.gif', images, duration=GIF_DELAY)
