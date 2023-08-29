### ~ THREADED BRISTOL BETTING EXCHANGE ~ ###

import sys, math, threading, time, queue, random, csv, config, pandas
from copy import deepcopy


from system_constants import *
from betting_agents import *
import numpy as np
from race_simulator import Simulator
from ex_ante_odds_generator import *
from exchange import Exchange
from message_protocols import *
from session_stats import *
from ODmodels import *


class Session:

    def __init__(self):
        # Initialise exchanges
        self.exchanges = {}
        self.exchangeOrderQs = {}
        self.exchangeThreads = []

        # Initialise betting agents
        self.bettingAgents = {}
        self.bettingAgentQs = {}
        self.bettingAgentThreads = []

        self.OpinionDynamicsPlatform = None

        # Needed attributes
        self.startTime = None
        self.numberOfTimesteps = None
        self.lengthOfRace = None
        self.event = threading.Event()
        self.endOfInPlayBettingPeriod = None
        self.winningCompetitor = None
        self.distances = None

        # Record keeping attributes
        self.tape = []
        self.priceRecord = {}
        self.spreads = {}
        self.opinion_hist = {'id': [], 'time': [], 'opinion': [], 'competitor': []}
        self.opinion_hist_l = {'id': [], 'time': [], 'opinion': [], 'competitor': []}
        self.opinion_hist_e = {'id': [], 'time': [], 'opinion': [], 'competitor': []}
        self.opinion_hist_g = {'id': [], 'time': [], 'opinion': [], 'competitor': []}
        self.opinion_hist_s = {'id': [], 'time': [], 'opinion': [], 'competitor': []}
        self.competitor_odds = {'time': [], 'odds': [], 'competitor': []}
        self.competitor_distances = {'time': [], 'distance': [], 'competitor': []}

        self.generateRaceData()
        self.initialiseThreads()

    def exchangeLogic(self, exchange, exchangeOrderQ):
        """
        Logic for thread running the exchange
        """
        #print("EXCHANGE " + str(exchange.id) + " INITIALISED...")
        self.event.wait()
        # While event is running, run logic for exchange

        competitor_odds = {'time': [], 'odds': [], 'competitor': []}

        while self.event.isSet():
            timeInEvent = (time.time() - self.startTime) / SESSION_SPEED_MULTIPLIER
            try: order = exchangeOrderQ.get(block=False)
            except: continue

            marketUpdates = {}
            for i in range(NUM_OF_EXCHANGES):
                marketUpdates[i] = self.exchanges[i].publishMarketState(timeInEvent)

            if timeInEvent < self.endOfInPlayBettingPeriod:
                self.OpinionDynamicsPlatform.initiate_conversations(timeInEvent)
                self.OpinionDynamicsPlatform.update_opinions(timeInEvent, marketUpdates)

            else:
                self.OpinionDynamicsPlatform.settle_opinions(self.winningCompetitor)



            (transactions, markets) = exchange.processOrder(timeInEvent, order)

            if transactions != None:
                for id, q in self.bettingAgentQs.items():
                    update = exchangeUpdate(transactions, order, markets)
                    q.put(update)


    def agentLogic(self, agent, agentQ):
        """
        Logic for betting agent threads
        """
        #print("AGENT " + str(agent.id) + " INITIALISED...")
        # Need to have pre-event betting period
        self.event.wait()
        # Whole event is running, run logic for betting agents
        while self.event.isSet():
            time.sleep(0.01)
            timeInEvent = (time.time() - self.startTime) / SESSION_SPEED_MULTIPLIER
            order = None
            trade = None


            while agentQ.empty() is False:
                qItem = agentQ.get(block = False)
                if qItem.protocolNum == EXCHANGE_UPDATE_MSG_NUM:
                    for transaction in qItem.transactions:
                        if transaction['backer'] == agent.id: agent.bookkeep(transaction, 'Backer', qItem.order, timeInEvent)
                        if transaction['layer'] == agent.id: agent.bookkeep(transaction, 'Layer', qItem.order, timeInEvent)

                elif qItem.protocolNum == RACE_UPDATE_MSG_NUM:
                    agent.observeRaceState(qItem.timestep, qItem.compDistances)
                else:
                    print("INVALID MESSAGE")



            marketUpdates = {}
            for i in range(NUM_OF_EXCHANGES):
                marketUpdates[i] = self.exchanges[i].publishMarketState(timeInEvent)

            agent.respond(timeInEvent, marketUpdates, trade)
            order = agent.getorder(timeInEvent, marketUpdates)


            if agent.id == 0:
                for i in range(NUM_OF_COMPETITORS):
                    self.competitor_odds['time'].append(timeInEvent)
                    self.competitor_odds['competitor'].append(i)
                    if marketUpdates[0][i]['backs']['n'] > 0:
                        self.competitor_odds['odds'].append(marketUpdates[0][i]['backs']['best'])
                    else:
                        self.competitor_odds['odds'].append(marketUpdates[0][i]['backs']['worst'])

                    self.competitor_distances['competitor'].append(i)
                    self.competitor_distances['time'].append(timeInEvent)
                    if len(agent.currentRaceState) == 0:
                        self.competitor_distances['distance'].append(0)
                    else:
                        self.competitor_distances['distance'].append(agent.currentRaceState[i])


            self.opinion_hist['id'].append(agent.id)
            self.opinion_hist['time'].append(timeInEvent)
            self.opinion_hist['opinion'].append(agent.opinion)
            self.opinion_hist['competitor'].append(OPINION_COMPETITOR)

            self.opinion_hist_e['id'].append(agent.id)
            self.opinion_hist_e['time'].append(timeInEvent)
            self.opinion_hist_e['opinion'].append(agent.event_opinion)
            self.opinion_hist_e['competitor'].append(OPINION_COMPETITOR)

            self.opinion_hist_l['id'].append(agent.id)
            self.opinion_hist_l['time'].append(timeInEvent)
            self.opinion_hist_l['opinion'].append(agent.local_opinion)
            self.opinion_hist_l['competitor'].append(OPINION_COMPETITOR)

            self.opinion_hist_g['id'].append(agent.id)
            self.opinion_hist_g['time'].append(timeInEvent)
            self.opinion_hist_g['opinion'].append(agent.global_opinion)
            self.opinion_hist_g['competitor'].append(OPINION_COMPETITOR)

            self.opinion_hist_s['id'].append(agent.id)
            self.opinion_hist_s['time'].append(timeInEvent)
            self.opinion_hist_s['opinion'].append(agent.strategy_opinion)
            self.opinion_hist_s['competitor'].append(OPINION_COMPETITOR)

            if order != None:

                if TBBE_VERBOSE:
                    print(order)
                agent.numOfBets = agent.numOfBets + 1
                self.exchangeOrderQs[order.exchange].put(order)


       # print("ENDING AGENT " + str(agent.id))
        return 0

    def populateMarket(self):
        """
        Populate market with betting agents as specified in config file
        """
        def initAgent(name, quantity, id):

            uncertainty = 1.0

            local_opinion = 1/ NUM_OF_COMPETITORS

            #
            # if name == 'Test': return Agent_Test(id, name, self.lengthOfRace, self.endOfInPlayBettingPeriod)
            # if name == 'Random': return Agent_Random(id, name, self.lengthOfRace, self.endOfInPlayBettingPeriod)
            # if name == 'Leader_Wins': return Agent_Leader_Wins(id, name, self.lengthOfRace, self.endOfInPlayBettingPeriod)
            # if name == 'Underdog': return Agent_Underdog(id, name, self.lengthOfRace, self.endOfInPlayBettingPeriod)
            # if name == 'Back_Favourite': return Agent_Back_Favourite(id, name, self.lengthOfRace, self.endOfInPlayBettingPeriod)
            # if name == 'Linex': return Agent_Linex(id, name, self.lengthOfRace, self.endOfInPlayBettingPeriod)
            # if name == 'Arbitrage': return Agent_Arbitrage(id, name, self.lengthOfRace, self.endOfInPlayBettingPeriod)
            # if name == 'Arbitrage2': return Agent_Arbitrage2(id, name, self.lengthOfRace, self.endOfInPlayBettingPeriod)
            # if name == 'Priveledged': return Agent_Priveledged(id, name, self.lengthOfRace, self.endOfInPlayBettingPeriod)

            if name == 'Agent_Opinionated_Random': return Agent_Opinionated_Random(id, name, self.lengthOfRace, self.endOfInPlayBettingPeriod, 0, local_opinion, uncertainty, MIN_OP, MAX_OP )
            if name == 'Agent_Opinionated_Leader_Wins': return Agent_Opinionated_Leader_Wins(id, name, self.lengthOfRace, self.endOfInPlayBettingPeriod, 0, local_opinion, uncertainty, MIN_OP, MAX_OP )
            if name == 'Agent_Opinionated_Underdog': return Agent_Opinionated_Underdog(id, name, self.lengthOfRace, self.endOfInPlayBettingPeriod, 0, local_opinion, uncertainty, MIN_OP, MAX_OP)
            if name == "Agent_Opinionated_Back_Favourite": return Agent_Opinionated_Back_Favourite(id, name, self.lengthOfRace, self.endOfInPlayBettingPeriod, 0, local_opinion, uncertainty, MIN_OP, MAX_OP)
            if name == 'Agent_Opinionated_Linex': return Agent_Opinionated_Linex(id, name, self.lengthOfRace, self.endOfInPlayBettingPeriod, 0, local_opinion,uncertainty, MIN_OP, MAX_OP)

            if name == 'Agent_Opinionated_Priviledged': return Agent_Opinionated_Priviledged(id, name, self.lengthOfRace, self.endOfInPlayBettingPeriod, 1, local_opinion, uncertainty, MIN_OP, MAX_OP)
            if name == 'XGBoostBettingAgent': return XGBoostBettingAgent(id, name, self.lengthOfRace, self.endOfInPlayBettingPeriod, 0, local_opinion,uncertainty, MIN_OP, MAX_OP)


        id = 0
        for agent in config.agents:
            type = agent[0]
            for i in range(agent[1]):
                self.bettingAgents[id] = initAgent(agent[0], agent[1], id)
                id = id + 1

    def initialiseExchanges(self):
        """
        Initialise exchanges, returns list of exchange objects
        """
        for i in range(NUM_OF_EXCHANGES):
            self.exchanges[i] = Exchange(i, NUM_OF_COMPETITORS) # NUM_OF_COMPETITORS may be changed to list of competitor objects that are participating
            self.exchangeOrderQs[i] = queue.Queue()

    def initialiseBettingAgents(self):
        """
        Initialise betting agents
        """
        self.populateMarket()
        self.OpinionDynamicsPlatform = OpinionDynamicsPlatform(list(self.bettingAgents.values()), MODEL_NAME)
        print("initializating")
        #print(list(self.bettingAgents.values()))
        # Create threads for all betting agents that wait until event session
        # has started
        for id, agent in self.bettingAgents.items():
            self.bettingAgentQs[id] = queue.Queue()
            thread = threading.Thread(target = self.agentLogic, args = [agent, self.bettingAgentQs[id]])
            self.bettingAgentThreads.append(thread)


    def updateRaceQ(self, timestep):
        """
        Read in race data and update agent queues with competitor distances at timestep
        """
        with open(RACE_DATA_FILENAME, 'r') as file:
            reader = csv.reader(file)
            r = [row for index, row in enumerate(reader) if index == timestep]
        time = r[0][0]
        compDistances = {}
        for c in range(NUM_OF_COMPETITORS):
            compDistances[c] = float(r[0][c+1])

        # Create update
        update = raceUpdate(time, compDistances)

        for id, q in self.bettingAgentQs.items():
            q.put(update)

    def preRaceBetPeriod(self):
        print("Start of pre-race betting period, lasting " + str(PRE_RACE_BETTING_PERIOD_LENGTH))
        time.sleep(PRE_RACE_BETTING_PERIOD_LENGTH / SESSION_SPEED_MULTIPLIER)
        print("End of pre-race betting period")
        # marketUpdates = {}
        # for id, ex in exchanges.items():
        #     timeInEvent = time.time() - startTime
        #     print("Exchange " + str(id) + " markets: ")
        #     print(exchanges[id].publishMarketState(timeInEvent))


    def eventSession(self, simulationId):
        """
        Set up and management of race event
        """

        # Record start time
        self.startTime = time.time()

        # Start exchange threads
        for id, exchange in self.exchanges.items():
            thread = threading.Thread(target = self.exchangeLogic, args = [exchange, self.exchangeOrderQs[id]])
            self.exchangeThreads.append(thread)

        for thread in self.exchangeThreads:
            thread.start()

        # Start betting agent threads
        for thread in self.bettingAgentThreads:
            thread.start()

        # Initialise event
        self.event.set()

        time.sleep(0.01)

        # Pre-race betting period
        self.preRaceBetPeriod()


        # have loop which runs until competitor has won race
        i = 0
        while(i < self.numberOfTimesteps):
            self.updateRaceQ(i+1)
            i = i+1
            if TBBE_VERBOSE: print(i)
            print(i)
            time.sleep(1 / SESSION_SPEED_MULTIPLIER)





        # End event
        self.event.clear()

        # Close threads
        for thread in self.exchangeThreads: thread.join()
        for thread in self.bettingAgentThreads: thread.join()

        print("Simulation complete")

        print("Writing data....")
        for id, ex in self.exchanges.items():
            for orderbook in ex.compOrderbooks:
                for trade in orderbook.tape:
                    #print(trade)
                    self.tape.append(trade)

        # Settle up all transactions over all exchanges
        for id, ex in self.exchanges.items():
            ex.settleUp(self.bettingAgents, self.winningCompetitor)

        # for id, exchange in exchanges.items():
        #     exchange.tapeDump('transactions.csv', 'a', 'keep')

        for id, agent in self.bettingAgents.items():
            print("Agent " + str(id) + "\'s final balance: " + str(agent.balance)+ " : "+str(agent.name))

        createstats(self.bettingAgents, simulationId, self.tape, self.priceRecord, self.spreads, self.competitor_distances)

    def initialiseThreads(self):
        self.initialiseExchanges()
        self.initialiseBettingAgents()

    def generateRaceData(self):
        # Create race event data
        race = Simulator(NUM_OF_COMPETITORS)

        compPool = deepcopy(race.competitors)
        raceAttributes = deepcopy(race.race_attributes)


        # create simulations for procurement of ex-ante odds for priveledged betters
        createExAnteOdds(compPool, raceAttributes)

        race.run("core")

        self.numberOfTimesteps = race.numberOfTimesteps
        self.lengthOfRace = race.race_attributes.length
        self.winningCompetitor = race.winner
        self.distances = race.raceData
        self.endOfInPlayBettingPeriod = race.winningTimestep - IN_PLAY_CUT_OFF_PERIOD


        createInPlayOdds(self.numberOfTimesteps)






class BBE(Session):
    def __init__(self):
        self.session = None
        return


    # MAIN LOOP
    # argFuncf is an optional function which sets up a new session (takes in a session)
    def runSession(self, argFunc=None):
        # Simulation attributes
        currentSimulation = 0
        ####################

        # set things up
        # have while loop for running multiple races
        # within loop instantiate competitors into list
        # run simulation and matching engine
        while currentSimulation < NUM_OF_SIMS:
            simulationId = "Simulation: " + str(currentSimulation)
            # Start up thread for race on which all other threads will wait
            self.session = Session()
            if argFunc:
                argFunc(self.session)
            self.session.eventSession(currentSimulation)

            currentSimulation = currentSimulation + 1

        # Opinion Dynamics results:

        opinion_hist_df = pandas.DataFrame.from_dict(self.session.opinion_hist)
        opinion_hist_df.to_csv('opinions.csv', index=False)

        opinion_hist_df_l = pandas.DataFrame.from_dict(self.session.opinion_hist_l)
        opinion_hist_df_l.to_csv('opinions_l.csv', index=False)

        opinion_hist_df_g = pandas.DataFrame.from_dict(self.session.opinion_hist_g)
        opinion_hist_df_g.to_csv('opinions_g.csv', index=False)

        opinion_hist_df_e = pandas.DataFrame.from_dict(self.session.opinion_hist_e)
        opinion_hist_df_e.to_csv('opinions_e.csv', index=False)

        competitor_odds_df = pandas.DataFrame.from_dict(self.session.competitor_odds)
        competitor_odds_df.to_csv('competitor_odds.csv', index=False)

        competitor_distances_df = pandas.DataFrame.from_dict(self.session.competitor_distances)
        competitor_distances_df.to_csv('competitor_distances.csv', index=False)
        #print(competitor_distances_df)

        opinion_hist_s_df = pandas.DataFrame.from_dict(self.session.opinion_hist_s)
        opinion_hist_s_df.to_csv('opinion_hist_s.csv', index=False)


if __name__ == "__main__":
    import time

    start = time.time()
    # random.seed(26)
    # np.random.seed(26)
    print('Running')
    bbe = BBE()
    print('Running')
    bbe.runSession()
    end = time.time()
    print('Time taken: ', end - start)

