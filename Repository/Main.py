import Graphics
import Preprocessing
from ABM import SubwayModel, AirModel
from Parameters import SimulationParams, DisplayParams
import networkx as nx
import matplotlib.pyplot as plt
import math
import numpy as np
import imageio

analysis_type = 'air_routes'
if analysis_type == 'subway':
    g_subway_map, routing_dict = Preprocessing.get_subway_map('NYC')

    print('Total order:', len(g_subway_map.nodes()))
    num_connected_components = nx.algorithms.components.number_connected_components(g_subway_map)
    print('NCC:', num_connected_components) #if this is >1, we have a problem

    if num_connected_components > 1:
        print("Warning: graph not connected. Picking GCC")
        cc_list = sorted(nx.connected_components(g_subway_map), key=len, reverse=True)  # largest first, for further debugging
        g_subway_map = g_subway_map.subgraph((cc_list[0]))

    model = SubwayModel.Subway_Model(g_subway_map, routing_dict)

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

    #TODO: so it turns out draw_graph should actually be at the model level. just copypasta for now.
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

Graphics.draw_SEIR_curve(SEIR_Statistics)  # TODO: Figure out what class this belongs in. also save it automatically.

images = []
for i in range(1, SimulationParams.RUN_SPAN + 1):
    images.append(imageio.imread("Visualizations/time" + f'{i:03}.png'))
imageio.mimsave('Visualizations/infection_timelapse.gif', images, duration=DisplayParams.GIF_DELAY)
