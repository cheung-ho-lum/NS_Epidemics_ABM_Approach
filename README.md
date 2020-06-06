# Epidemics on Transportation Networks (with a deep dive into the NYC Subway System)

In this project, we build an ABM framework for modeling epidemics on transportation networks, and use it to take a look at the spread of COVID on the NYC Subway as well as on the world airline network.

## Why?
COVID-19 has disrupted the lives of a lot of people, and so everyone (ourselves included) has been very interested in understanding it better. One important aspect is how it is spread and how we can prevent that.

While statistical models are good at forecasting the current crisis, a simulation is more useful for giving us a general idea of the general spread characteristics of a different outbreak, or even a second wave of covid.

Lastly, we built a framework rather than a single ABM because diseases spread on different transportation networks differently. For example, for subways, we focus our model on the idea that they spread through different lines. This being the case, we need to describe our environment (network) and agent (population at a node) differently.

## How it works
The framework itself is really just different classes of special agents and special networks inherit from a base TransportationModel and SEIR_Agent. This is just the basic OOP paradigm. As for how each of them function, we refer you to this design document with the caveat that things may change as we have better thoughts:
[Framework Design Doc](https://github.com/cheung-ho-lum/NS_Epidemics_ABM_Approach/blob/master/Report/Design_doc_for_expansion_of_subway_model.pdf)

As for the overall flow of the code, the only extra thing is that there is, of course, preprocessing to do. This uml is slightly outdated (we have a graphics module), but should show how things are put together:
[Code UML](https://github.com/cheung-ho-lum/NS_Epidemics_ABM_Approach/blob/master/Report/Scratch_Visuals/covid_subway.png)

### A look at the NYC Subway
Let's look at what we did for the NYC Subway. We have a lot of data for NYC, but not enough that we can see when and where every single commuter enters and exits the subway or if they are infected. We do have turnstile data (passenger flow) and tons of mapping data.

#### Preprocessing
Essentially, we just preprocess NYC subway data into environment data. There's a lot of work and things to complain about here. For example, service S is actually 3 different shuttle services. But perhaps the other key point is that besides the basic network, we store away some key data unique to subways as a transportation system (services, or routes) to use later.

#### Agent (population)
* The population of each station is simply the aggregated passenger flow from the period March 1 to March 21. 
* The agent updates its own SEIR numbers at each timestep based on:
  * SEIR numbers at previous step
  * 'viral load' representing exposure from an outside source.
How this 'viral load' is key. From literature, we think the two major factors are the services coming to the station and the average commute distance from this station. We'll try to model it with this viral load.

#### Environment
It adds node labels describing what route the node is on
It adds node labels describing the passenger flow in and out of the station
It adds node labels describing what complex the node is part of.
For faster lookup, it also has a dictionary of route to nodes on the route

## Demo
For our demo, we choose to show the WAN instead of on the NYC Subway to demonstrate the extensibility of our work. We would like to note that while all models are wrong (For example, it's highly likely that intercity spread in China was due to trains), some are useful (or at least pretty).

![WAN](https://github.com/cheung-ho-lum/NS_Epidemics_ABM_Approach/blob/master/Repository/Visualizations/infection_timelapse_world.gif)
