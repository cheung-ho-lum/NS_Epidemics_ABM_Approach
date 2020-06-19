import datetime
import Graphics
import Preprocessing
from ABM import SubwayModel, AirModel
from Parameters import SimulationParams, DisplayParams
import networkx as nx
import matplotlib.pyplot as plt
import math
import numpy as np
import imageio

benchmark_statistics = []

# Subway Simulation Setup
if SimulationParams.SIMULATION_TYPE == SimulationParams.SUBWAY_SIM:
    g_subway_map, routing_dict = Preprocessing.get_subway_map('NYC')

    print('Total order:', len(g_subway_map.nodes()))
    num_connected_components = nx.algorithms.components.number_connected_components(g_subway_map)
    print('NCC:', num_connected_components)  # if this is >1, we have a problem

    if num_connected_components > 1:  # TODO: this goes in preprocessing
        print("Warning: graph not connected. Picking GCC")
        cc_list = sorted(nx.connected_components(g_subway_map), key=len, reverse=True)  # largest first
        g_subway_map = g_subway_map.subgraph((cc_list[0]))

    model = SubwayModel.SubwayModel(g_subway_map, routing_dict)

    date_start = datetime.datetime(2020, 3, 1, 0, 0)  # inclusive
    date_end = datetime.datetime(2020, 3, 21, 0, 0)  # inclusive
    benchmark_statistics = Preprocessing.get_benchmark_statistics('NYC', date_start)
# Airway Simulation Setup
elif SimulationParams.SIMULATION_TYPE == SimulationParams.AIR_SIM:
    g_airway_map = Preprocessing.get_airway_map(SimulationParams.MAP_TYPE_HLC_CURATED_WAN)

    print('Total order:', len(g_airway_map.graph.nodes()))
    num_connected_components = nx.algorithms.components.number_connected_components(g_airway_map.graph)
    print('NCC:', num_connected_components)  # if this is >1, we have a problem

    if num_connected_components > 1:
        print("Warning: graph not connected. Picking GCC")
        cc_list = sorted(nx.connected_components(g_airway_map.graph), key=len, reverse=True)  # largest first
        g_airway_map.graph = g_airway_map.graph.subgraph((cc_list[0]))
        for cc in cc_list:
            if len(cc) < 10:
                print(cc)

    model = AirModel.AirModel(g_airway_map)
elif SimulationParams.SIMULATION_TYPE == SimulationParams.TRAIN_SIM:
    g_subway_map, routing_dict = Preprocessing.get_subway_map(SimulationParams.MAP_TYPE_TREN_MADRID)

    print('Total order:', len(g_subway_map.nodes()))
    num_connected_components = nx.algorithms.components.number_connected_components(g_subway_map)
    print('NCC:', num_connected_components)  # if this is >1, we have a problem

    if num_connected_components > 1:  # TODO: this goes in preprocessing
        print("Warning: graph not connected. Picking GCC")
        cc_list = sorted(nx.connected_components(g_subway_map), key=len, reverse=True)  # largest first
        g_subway_map = g_subway_map.subgraph((cc_list[0]))

    model = SubwayModel.SubwayModel(g_subway_map, routing_dict)

SEIR_Statistics = np.zeros(shape=(SimulationParams.RUN_SPAN + 1, 5))  # reminder: np is zero indexed
SEIR_Statistics[0, 0] = 0
SEIR_Statistics[0, 1:5] = model.calculate_SEIR(True)

# Run the simulation. Set DRAW_GRAPHS to false to make this run faster
for i in range(1, SimulationParams.RUN_SPAN + 1):
    model.step()
    print('TIME', model.schedule.time)
    SEIR_Statistics[i, 0] = model.schedule.time
    SEIR_Statistics[i, 1:5] = model.calculate_SEIR(True)

    f = plt.figure()
    map_type = SimulationParams.MAP_TYPE_NYC
    if SimulationParams.SIMULATION_TYPE == SimulationParams.SUBWAY_SIM:
        nx_graph = model.subway_graph.graph
        map_type = SimulationParams.MAP_TYPE_NYC
    elif SimulationParams.SIMULATION_TYPE == SimulationParams.AIR_SIM:
        nx_graph = model.airway_graph.graph
        map_type = SimulationParams.MAP_TYPE_HLC_CURATED_WAN
    elif SimulationParams.SIMULATION_TYPE == SimulationParams.TRAIN_SIM:
        nx_graph = model.subway_graph.graph
        map_type = SimulationParams.MAP_TYPE_TREN_MADRID
    else:
        print('Error: Unknown Simulation Type')

    if DisplayParams.DRAW_GRAPHS:
        vmax = 0.11  # TODO: minor, clean this up. it's color map encoding
        if SimulationParams.SIMULATION_TYPE == SimulationParams.SUBWAY_SIM:
            vmax = 0.0011
        elif SimulationParams.SIMULATION_TYPE == SimulationParams.TRAIN_SIM:
            vmax = 0.0007

        #Draws the graph. figure and model required if you want to draw the map as well
        Graphics.draw_graph(nx_graph, DisplayParams.GRAPH_BY_FEATURE, timestamp=str(i),
                            map_type=map_type, figure=f, model=model, vmax=vmax)

        f.savefig("Visualizations/time" + f'{i:03}')
        if DisplayParams.ALWAYS_SHOW_GRAPH or (math.log2(i).is_integer() and DisplayParams.SHOW_EVERY_2X):
            plt.show()
    plt.close(f)

# Save final SEIR Results
f = plt.figure()
Graphics.draw_SEIR_curve(SEIR_Statistics, f, benchmark_SEIR=benchmark_statistics)
f.savefig("Visualizations/SEIR_Curve")
plt.show()
plt.close(f)

# Save final animation
if DisplayParams.DRAW_GRAPHS:
    images = []
    for i in range(1, SimulationParams.RUN_SPAN + 1):
        images.append(imageio.imread("Visualizations/time" + f'{i:03}.png'))
    imageio.mimsave('Visualizations/infection_timelapse.gif', images, duration=DisplayParams.GIF_DELAY)
