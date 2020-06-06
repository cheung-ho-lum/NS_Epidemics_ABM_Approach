from mpl_toolkits.basemap import Basemap as Basemap
from itertools import count
import matplotlib.pyplot as plt
import networkx as nx
from Parameters import SimulationParams, DisplayParams
import math
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


def draw_graph(nx_graph, node_attr="type", timestamp="", vmin=0, vmax=0.11, map_type = SimulationParams.MAP_TYPE_WORLD):
    has_background_map = True
    if DisplayParams.DRAW_MAP:
        if map_type == SimulationParams.MAP_TYPE_HLC_CURATED_WAN:
            m = Basemap(projection='merc', llcrnrlon=-180, llcrnrlat=-55, urcrnrlon=180,
                    urcrnrlat=65, lat_ts=0, resolution='l', suppress_ticks=True)
            m.drawcountries(linewidth=1)
            m.drawcoastlines(linewidth=1)
        elif map_type == SimulationParams.MAP_TYPE_NYC:
            m = Basemap(projection='merc', llcrnrlon=-74.1, llcrnrlat=40.57, urcrnrlon=-73.8,
                    urcrnrlat=40.91, lat_ts=0, resolution='h', suppress_ticks=True)
            m.drawcountries(linewidth=1)
            m.drawcoastlines(linewidth=1)
        else:
            print('no background map found')
            has_background_map = False
    else:
        has_background_map = False

    groups = set(nx.get_node_attributes(nx_graph, node_attr).values())
    mapping = dict(zip(sorted(groups), count()))
    nodes = nx_graph.nodes()
    node_sizes = []

    for n in nodes:  # TODO: hmm... this needs some rethinking with different passenger flows.
        size_of_n = math.sqrt(nodes[n]['flow'] / 1e6) #500 works well for subway, 1e6 for airports
        node_sizes.append(min(100, max(10, size_of_n)))  # range from 10 - 100
        #this changes pos to the mercator projection
        if has_background_map:
            mx, my = m(nodes[n]['x'], nodes[n]['y'])
            nodes[n]['pos'] = (mx, my)

    colors = [mapping[nx_graph.nodes[n][node_attr]] for n in nodes]
    if 'normalized' in node_attr:
        colors = list(nx.get_node_attributes(nx_graph, node_attr).values())
        # print(max(colors)) #use to get an idea what vmax is.
    pos = nx.get_node_attributes(nx_graph, 'pos')
    if len(pos) == 0:
        pos = nx.spring_layout(nx_graph, seed=SimulationParams.GRAPH_SEED)
    nx.draw_networkx(nx_graph, node_size=node_sizes, with_labels=False, width=0.1, node_color=colors, pos=pos,
                     cmap=plt.cm.jet, vmin=vmin, vmax=vmax, edgelist=[]) #edgelist = none for airports for now.

    if len(timestamp) > 0:
        plt.title(node_attr + ' t=' + timestamp)

    return None


def draw_SEIR_curve(statistics, fig):
    """It's questionable to keep statistics in a non-descript matrix because we might want more, but for now:
    rows = timestamp, cols(5) = t,S,E,I,R"""
    #time_span = np.shape(statistics)[1] #should match run timespan

    ax = fig.add_subplot(111, facecolor='#dddddd', axisbelow=True)
    ax.plot(statistics[..., 0], statistics[..., 1], 'blue', alpha=0.5, lw=2, label='Susceptible')
    ax.plot(statistics[..., 0], statistics[..., 2], 'orange', alpha=0.5, lw=2, label='Exposed')
    ax.plot(statistics[..., 0], statistics[..., 3], 'red', alpha=0.5, lw=2, label='Infected')
    ax.plot(statistics[..., 0], statistics[..., 4], 'green', alpha=0.5, lw=2, label='Recovered')
    ax.set_xlabel('Time')
    ax.set_ylabel('Patients')
    ax.set_ylim(0, sum(statistics[0, 1:]))
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