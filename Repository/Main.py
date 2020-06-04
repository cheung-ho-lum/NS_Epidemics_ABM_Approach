import Graphics
import Preprocessing
from ABM import SubwayModel, AirModel
from Parameters import SimulationParams, DisplayParams
import networkx as nx
import matplotlib.pyplot as plt
import math
import numpy as np
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
# Stage 3.6:
# total passenger flow now calculated
# riders spawned by ratio of their station to the total
# Some code cleanup (give map types an enum, create DisplayParams)
# Stage 3.6.5:
# Evaluate and pull out what is common to agents on all types of transportation
# Create Generic Transportation Model
# Refactor SubwayModel to inherit from TransportationModel
# Stage 3.6.6:
# Redo agents to best mimic a population at a station.
# Stage 3.7:
# More code cleanup: It's time preprocessing just created an OurGraph
# Clean up passenger flow calculations
# Stage 3.9:
# Refactor and clean up data folder.
# Code cleanup: Model should really handle more of its own graphics
# Stage 4:
# Give agents some work data


# Open TODO modeling parameters. Note that all parameters beyond basic abstraction should be optional!
# Currently, viral load is not diminished by distance.
# Currently, viral load is not diminished by number of routes

analysis_type = 'air_routes'
if analysis_type == 'subway':
    g_subway_map, routing_dict, passenger_flow = Preprocessing.get_subway_map('NYC')

    ADD_SHADOW = False
    if ADD_SHADOW:
        g_full_map = Preprocessing.make_exit_nodes(g_subway_map)
    else:
        g_full_map = g_subway_map

    print('Num stations:', len(g_subway_map.nodes()))
    print('Total order:', len(g_full_map.nodes()))
    num_connected_components = nx.algorithms.components.number_connected_components(g_full_map)
    print('NCC:', num_connected_components) #if this is >1, we have a problem

    if num_connected_components > 1:
        print("Warning: graph not connected. Picking GCC")
        cc_list = sorted(nx.connected_components(g_full_map), key=len, reverse=True)  # largest first, for further debugging
        g_full_map = g_full_map.subgraph((cc_list[0]))

    model = SubwayModel.Subway_Model(SimulationParams.TOTAL_POPULATION, g_full_map, routing_dict, passenger_flow)

if analysis_type == 'air_routes':
    g_airway_map = Preprocessing.get_airway_map('world')
    print('Total order:', len(g_airway_map.graph.nodes()))
    num_connected_components = nx.algorithms.components.number_connected_components(g_airway_map.graph)
    print('NCC:', num_connected_components)  # if this is >1, we have a problem
    if num_connected_components > 1:
        print("Warning: graph not connected. Picking GCC")
        cc_list = sorted(nx.connected_components(g_airway_map.graph), key=len, reverse=True)  # largest first, for further debugging
        g_airway_map.graph = g_airway_map.graph.subgraph((cc_list[0]))

    model = AirModel.Air_Model(SimulationParams.TOTAL_POPULATION, g_airway_map)


SEIR_Statistics = np.zeros(shape=(SimulationParams.RUN_SPAN + 1, 5)) #reminder: np is zero indexed
SEIR_Statistics[0, 0] = 0
SEIR_Statistics[0, 1:5] = model.calculate_SEIR(True)  #reminder: but ranges are exclusive or something.


for i in range(1, SimulationParams.RUN_SPAN + 1):
    model.step()
    print('TIME', model.schedule.time)
    SEIR_Statistics[i, 0] = model.schedule.time
    SEIR_Statistics[i, 1:5] = model.calculate_SEIR(True)

    #TODO: for now, just create separate graphics modelling for map type
    if analysis_type == 'subway':
        f = plt.figure()
        model.subway_graph.draw_graph(DisplayParams.GRAPH_BY_FEATURE, timestamp=str(i)) #by number of agents (unnormalized)
        f.savefig("Visualizations/time" + f'{i:03}')
        if DisplayParams.ALWAYS_SHOW_GRAPH or (math.log2(i).is_integer() and DisplayParams.SHOW_EVERY_2X):
            plt.show()
        plt.close(f)

    #TODO: Rendering this large graph makes things go real slow.
    if analysis_type == 'air_routes':
        f = plt.figure()
        model.airway_graph.draw_graph(DisplayParams.GRAPH_BY_FEATURE, timestamp=str(i)) #by number of agents (unnormalized)
        f.savefig("Visualizations/time" + f'{i:03}')
        if DisplayParams.ALWAYS_SHOW_GRAPH or ((math.log2(i).is_integer() and DisplayParams.SHOW_EVERY_2X)):
            plt.show()
        plt.close(f)

Graphics.draw_SEIR_curve(SEIR_Statistics)  # TODO: Figure out what class this belongs in
images = []
for i in range(1, SimulationParams.RUN_SPAN + 1):
    images.append(imageio.imread("Visualizations/time" + f'{i:03}.png'))
imageio.mimsave('Visualizations/infection_timelapse.gif', images, duration=DisplayParams.GIF_DELAY)
