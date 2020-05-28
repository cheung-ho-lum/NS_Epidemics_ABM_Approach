import Preprocessing
from ABM import Agent
from ABM import Model

RUN_SPAN = 10
# Stage 1:
# Just the map and people
# Create station map
# Add an above-ground node for people in the zip. These people interact... 'freely'
# Use MESA to make our Model
# Have people move around the subway
# End stage 1


G_subway_map = Preprocessing.get_subway_map('TEST')
G_full_map = Preprocessing.make_exit_nodes(G_subway_map)
# Let's say that ticks are approximately 30 minutes.
# And that agents have a chance of infecting anyone between their source and destination while in subway
print('Num stations:', len(G_subway_map.nodes())) #TODO: It appears I've written some trolly code
print('Total order:', len(G_full_map.nodes()))
model = Model.SEIR_Subway_Model(10, G_full_map)
for i in range(1, RUN_SPAN + 1):
    model.step()
    print('TIME', i)
    for agent in model.schedule.agents:
        print('Agent', agent.unique_id, 'is at location', agent.location)
