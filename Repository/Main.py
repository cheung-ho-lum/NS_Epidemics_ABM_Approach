import Preprocessing
import Parameters
from ABM import Agent
from ABM import Model
from Parameters import SimulationParams
from itertools import count
import networkx as nx
from Parameters import SubwayParams
import matplotlib.pyplot as plt

# Stage 1:
# Just the map and people
# Create station map
# Add an above-ground node for people in the zip. These people interact... 'freely'
# Use MESA to make our Model
# Have people move around the subway
# End stage 1
# Modification 1: Have people
G_subway_map = Preprocessing.get_subway_map('TEST')
G_full_map = Preprocessing.make_exit_nodes(G_subway_map)
# Let's say that ticks are approximately 30 minutes.
# And that agents have a chance of infecting anyone between their source and destination while in subway
print('Num stations:', len(G_subway_map.nodes())) #TODO: It appears I've written some trolly code
print('Total order:', len(G_full_map.nodes()))
model = Model.SEIR_Subway_Model(10, G_full_map)
for i in range(1, SimulationParams.RUN_SPAN + 1):
    print('TIME', i)
    model.step()
    # 100% past time you created a graph wrapper
    subway_map = model.graph

    groups = set(nx.get_node_attributes(subway_map, 'type').values())
    mapping = dict(zip(sorted(groups), count()))
    nodes = subway_map.nodes()
    colors = [mapping[subway_map.nodes[n]['type']] for n in nodes]
    pos = nx.spring_layout(subway_map, seed=SubwayParams.GRAPH_SEED)
    nx.draw_networkx(subway_map, node_size=700, with_labels=False, width=0.1, node_color=colors, pos=pos, cmap=plt.cm.jet)

    #plt.show()

