# System constants used across BBE

# General
#NUM_OF_SIMS = 1
NUM_OF_SIMS = 1
NUM_OF_COMPETITORS = 5
NUM_OF_EXCHANGES = 1
PRE_RACE_BETTING_PERIOD_LENGTH = 0
IN_PLAY_CUT_OFF_PERIOD = 0
SESSION_SPEED_MULTIPLIER = 1

# Data Store Attributes
RACE_DATA_FILENAME = 'race_event_core.csv'

# Message Protocol Numbers
EXCHANGE_UPDATE_MSG_NUM = 1
RACE_UPDATE_MSG_NUM = 2

# Exchange Attributes
MIN_ODDS = 1.1
MAX_ODDS = 20.00

# Print-Outs
TBBE_VERBOSE = False
SIM_VERBOSE = False
EXCHANGE_VERBOSE = False

# Event Attributes
# average horse races are between 5 and 12 (1005 - 2414) furlongs or could go min - max (400 - 4000)
#RACE_LENGTH = 500
RACE_LENGTH = 500
MIN_RACE_LENGTH = 400
MAX_RACE_LENGTH = 4000

MIN_RACE_UNDULATION = 0
MAX_RACE_UNDULATION = 100

MIN_RACE_TEMPERATURE = 0
MAX_RACE_TEMPERATUE = 50

# Betting Agent Attributes
NUM_EX_ANTE_SIMS = 5
NUM_IN_PLAY_SIMS = 5



#OD models

MODEL_NAME = 'BC'
OPINION_COMPETITOR = 0 # Bettors will be expressing opinions about this competitor. Opinions are in the range of [0,1].

MAX_OP = 1
MIN_OP = 0

# intensity of interactions
mu = 0.2 # used for all models eg. 0.2
delta = 0.25 # used for Bounded Confidence Model eg. 0.1
lmda = 0.5 # used for Relative Disagreement Model eg. 0.1


