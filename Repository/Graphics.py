import matplotlib.pyplot as plt
import numpy as np

from Parameters import SimulationParams


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