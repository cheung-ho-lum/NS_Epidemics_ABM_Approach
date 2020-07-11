import imageio
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon
from mpl_toolkits.basemap import Basemap as Basemap
from itertools import count
import matplotlib.pyplot as plt
import networkx as nx

import Utilities
from Parameters import SimulationParams, DisplayParams
import math
import numpy as np

# TODO: when this gets fleshed out, it might belong in its own directory

# recommended NYC settings
# latitude:     40.5744     40.903
# longtitude:   -74.0445    -73.836

# recommended World settings
# latitude:     -55         65
# longtitude    -180        180


# TODO: timespan (ok this is a main.py issue) needs to be set based on model
# TODO: we can proooobably draw the map once and keep it around. this will cut down on runtime.
# A quick note that the suggested way to save a basemap is to pickle/unpickle it. ookkk... maybe later.


# TODO: ok, you should have definitely used a dataframe
def draw_geographical_hotspots(data_matrix="", zip_list="", date_list="", dataframe=None,
                               save_name='tests_by_modzcta_NYC_', ax=None, fig=None):
    images = []
    for date in date_list:
        fig = plt.figure()
        fig.suptitle(date)
        ax = fig.add_subplot(111)
        m = Basemap(projection='merc', llcrnrlon=-74.1, llcrnrlat=40.55, urcrnrlon=-73.75,
                    urcrnrlat=40.91, lat_ts=0, resolution='h', suppress_ticks=True)
        m.drawcountries(linewidth=1)
        m.drawcoastlines(linewidth=1)
        m.readshapefile('Data/NYC/Geographical/NYC_modzcta', 'NYC')

        # Color the patches
        patches = []
        color_list = []

        for info, shape in zip(m.NYC_info, m.NYC):
            # print(info)
            s_modzcta = info['modzcta']

            patches.append(Polygon(np.array(shape), True))

            if s_modzcta in zip_list:
                modzcta = int(s_modzcta)
                case_rate = data_matrix[zip_list.index(s_modzcta)][date_list.index(date)]
                vmax = 0.04  # corona = 4643 / 111594.1 =
                vmin = 0
                gradient = max(0, (vmax - case_rate) / vmax)

                #TOOD: why is the typecast to int necessary here? hmm...
                r_value = int(round(153 - 153 * (1 - gradient)))
                g_value = int(round(255 - 153 * (1 - gradient)))
                b_value = int(round(153 - 153 * (1 - gradient)))
                hex_code = "#{0:02x}{1:02x}{2:02x}".format(r_value, g_value, b_value)
                color_list.append(hex_code)

            else:  # coloring for staten island and other things like it
                color_list.append(r"#99FF99")

        # colors go from ffffff to 660066
        ax.add_collection(PatchCollection(patches, facecolor=color_list, edgecolor='k', linewidths=1., zorder=2))
        fig.savefig("Visualizations/" + save_name + date)
        plt.close(fig)

        images.append(imageio.imread("Visualizations/" + save_name + date + ".png"))
    imageio.mimsave('Visualizations/' + save_name + '.gif', images, duration=DisplayParams.GIF_DELAY)
    return None

def draw_prediction_error(errors_dict, save_name='total_error', vmin=0, vmax=2):
    fig = plt.figure()
    fig.suptitle('Regional Error')
    ax = fig.add_subplot(111)
    m = Basemap(projection='merc', llcrnrlon=-74.1, llcrnrlat=40.55, urcrnrlon=-73.75,
                urcrnrlat=40.91, lat_ts=0, resolution='h', suppress_ticks=True)
    m.drawcountries(linewidth=1)
    m.drawcoastlines(linewidth=1)
    m.readshapefile('Data/NYC/Geographical/NYC_modzcta', 'NYC')

    # Color the patches
    patches = []
    color_list = []

    for info, shape in zip(m.NYC_info, m.NYC):
        s_modzcta = info['modzcta']

        patches.append(Polygon(np.array(shape), True))

        if s_modzcta in errors_dict.keys():
            error_rate = errors_dict[s_modzcta]
            gradient = max(0, (vmax - error_rate) / vmax)

            # TOOD: why is the typecast to int necessary here? hmm...
            r_value = int(round(153 - 153 * (1 - gradient)))
            g_value = int(round(255 - 153 * (1 - gradient)))
            b_value = int(round(153 - 153 * (1 - gradient)))
            hex_code = "#{0:02x}{1:02x}{2:02x}".format(r_value, g_value, b_value)
            color_list.append(hex_code)

        else:  # coloring for staten island and other things like it
            color_list.append(r"#99FF99")

    # colors go from ffffff to 660066
    ax.add_collection(PatchCollection(patches, facecolor=color_list, edgecolor='k', linewidths=1., zorder=2))
    fig.savefig("Visualizations/" + save_name)
    plt.close(fig)

def draw_hotspots_forecast(forecasts_dict, actual_dict=None, offset=32, save_name='forecast_by_modzcta_NYC_',
                           print_results=False):
    images = []
    if actual_dict is None:
        vmin, vmax = 0, 0.04  # corona = 4643 / 111594.1
    else:
        vmin, vmax = 0, 0.04
        save_name = 'error_by_modzcta_NYC_'
        for i in range(0, SimulationParams.RUN_SPAN+1):
            for key in forecasts_dict:
                forecast = forecasts_dict[key][i]
                # TODO: copying needed! i think this changes forecasts_dict!
                if i - offset < 0:
                    forecasts_dict[key][i] = 0
                else:
                    actual = actual_dict[key][i - offset]
                    forecasts_dict[key][i] = abs(forecast - actual)
                    if print_results:
                        print(key, i, forecast - actual)

    for i in range(0, SimulationParams.RUN_SPAN+1):
        fig = plt.figure()
        fig.suptitle('Regional Forecast for t=' + str(i))
        ax = fig.add_subplot(111)
        m = Basemap(projection='merc', llcrnrlon=-74.1, llcrnrlat=40.55, urcrnrlon=-73.75,
                    urcrnrlat=40.91, lat_ts=0, resolution='h', suppress_ticks=True)
        m.drawcountries(linewidth=1)
        m.drawcoastlines(linewidth=1)
        m.readshapefile('Data/NYC/Geographical/NYC_modzcta', 'NYC')

        # Color the patches
        patches = []
        color_list = []

        for info, shape in zip(m.NYC_info, m.NYC):
            # print(info)
            s_modzcta = info['modzcta']

            patches.append(Polygon(np.array(shape), True))

            if s_modzcta in forecasts_dict.keys():
                case_rate = forecasts_dict[s_modzcta][i]
                gradient = max(0, (vmax - case_rate) / vmax)

                #TOOD: why is the typecast to int necessary here? hmm...
                r_value = int(round(153 - 153 * (1 - gradient)))
                g_value = int(round(255 - 153 * (1 - gradient)))
                b_value = int(round(153 - 153 * (1 - gradient)))
                hex_code = "#{0:02x}{1:02x}{2:02x}".format(r_value, g_value, b_value)
                color_list.append(hex_code)

            else:  # coloring for staten island and other things like it
                color_list.append(r"#99FF99")

        # colors go from ffffff to 660066
        ax.add_collection(PatchCollection(patches, facecolor=color_list, edgecolor='k', linewidths=1., zorder=2))
        fig.savefig("Visualizations/" + save_name + str(i))
        plt.close(fig)

        images.append(imageio.imread("Visualizations/" + save_name + (str(i)) + ".png"))
    imageio.mimsave('Visualizations/' + save_name + '_timelapse.gif', images, duration=DisplayParams.GIF_DELAY)
    return None

def draw_graph(nx_graph, node_attr="type", timestamp="", vmin=0, vmax=0.11,
               map_type=SimulationParams.MAP_TYPE_WORLD, figure=None, model=None, with_labels=False, with_edges=False):
    has_background_map = True
    if DisplayParams.DRAW_MAP:
        ax = figure.add_subplot(111)
        if map_type == SimulationParams.MAP_TYPE_HLC_CURATED_WAN:
            m = Basemap(projection='merc', llcrnrlon=-180, llcrnrlat=-55, urcrnrlon=180,
                    urcrnrlat=65, lat_ts=0, resolution='l', suppress_ticks=True)
            m.drawcountries(linewidth=1)
            m.drawcoastlines(linewidth=1)
        elif map_type == SimulationParams.MAP_TYPE_NYC:
            m = Basemap(projection='merc', llcrnrlon=-74.1, llcrnrlat=40.55, urcrnrlon=-73.75,
                    urcrnrlat=40.91, lat_ts=0, resolution='h', suppress_ticks=True)
            m.drawcountries(linewidth=1)
            m.drawcoastlines(linewidth=1)
            m.readshapefile('Data/NYC/Geographical/NYC_modzcta', 'NYC')

            # Color the patches
            patches = []
            color_list = []

            for info, shape in zip(m.NYC_info, m.NYC):
                norm_hotspot = -1
                #print(info)
                modzcta = info['modzcta']
                zcta = info['zcta']
                #print(modzcta, zcta) #zcta has multipe entries
                patches.append(Polygon(np.array(shape), True))
                zip2s = model.zip_to_station_dictionary
                stations = []
                if modzcta in zip2s:
                    stations = zip2s[modzcta]
                    norm_hotspot = nx_graph.nodes[stations[0]]['normalized_hotspot']

                if norm_hotspot >= 0:
                    vmax_map = 0.0011
                    gradient = max(0, (vmax_map - norm_hotspot) / vmax_map)

                    r_value = round(153 - 153 * (1 - gradient))
                    g_value = round(255 - 153 * (1 - gradient))
                    b_value = round(153 - 153 * (1 - gradient))
                    hex_code = "#{0:02x}{1:02x}{2:02x}".format(r_value, g_value, b_value)
                    color_list.append(hex_code)

                else:  # coloring for staten island and other things like it
                    color_list.append(r"#99FF99")

            # colors go from ffffff to 660066
            ax.add_collection(PatchCollection(patches, facecolor=color_list, edgecolor='k', linewidths=1., zorder=2))
        elif map_type == SimulationParams.MAP_TYPE_TREN_MADRID:
            m = Basemap(projection='merc', llcrnrlon=-4.14, llcrnrlat=40.15, urcrnrlon=-3.29,
                    urcrnrlat=40.83, lat_ts=0, resolution='h', suppress_ticks=True)

            m.readshapefile('Data/madrid/Geographical/espania', 'Madrid')

            # Color the patches
            patches = []
            color_list = []

            for info, shape in zip(m.Madrid_info, m.Madrid):
                patches.append(Polygon(np.array(shape), True))
                color_list.append(r"#99FF99")

            # colors go from ffffff to 660066
            ax.add_collection(PatchCollection(patches, facecolor=color_list, edgecolor='k', linewidths=1., zorder=2))

        else:
            print('no background map found')
            has_background_map = False
    else:
        has_background_map = False

    groups = set(nx.get_node_attributes(nx_graph, node_attr).values())
    mapping = dict(zip(sorted(groups), count()))
    nodes = nx_graph.nodes()
    node_sizes = []
    if not DisplayParams.DRAW_MAP_ONLY:
        for n in nodes:  # TODO: hmm... this needs some rethinking with different passenger flows.
            size_of_n = math.sqrt(nodes[n]['flow'] / 1e6) #500 works well for subway, 1e6 for airports
            node_sizes.append(min(100, max(10, size_of_n)))  # range from 10 - 100
            #this changes pos to the mercator projection
            if has_background_map:
                mx, my = m(nodes[n]['x'], nodes[n]['y'])
                nodes[n]['pos'] = (mx, my)

        #colors = [mapping[nx_graph.nodes[n][node_attr]] for n in nodes]

        colors = list(nx.get_node_attributes(nx_graph, node_attr).values())
        print('vmax:', max(colors)) #use to get an idea what vmax is.

        pos = nx.get_node_attributes(nx_graph, 'pos')
        if len(pos) == 0:
            pos = nx.spring_layout(nx_graph, seed=SimulationParams.GRAPH_SEED)

        edgelist = []
        if with_edges:
            edgelist = list(nx_graph.edges)
        nx.draw_networkx(nx_graph, node_size=node_sizes, with_labels=with_labels, width=0.2, node_color=colors, pos=pos,
                         cmap=plt.cm.jet, vmin=vmin, vmax=vmax, edge_color='k', edgelist=edgelist) #edgelist = none for airports for now.

    if len(timestamp) > 0:
        plt.title(node_attr + ' t=' + timestamp)

    return None

def draw_case_rate_by_zip(actual_data, forecast_data, fig, offset=32, target_keys=None):
    # all data required for now
    ax = fig.add_subplot(111, facecolor='#dddddd', axisbelow=True)
    num_entries = len(list(actual_data.values())[0])

    time_col = []
    for n in range(0, num_entries):
        time_col.append(n)

    hex_gradient = 0
    for zc in forecast_data:
        if target_keys is None or zc in target_keys:
            hex_gradient += 1
            r_value = 255
            g_value = 100  # max(100, 255 - hex_gradient)
            b_value = 100  # max(100, 255 - hex_gradient)
            hex_code = "#{0:02x}{1:02x}{2:02x}".format(r_value, g_value, b_value)
            #ax.plot(time_col, forecast_data[zc][offset:], hex_code, alpha=0.5, lw=2, label=zc, linestyle='dashed')

            #ax.plot(time_col, actual_data[zc], hex_code, alpha=0.5, lw=2, label=zc)

            error = [x1 - x2 for (x1, x2) in zip(forecast_data[zc][offset:], actual_data[zc])]
            ax.plot(time_col, error, hex_code, alpha=0.8, lw=2)

            #this one (like mape) is quite ugly
            #percent_error = [x1 / x2 for (x1, x2) in zip(error, actual_data[zc])]
            #ax.plot(time_col, percent_error, hex_code, alpha=0.5, lw=2)

    ax.set_xlabel('Time')
    ax.set_ylabel('Cumulative Case Rate (Error)')
    #ax.set_ylim(0, 6000/100000)
    ax.yaxis.set_tick_params(length=0)
    ax.xaxis.set_tick_params(length=0)
    ax.grid(b=True, which='major', c='w', lw=2, ls='-')
    legend = ax.legend()
    legend.get_frame().set_alpha(0.5)
    for spine in ('top', 'right', 'bottom', 'left'):
        ax.spines[spine].set_visible(False)

def draw_SEIR_curve(statistics, fig, benchmark_SEIR=None):
    """It's questionable to keep statistics in a non-descript matrix because we might want more, but for now:
    rows = timestamp, cols(5) = t,S,E,I,R"""
    #time_span = np.shape(statistics)[1] #should match run timespan

    ax = fig.add_subplot(111, facecolor='#dddddd', axisbelow=True)
    time_col = statistics[..., 0]
    ax.plot(time_col, statistics[..., 1], 'blue', alpha=0.3, lw=2, label='Susceptible', linestyle='dashed')
    ax.plot(time_col, statistics[..., 2], 'orange', alpha=0.3, lw=2, label='Exposed', linestyle='dashed')
    ax.plot(time_col, statistics[..., 3], 'red', alpha=0.3, lw=2, label='Infected', linestyle='dashed')
    ax.plot(time_col, statistics[..., 4], 'green', alpha=0.3, lw=2, label='Removed', linestyle='dashed')

    #also show cumulative infections. TODO: kludgy
    infected_total = np.zeros(shape=(SimulationParams.RUN_SPAN + 1, 1))
    for i in range(0, SimulationParams.RUN_SPAN + 1):
        infected_total[i] = statistics[i, 3] + statistics[i, 4]

    if len(benchmark_SEIR) > 0:
        bench_time_col = benchmark_SEIR[..., 0]
        ax.plot(time_col, statistics[..., 3] + statistics[..., 4], 'black', alpha=0.5, lw=2, label='Total Cases (Forecast)', linestyle='dashed')
        ax.plot(bench_time_col, benchmark_SEIR[..., 2], 'gray', alpha=0.5, lw=2, label='New Cases (Actual)')
        ax.plot(bench_time_col, benchmark_SEIR[..., 3], 'black', alpha=0.5, lw=2, label='Total Cases (Actual)')
    ax.set_xlabel('Time')
    ax.set_ylabel('Patients')
    benchmark_max = 0
    if len(benchmark_SEIR) > 0:
        benchmark_max = np.max(benchmark_SEIR[..., 3])
        y_lim = max(np.max(statistics[..., 3:]),
                    np.max(statistics[..., 4:]),
                    benchmark_max
                    )  # y lim now based on maximum of a few possible statistics.
        print(Utilities.calculate_MAPE(benchmark_SEIR[..., 3], statistics[..., 3] + statistics[..., 4]))
    else:
        y_lim = np.max(statistics[..., 2:5])  # *HLC 19.06 - y lim now ignores S statistic
    ax.set_ylim(0, y_lim)
    ax.yaxis.set_tick_params(length=0)
    ax.xaxis.set_tick_params(length=0)
    ax.grid(b=True, which='major', c='w', lw=2, ls='-')
    legend = ax.legend()
    legend.get_frame().set_alpha(0.5)
    for spine in ('top', 'right', 'bottom', 'left'):
        ax.spines[spine].set_visible(False)

    return None

#TODO: it would be good if we outline NYC in the background
#TODO: but it seems a little trickier than I previously thought.
#TODO: this belongs in a graphics class.

# def nyc_map_test():
#     print('nyc map test')
#     west, south, east, north = -74.26, 40.50, -73.70, 40.92
#     m = Basemap(resolution='f', # c, l, i, h, f or None
#                 projection='merc',
#                 area_thresh=50,
#                 lat_0=(west + south)/2, lon_0=(east + north)/2,
#                 llcrnrlon= west, llcrnrlat= south, urcrnrlon= east, urcrnrlat= north)
#
#     m.drawmapboundary(fill_color='#46bcec')
#     m.fillcontinents(color='#f2f2f2',lake_color='#46bcec')
#     m.drawcoastlines()
#     m.drawrivers()