# XGBoost_TBBE

### This is code for A XGBoost-Agent Based model in In-Play Betting on a Sports Betting Exchange dissertation 

It is the extended version from Multi-threaded BBE (Bristol Betting Exchange) integrated with Opinion Dynamics Platform (https://github.com/Guzelyte/TBBE_OD). 

This version integrated an agent called XGBoostbettingagent to the original 'betting_agents.py' file in the Application folder. This agent uses the model trained from https://github.com/ChawinT/XGBoost_ModelTraining to make the prediction. Moreover, this version also added a function called 'getXGboostTrainData' to 'session_stats.py' file to collects/gather data for XGboost model training. 

Basic steps for running the BBE (Bristol Betting Exchange): 
1. In config.py -> Initialize the agents list. Below is the example of agents list:
   agents = [('Agent_Opinionated_Random', 10), ('Agent_Opinionated_Leader_Wins', 10),
          ('Agent_Opinionated_Underdog', 10),('Agent_Opinionated_Back_Favourite',10),
          ('Agent_Opinionated_Linex', 10), ('Agent_Opinionated_Priviledged', 5),
          ('XGBoostBettingAgent', 5)]

   This will be the agnet that system use when running the simulation. 

2. In systems_constant.py defines parameters/settings of the simulations. Example of parameters  systems_constant.py:

   -> General
  #NUM_OF_SIMS = 1
  NUM_OF_SIMS = 1
  NUM_OF_COMPETITORS = 5
  NUM_OF_EXCHANGES = 1
  PRE_RACE_BETTING_PERIOD_LENGTH = 0
  IN_PLAY_CUT_OFF_PERIOD = 0
  SESSION_SPEED_MULTIPLIER = 1

  -> Exchange Attributes
  MIN_ODDS = 1.1
  MAX_ODDS = 20.00

  -> Event Attributes
  RACE_LENGTH = 500
  MIN_RACE_LENGTH = 400
  MAX_RACE_LENGTH = 4000


3. "RUN" the session -> run TBBE.py file. 

4. After the session finished, results will be available in data folder. Many result files will be generated. Please look at session_stats.py file for how each file is generated. 



### This github doens't contain data files due to a large files size. The training data can be collect from running sessions in https://github.com/ChawinT/XGBoost_TBBE using the setup in the dissertation. 

  

  





