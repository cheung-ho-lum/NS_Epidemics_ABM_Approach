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
# Researcher Adjustable Parameters
DEFAULT_BETA = 1.00     # Try to match infection rate when there is 0 exposure (i.e. zc 10007)
DEFAULT_ALPHA = 0.24    # About 4.1 days. This is about the only agreed upon number.
DEFAULT_GAMMA = 0.16   # About 6 days when left unchecked
INITIAL_REDUCTION_TIME = 7  #TODO: are these agent params or env params. hmm
FULL_REDUCTION_TIME = 60
STARTING_RATIO = 2.5
STARTING_PERCENTAGE = 10e-7     # Calibrates start to match known data
# Recommended Hyper-parameters
INITIAL_REDUCTION_TGT = 1.50    # Calibrates initial countermeasure effectiveness
FULL_REDUCTION_TGT = 0.60  # Calibrates steady state behavior
CONTACT_MODIFIER = 0.051         # Use this to increase infection based on travel

