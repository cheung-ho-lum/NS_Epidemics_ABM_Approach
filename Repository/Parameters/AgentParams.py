STATUS_SUSCEPTIBLE = 'Susceptible'
STATUS_EXPOSED = 'Exposed'
STATUS_INFECTED = 'Infected'
STATUS_RECOVERED = 'Recovered'
MAP_LOCATION_JUNCTION_BLVD = 451 #TODO: wait... these are EnvParams
MAP_LOCATION_55_ST = 62
MAP_LOCATION_98_BEACH = 201
MAP_LOCATION_BRIGHTON_BEACH = 55
MAP_LOCATION_WUHAN_TIANHE = 3376
MAP_LOCATION_ATOCHA = 18000
MAP_LOCATION_COLMENAR_VIEJO = 17005
GLOBAL_FACTOR_NYC_SUBWAY = 0.7 #TODO: unused?
# Researcher Adjustable
#try to match r0 = 5.7 for wuhan
DEFAULT_BETA = 1.14  # This is the real question. (R0 =  beta/gamma btw)
DEFAULT_ALPHA = 0.24  # About 5 days. This is about the only agreed upon number.
DEFAULT_GAMMA = 0.20  # About 5 days infectious and not removed
