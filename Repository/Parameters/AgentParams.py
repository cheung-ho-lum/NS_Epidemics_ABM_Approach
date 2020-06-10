STATUS_SUSCEPTIBLE = 'Susceptible'
STATUS_EXPOSED = 'Exposed'
STATUS_INFECTED = 'Infected'
STATUS_RECOVERED = 'Recovered'
MAP_LOCATION_JUNCTION_BLVD = 451
MAP_LOCATION_BRIGHTON_BEACH = 55
MAP_LOCATION_WUHAN_TIANHE = 3376
# Researcher Adjustable
DEFAULT_BETA = 1.75  # This is the real question. (R0 =  beta/gamma btw)
DEFAULT_ALPHA = 0.2  # About 5 days
DEFAULT_GAMMA = 0.5  # About 2 days infectious and not removed
ISOLATED_BETA = 1.00 #TODO: consider... hmm. consider how to model this properly. (currently unused)
ISOLATED_ALPHA = 1.00
ISOLATED_GAMMA = 1.00