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
import Utilities

benchmark_statistics = []
# Draw NYC Case Map (currently cumulative test cases, not normalized by population)
if DisplayParams.DRAW_NYC_CASES:
    Utilities.draw_severity_by_region()

if SimulationParams.MAP_TYPE == SimulationParams.MAP_TYPE_LONDON:
    case_rates_actual = Utilities.london_case_data_by_borough_dict()
    raw_case_data = Utilities.london_case_data_by_borough_dict(normalized=False)

# Forecasting dictionary by modzcta. Starts from April 1 (t = 32)
if SimulationParams.MAP_TYPE == SimulationParams.MAP_TYPE_NYC:
    case_rates_actual = Utilities.nyc_case_data_by_modzcta_dict(smoothing=0)
    raw_case_data = Utilities.nyc_case_data_by_modzcta_dict(normalized=False, smoothing=0)

# Subway Simulation Setup
if SimulationParams.SIMULATION_TYPE == SimulationParams.SUBWAY_SIM:
    g_subway_map, routing_dict = Preprocessing.get_subway_map(SimulationParams.MAP_TYPE)

    print('Total order:', len(g_subway_map.nodes()))
    num_connected_components = nx.algorithms.components.number_connected_components(g_subway_map)
    print('NCC:', num_connected_components)  # if this is >1, we have a problem

    if num_connected_components > 1:  # TODO: this goes in preprocessing
        print("Warning: graph not connected. Picking GCC")
        cc_list = sorted(nx.connected_components(g_subway_map), key=len, reverse=True)  # largest first
        g_subway_map = g_subway_map.subgraph((cc_list[0]))

    model = SubwayModel.SubwayModel(g_subway_map, routing_dict)

    if SimulationParams.MAP_TYPE == SimulationParams.MAP_TYPE_NYC:
        date_start = datetime.datetime(2020, 3, 1, 0, 0)  # inclusive
        date_end = datetime.datetime(2020, 3, 21, 0, 0)  # inclusive
        valid_zip_codes = model.zip_to_station_dictionary.keys()
        # Print a list of population by zip code
        # for key in case_rates_actual:
        #     if key in valid_zip_codes:
        #         print(key, "{:.2f}".format(raw_case_data[key][0] / case_rates_actual[key][0]))
        benchmark_statistics = Utilities.get_benchmark_statistics('NYC', date_start, 31, raw_case_data, valid_zip_codes)

    if SimulationParams.MAP_TYPE == SimulationParams.MAP_TYPE_LONDON:
        date_start = datetime.datetime(2020, 3, 1, 0, 0)  # inclusive
        benchmark_statistics = Utilities.get_benchmark_statistics('LONDON', date_start, 0, raw_case_data, None)


    if DisplayParams.DRAW_NYC_CASES:
        f = plt.figure()
        Graphics.draw_graph(model.subway_graph.graph, 'commute_time', timestamp='0', vmin=0, vmax=26.0, figure=f,
                            model=model, map_type=SimulationParams.MAP_TYPE_NYC, with_labels=True, with_edges=True)
        plt.show()
        plt.close(f)

        for node in model.subway_graph.graph.nodes():
            current_node = model.subway_graph.graph.nodes[node]
            print(node, current_node['population'], current_node['region'], current_node['zip'])

        f = plt.figure()
        Graphics.draw_graph(model.subway_graph.graph, 'population', timestamp='0', vmin=0, vmax=50000, figure=f,
                            model=model, map_type=SimulationParams.MAP_TYPE_NYC, with_labels=True, with_edges=True)
        plt.show()
        plt.close(f)

        f = plt.figure()
        Graphics.draw_graph(model.subway_graph.graph, 'flow', timestamp='0', vmin=0, vmax=50000, figure=f,
                            model=model, map_type=SimulationParams.MAP_TYPE_NYC, with_labels=True)
        plt.show()
        plt.close(f)
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

#Track case rates for the subway only. TODO: the model should really just update itself every step.
if SimulationParams.SIMULATION_TYPE == SimulationParams.SUBWAY_SIM:
    case_rates_forecast = {}
    case_rates_forecast = model.calculate_modzcta_case_rate(case_rates_forecast, 0)

# Run the simulation. Set DRAW_GRAPHS to false to make this run faster
for i in range(1, SimulationParams.RUN_SPAN + 1):
    model.step()
    print('TIME', model.schedule.time)
    SEIR_Statistics[i, 0] = model.schedule.time
    SEIR_Statistics[i, 1:5] = model.calculate_SEIR(True)

    if SimulationParams.SIMULATION_TYPE == SimulationParams.SUBWAY_SIM:
        case_rates_forecast = model.calculate_modzcta_case_rate(case_rates_forecast, i)

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
            vmax = 0.0033
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

if SimulationParams.MAP_TYPE == SimulationParams.MAP_TYPE_LONDON:
    case_rates_forecast.pop('City of London') #Omit this forecast. No case rate
    f = plt.figure()
    Graphics.draw_case_rate_by_zip(case_rates_actual, case_rates_forecast, f, offset=0)
    f.savefig("Visualizations/Case_Rates_Plot")
    plt.show()
    plt.close(f)

    mape_dict = Utilities.calculate_MAPE_by_zip(actual=case_rates_actual, forecast=case_rates_forecast, offset=1,
                                                print_results=True)

if SimulationParams.MAP_TYPE == SimulationParams.MAP_TYPE_NYC:
    f = plt.figure()
    Graphics.draw_case_rate_by_zip(case_rates_actual, case_rates_forecast, f, offset=32)
    f.savefig("Visualizations/Case_Rates_Plot")
    plt.show()
    plt.close(f)

    #print(case_rates_dict)
    mape_dict = Utilities.calculate_MAPE_by_zip(actual=case_rates_actual, forecast=case_rates_forecast, offset=32, print_results=True)

    if DisplayParams.DRAW_NYC_CASES:
        Graphics.draw_hotspots_forecast(case_rates_forecast, actual_dict=case_rates_actual, offset=32)
        Graphics.draw_prediction_error(mape_dict, vmin=0, vmax=0.8)

    if DisplayParams.PRINT_DEBUG:
        print('MAPE Summary')
        for key in mape_dict:
            print(key, mape_dict[key])

        print('Full Forecast Comparison')
        for key in case_rates_forecast:
            if key in []: #['11692', '11215', '10458', '11419', '10470', '10460', '10003', '10007', '11215']:
                for i in range(32, SimulationParams.RUN_SPAN + 1):
                    forecast = case_rates_forecast[key][i]
                    actual = case_rates_actual[key][i - 32]
                    error = (forecast - actual) / actual
                    print(key, i, forecast, actual, error)


# Save final animation
if DisplayParams.DRAW_GRAPHS:
    images = []
    for i in range(1, SimulationParams.RUN_SPAN + 1):
        images.append(imageio.imread("Visualizations/time" + f'{i:03}.png'))
    imageio.mimsave('Visualizations/infection_timelapse.gif', images, duration=DisplayParams.GIF_DELAY)
