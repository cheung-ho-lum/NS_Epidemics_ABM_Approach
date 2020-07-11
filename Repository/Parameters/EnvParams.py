NODE_TYPE_STATION = 'station'
NODE_TYPE_STREET = 'street' # street level, above ground, not the subway, etc.
ISOLATION_COUNTERMEASURE = 'isolation'
TESTING_COUNTERMEASURE = 'testing'
RECOMMENDATION_COUNTERMEASURE = 'warning'
AWARENESS_COUNTERMEASURE = 'awareness'
BOROUGH_BRONX = 'Bx'
BOROUGH_QUEENS = 'Q'
BOROUGH_BROOKLYN = 'Bk'
BOROUGH_MANHATTAN = 'M'
BOROUGH_STATEN_ISLAND = 'SI'
ADJUST_COMMUTERS_BY_FLOW = False
# Researcher-Adjustable
# These numbers calculated based on flow adjustments based on residential neighborhoods
COMMUTER_RATIO_BRONX = 0.500
COMMUTER_RATIO_BROOKLYN = 0.500
COMMUTER_RATIO_MANHATTAN = 0.500
COMMUTER_RATIO_QUEENS = 0.500
# Recommended Hyper-parameters
ISOLATION_COUNTERMEASURE_START = 500

"""
# Recommended Hyper-parameters: NYC
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
CONTACT_MODIFIER = 0.22         # Use this to increase infection based on travel

# These numbers calculated based on flow adjustments based on residential neighborhoods
COMMUTER_RATIO_BRONX = 0.306
COMMUTER_RATIO_BROOKLYN = 0.355
COMMUTER_RATIO_MANHATTAN = 0.492
COMMUTER_RATIO_QUEENS = 0.274
# Recommended Hyper-parameters
ISOLATION_COUNTERMEASURE_START = 500
"""
"""
# Recommended Hyper-parameters: LONDON
# Researcher Adjustable Parameters
DEFAULT_BETA = 1.00     # Try to match infection rate when there is 0 exposure (i.e. zc 10007)
DEFAULT_ALPHA = 0.24    # About 4.1 days. This is about the only agreed upon number.
DEFAULT_GAMMA = 0.16   # About 6 days when left unchecked
INITIAL_REDUCTION_TIME = 7  #TODO: are these agent params or env params. hmm
FULL_REDUCTION_TIME = 60
STARTING_RATIO = 2.5
STARTING_PERCENTAGE = 10e-7     # Calibrates start to match known data
# Recommended Hyper-parameters
INITIAL_REDUCTION_TGT = 1.00   # Calibrates initial countermeasure effectiveness
FULL_REDUCTION_TGT = 0.60  # Calibrates steady state behavior
CONTACT_MODIFIER = 0.10         # Use this to increase infection based on travel

#(London's Default commuter ratio is 0.500)
# Recommended Hyper-parameters
ISOLATION_COUNTERMEASURE_START = 200

"""