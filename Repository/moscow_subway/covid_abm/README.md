covid_abm
========================

A covid-19 agent based model on how covid spreads across Moscow subway system, aka the metro

Rules:

* Model (Transport Networks):

  * Nodes are metro stations

  * Edges are the distances between metro stations

  * Graph is a represenatation of Moscow Metro

* Agents are Stations


Currently thinking of network as stations(nodes) and the distances between them(edges).
I am currenly not considering people, but if a node is infected after a while it can spread to other nodes.

Next Steps:
    * virus_spread_chance -- infected person must show up there (longer rides increases chances of spread)
    * recovery_chance -- infected people have been treated (SEIR Model)
    
