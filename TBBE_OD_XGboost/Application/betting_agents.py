### ~ THREADED BRISTOL BETTING EXCHANGE ~ ###

'''
Page 56 - The Perfect Bet
Strategy by Benter -> Find predicted odds then combine with markets as markets may contain privileged infomation

Should be stock pool of betting agents representing normal civilian bettors (eg. with range from less to more privileged info - recreational and insiders (eg. knowing diet / jockey strat))


'''

import sys, math, threading, time, queue, random, csv, config, random, operator
from message_protocols import Order
from system_constants import *
from ex_ante_odds_generator import *
import xgboost as xgb
from xgboost import DMatrix
import pandas as pd 


class BettingAgent:
    def __init__(self, id, name, lengthOfRace, endOfInPlayBettingPeriod, influenced_by_opinions, local_opinion,
                 uncertainty, lower_op_bound,
                 upper_op_bound, exchange=None):
        self.id = id
        self.name = name
        self.balance = 100000000
        self.liability = 0  # Amount that bettor is liable for if bettor lays winner
        self.availableBalance = self.balance
        self.orders = []
        self.amountFromOrders = 0
        self.amountFromTransactions = 0
        self.numOfBets = 0  # Number of bets live on BBE
        self.exchange = random.randint(0, NUM_OF_EXCHANGES - 1)
        self.endOfInPlayBettingPeriod = endOfInPlayBettingPeriod
        self.bettingPeriod = True
        self.trades = []

        self.stakeLower = 15
        self.stakeHigher = 15

        # race details
        self.lengthOfRace = lengthOfRace
        self.raceStarted = False
        self.raceTimestep = 0
        self.currentRaceState = {}
        self.raceHistoryDists = {}

        self.omega = random.uniform(0, 1)  # 'influenced_by_opinions' bettors bias weight they put on opinion vs their coded strategy when
        # betting.
        self.chosen_competitor = -1
        self.opinion = 1/NUM_OF_COMPETITORS

        self.local_opinion = local_opinion  # opinion about OPINION_COMPETITOR between [0,1], where 0 means that
        # bettor is certain that OPINION_COMPETITOR will lose and 1 means that the bettor is certain OPINION_COMPETITOR
        # will win (can be interpreted as bettor opinion of prob of horse winning)

        self.global_opinion = 1/NUM_OF_COMPETITORS
        self.event_opinion = 1/NUM_OF_COMPETITORS
        self.strategy_opinion = 1/NUM_OF_COMPETITORS

        self.start_a1 = 0.8 # start weight for local_opinion
        self.start_a2 = 1 - self.start_a1 # start weight for global_opinion
        self.start_a3 = 0  # start weight for event_opinion

        self.strategy_weight = 0.5

        self.a1 = self.start_a1  # weight for local_opinion
        self.a2 = self.start_a2  # weight for global_opinion
        self.a3 = self.start_a3  # weight for event_opinion



        self.uncertainty = uncertainty  # uncertainty between [0, 2]
        self.lower_op_bound = lower_op_bound
        self.upper_op_bound = upper_op_bound
        self.lower_un_bound = 0
        self.upper_un_bound = 2

        self.opinionated = 0 # [0,1] values.  0 - agent does not share opinions, 1 - agent shares opinions (
        # 'Opionionated' bettors).
        self.influenced_by_opinions = influenced_by_opinions  # [0,1] values. 0 - agent shares opinions, but does not listen.
        # 1 - agent shares and listens to opinions
        self.in_conversation = 0

    def observeRaceState(self, timestep, compDistances):
        if self.raceStarted == False: self.raceStarted = True
        for id, dist in compDistances.items():
            self.currentRaceState[id] = dist
            if id not in self.raceHistoryDists:
                self.raceHistoryDists[id] = []
            self.raceHistoryDists[id].append(dist)
        self.raceTimestep = int(timestep)
        if int(timestep) >= self.endOfInPlayBettingPeriod:
            self.bettingPeriod = False


    def bookkeep(self, trade, type, order, time):
        orderType = self
        self.trades.append(trade)
        self.numOfBets = self.numOfBets - 1
        if type == 'Backer':
            self.amountFromTransactions += trade['stake']
            # self.availableBalance = self.availableBalance - trade['stake']
        if type == 'Layer':
            self.amountFromTransactions += (trade['odds'] * trade['stake']) + trade['stake']
            # self.availableBalance = self.availableBalance - (trade['odds'] * trade['stake']) + trade['stake']

        return None

    def respond(self, time, markets, trade):

        return None

    def set_opinion(self, updated_opinion):

        validated_update = updated_opinion

        if updated_opinion >= self.upper_op_bound:
            # set to upper bound
            validated_update = self.upper_op_bound
        elif updated_opinion <= self.lower_op_bound:
            # set to lower bound
            validated_update = self.lower_op_bound

        self.local_opinion = validated_update

    def set_uncertainty(self, updated_uncertainty):

        validated_update = updated_uncertainty

        if updated_uncertainty >= self.upper_un_bound:
            # set to upper bound
            validated_update = self.upper_un_bound
        elif updated_uncertainty <= self.lower_un_bound:
            # set to lower bound
            validated_update = self.lower_un_bound

        self.uncertainty = validated_update


# --- AGENTS OF THE BETTING POOL BELOW --- #
# on initialisation will be given an exchange to operate on

class Agent_Opinionated_Random(BettingAgent):

    def __init__(self, id, name, lengthOfRace, endOfInPlayBettingPeriod, influenced_by_opinions, local_opinion,
                 uncertainty, lower_op_bound,
                 upper_op_bound):
        BettingAgent.__init__(self, id, name, lengthOfRace, endOfInPlayBettingPeriod, influenced_by_opinions,
                              local_opinion, uncertainty, lower_op_bound,
                              upper_op_bound)
        self.opinionated = 1
        self.name = 'Agent_Opinionated_Random'

    def getorder(self, time, markets):
        order = None
        if len(self.orders) > 0:
            order = self.orders.pop()

        return order

    def respond(self, time, markets, trade):
        order = None

        if self.bettingPeriod == False: return None
        r = random.randint(0, 10)
        if (r == 0):
            e = random.randint(0, NUM_OF_EXCHANGES - 1)
            # b = random.randint(0, 1)
            delta = b = random.randint(-1, 1)

            if self.chosen_competitor == -1:
                c = random.randint(0, NUM_OF_COMPETITORS - 1)
                self.chosen_competitor = c

                if self.chosen_competitor == OPINION_COMPETITOR:
                    self.local_opinion = random.uniform(1 / NUM_OF_COMPETITORS, 1)
                else:
                    self.local_opinion = random.uniform(0, 1 / NUM_OF_COMPETITORS)

            else:
                c = self.chosen_competitor

            #print("Component", c)


            if(b == 0):
                quoteodds = MIN_ODDS
                if markets[e][c]['lays']['best'] is not None:
                    quoteodds = markets[e][c]['lays']['best'] + delta
                    order = Order(e, self.id, c, 'Back', min(MAX_ODDS, max(MIN_ODDS, quoteodds)), random.randint(self.stakeLower, self.stakeHigher), markets[e][c]['QID'], time)
                    #print("BACK MADE BY AGENT " + str(self.id)+"   "+str(c))
            else:
                quoteodds = MAX_ODDS
                if markets[e][c]['backs']['best'] is not None:
                    quoteodds = markets[e][c]['backs']['best'] + delta
                    order = Order(e, self.id, c, 'Lay', min(MAX_ODDS, max(MIN_ODDS, quoteodds)), random.randint(self.stakeLower, self.stakeHigher), markets[e][c]['QID'], time)
                    #print("LAY MADE BY AGENT " + str(self.id)+"   "+str(c))

        if order != None:
            if(order.direction == 'Back'):
                liability = self.amountFromOrders + order.stake
                if liability > self.balance: return
                else:
                    self.orders.append(order)
                    self.amountFromOrders = liability

            elif(order.direction == 'Lay'):
                liability = self.amountFromOrders + ((order.stake * order.odds) - order.stake)
                if liability > self.balance: return
                else:
                    self.orders.append(order)
                    self.amountFromOrders = liability


class Agent_Opinionated_Leader_Wins(BettingAgent):
    # This betting agent's view of the race outcome is that whichever competitor
    # that is currently in the lead after random number of timesteps between 5, 15
    # will win and will bet one better
    def __init__(self, id, name, lengthOfRace, endOfInPlayBettingPeriod, influenced_by_opinions, local_opinion,
                 uncertainty, lower_op_bound,
                 upper_op_bound):
        BettingAgent.__init__(self, id, name, lengthOfRace, endOfInPlayBettingPeriod, influenced_by_opinions,
                              local_opinion, uncertainty, lower_op_bound,
                              upper_op_bound)
        self.bettingTime = random.randint(5, 15)
        self.bettingInterval = 2

            # random.randint(2,10)
        self.opinionated = 1
        self.name = 'Agent_Opinionated_Leader_Wins'

    def getorder(self, time, markets):
        order = None
        if len(self.orders) > 0:
            order = self.orders.pop()
        return order


    def respond(self, time, markets, trade):

        if self.bettingPeriod == False: return None
        order = None
        if self.raceStarted == False: return order

        if self.bettingTime <= self.raceTimestep and self.raceTimestep % self.bettingInterval == 0:

            sortedComps = sorted((self.currentRaceState.items()), key=operator.itemgetter(1))
            compInTheLead = int(sortedComps[len(sortedComps) - 1][0])

            if compInTheLead != self.chosen_competitor:

                if compInTheLead == OPINION_COMPETITOR:
                    self.local_opinion = random.uniform(1/NUM_OF_COMPETITORS, 1)
                else:
                    self.local_opinion = random.uniform(0, 1/NUM_OF_COMPETITORS)

            self.chosen_competitor = compInTheLead

            if markets[self.exchange][compInTheLead]['backs']['n'] > 0:
                quoteodds = max(MIN_ODDS, markets[self.exchange][compInTheLead]['backs']['best'] - 0.1)
            else:
                quoteodds = markets[self.exchange][compInTheLead]['backs']['worst']
            order = Order(self.exchange, self.id, compInTheLead, 'Back', quoteodds, random.randint(self.stakeLower, self.stakeHigher), markets[self.exchange][compInTheLead]['QID'], time)



        if order != None:
            if(order.direction == 'Back'):
                liability = self.amountFromOrders + order.stake
                if liability > self.balance: return
                else:
                    self.orders.append(order)
                    self.amountFromOrders = liability

            elif(order.direction == 'Lay'):
                liability = self.amountFromOrders + ((order.stake * order.odds) - order.stake)
                if liability > self.balance: return
                else:
                    self.orders.append(order)
                    self.amountFromOrders = liability


class Agent_Opinionated_Underdog(BettingAgent):
    # This betting agent's view of the race outcome is that the competitor in
    # second place will win if distance between it and the winner is small
    # if competitor in second place falls too far behind then agent will lay the
    # second place competitor and back the winning competitor
    def __init__(self, id, name, lengthOfRace, endOfInPlayBettingPeriod, influenced_by_opinions, local_opinion,
                 uncertainty, lower_op_bound,
                 upper_op_bound):
        BettingAgent.__init__(self, id, name, lengthOfRace, endOfInPlayBettingPeriod, influenced_by_opinions,
                              local_opinion, uncertainty, lower_op_bound,
                              upper_op_bound)
        self.bettingTime = random.randint(5, 15)
        self.threshold = random.randint(10, 35)
        self.compInTheLead = None
        self.compInSecond = None
        self.job = None
        self.opinionated = 1
        self.name = 'Agent_Opinionated_Underdog'

    def observeRaceState(self, timestep, compDistances):
        super().observeRaceState(timestep, compDistances)
        if self.bettingTime <= self.raceTimestep:
            sortedComps = sorted(self.currentRaceState.items(), key=operator.itemgetter(1))
            #print(sortedComps)
            # print(sortedComps[0][0])
            compInTheLead = sortedComps[len(sortedComps) - 1]
            #print("CompInTheLead",compInTheLead)
            compInSecond = sortedComps[len(sortedComps) - 2]

            if float(compInTheLead[1]) <= (float(compInSecond[1]) + float(self.threshold)) and compInTheLead[
                0] != self.compInTheLead:
                self.job = "back_underdog"
                self.compInTheLead = compInTheLead[0]
                self.compInSecond = compInSecond[0]

    def getorder(self, time, markets):
        order = None
        if len(self.orders) > 0:
            order = self.orders.pop()
        return order

    def respond(self, time, markets, trade):
        order = None


        if self.numOfBets >= 10 or self.raceStarted == False or self.bettingPeriod == False: return order
        if self.bettingTime <= self.raceTimestep:
            if self.job == 'back_underdog':
                if self.compInSecond != self.chosen_competitor:

                    if self.compInSecond == OPINION_COMPETITOR:
                        self.local_opinion = random.uniform(1/NUM_OF_COMPETITORS, 1)
                    else:
                        self.local_opinion = random.uniform(0, 1/NUM_OF_COMPETITORS)

                self.chosen_competitor = self.compInSecond

                if markets[self.exchange][self.compInSecond]['backs']['n'] > 0:
                    quoteodds = max(MIN_ODDS, markets[self.exchange][self.compInSecond]['backs']['best'] - 0.1)
                else:
                    quoteodds = markets[self.exchange][self.compInTheLead]['backs']['worst']

                order = Order(self.exchange, self.id, self.compInSecond, 'Back', quoteodds,
                              random.randint(self.stakeLower, self.stakeHigher),
                              markets[self.exchange][self.compInSecond]['QID'], time)
                self.job = "lay_leader"

            elif self.job == 'lay_leader':

                if markets[self.exchange][self.compInTheLead]['lays']['n'] > 0:

                    quoteodds = markets[self.exchange][self.compInTheLead]['lays']['best'] + 0.1
                else:
                    quoteodds = markets[self.exchange][self.compInTheLead]['lays']['worst']

                order = Order(self.exchange, self.id, self.compInTheLead, 'Lay', quoteodds,
                              random.randint(self.stakeLower, self.stakeHigher),
                              markets[self.exchange][self.compInTheLead]['QID'], time)
                self.job = None

        if order != None:
            if (order.direction == 'Back'):
                liability = self.amountFromOrders + order.stake
                if liability > self.balance:
                    return
                else:
                    self.orders.append(order)
                    self.amountFromOrders = liability

            elif (order.direction == 'Lay'):
                liability = self.amountFromOrders + ((order.stake * order.odds) - order.stake)
                if liability > self.balance:
                    return
                else:
                    self.orders.append(order)
                    self.amountFromOrders = liability


class Agent_Opinionated_Back_Favourite(BettingAgent):
    # This betting agent will place a back bet on the markets favourite to win (lowest back odds),
    # hence not having any priveledged view on which competitor will win the race
    # but instead relies on that information being ingrained in the market state
    def __init__(self, id, name, lengthOfRace, endOfInPlayBettingPeriod, influenced_by_opinions, local_opinion,
                 uncertainty, lower_op_bound,
                 upper_op_bound):
        BettingAgent.__init__(self, id, name, lengthOfRace, endOfInPlayBettingPeriod, influenced_by_opinions,
                              local_opinion, uncertainty, lower_op_bound,
                              upper_op_bound)
        self.marketsFave = None
        self.opinionated = 1
        self.name = 'Agent_Opinionated_Back_Favourite'

    def getorder(self, time, markets):
        order = None
        if len(self.orders) > 0:
            order = self.orders.pop()
        return order

    def respond(self, time, markets, trade):


        if self.bettingPeriod == False: return None
        order = None
        marketsFave = None
        lowestOdds = MAX_ODDS
        for comp in markets[self.exchange]:
            market = markets[self.exchange][comp]
            if market['backs']['best'] is not None:
                bestodds = market['backs']['best']
                if bestodds < lowestOdds:
                    lowestOdds = bestodds
                    marketsFave = comp

        if marketsFave == self.marketsFave:
            # market favourite hasn't changed therefore no need to back again
            return None

        elif marketsFave != None:
            self.marketsFave = marketsFave

            if self.marketsFave != self.chosen_competitor:

                if self.marketsFave == OPINION_COMPETITOR:
                    self.local_opinion = random.uniform(1/NUM_OF_COMPETITORS, 1)
                else:
                    self.local_opinion = random.uniform(0, 1/NUM_OF_COMPETITORS)

            self.chosen_competitor = self.marketsFave

            quoteodds = max(MIN_ODDS, lowestOdds - 0.1)
            order = Order(self.exchange, self.id, marketsFave, 'Back', quoteodds,
                          random.randint(self.stakeLower, self.stakeHigher), markets[self.exchange][marketsFave]['QID'],
                          time)

        if order != None:
            if (order.direction == 'Back'):
                liability = self.amountFromOrders + order.stake
                if liability > self.balance:
                    return
                else:
                    self.orders.append(order)
                    self.amountFromOrders = liability

            elif (order.direction == 'Lay'):
                liability = self.amountFromOrders + ((order.stake * order.odds) - order.stake)
                if liability > self.balance:
                    return
                else:
                    self.orders.append(order)
                    self.amountFromOrders = liability



class Agent_Opinionated_Linex(BettingAgent):
    # This betting agent's view of the race result stems from performing linear
    # extrapolation for each competitor to see which will finish first, calculated
    # winner is then backed whilst the worst competitor is layed, only starts
    # recording after random amount of time so as to avoid interference at start of race
    def __init__(self, id, name, lengthOfRace, endOfInPlayBettingPeriod, influenced_by_opinions, local_opinion,
                 uncertainty, lower_op_bound,
                 upper_op_bound):
        BettingAgent.__init__(self, id, name, lengthOfRace, endOfInPlayBettingPeriod, influenced_by_opinions,
                              local_opinion, uncertainty, lower_op_bound,
                              upper_op_bound)
        self.timeSinceLastBet = 0
        self.bettingInterval = random.randint(30, 60)
        self.recordingTime = random.randint(5, 15)
        self.n = random.randint(15, 25)
        self.predictedResults = {}
        self.predictedWinner = None
        self.predictedLoser = None
        self.injuredCompetitors = []
        self.job = None
        self.predicted = False
        self.opinionated = 1
        self.name = 'Agent_Opinionated_Linex'

    def predict(self):
        predictedWinnerTime = 10000
        predictedLoserTime = 0
        for i in range(NUM_OF_COMPETITORS):
            if i in self.injuredCompetitors: continue
            dists = self.raceHistoryDists[i]
            fromDist = float(dists[len(dists) - self.n])
            toDist = float(dists[-1])
            timeTaken = float(len(dists))
            avgSpeed = (toDist - fromDist) / timeTaken
            distLeft = self.lengthOfRace - toDist

            try:
                self.predictedResults[i] = distLeft / avgSpeed
            except:
                # competitor has been injured / cannot race further
                self.injuredCompetitors.append(i)
                continue
            if self.predictedWinner == None or self.predictedResults[i] < predictedWinnerTime:
                self.predictedWinner = i
                predictedWinnerTime = self.predictedResults[i]
            if self.predictedLoser == None or self.predictedResults[i] > predictedLoserTime:
                self.predictedLoser = i
                predictedLoserTime = self.predictedResults[i]
        ### Add print
        # print("Linex Result: ",self.predictedResults)
        # print("Linex loser: ",self.predictedLoser)
        # print("Linex winner: ",self.predictedWinner)
        self.predicted = True

    def observeRaceState(self, timestep, compDistances):
        super().observeRaceState(timestep, compDistances)
        if self.bettingPeriod == False: return

        if len(self.raceHistoryDists[0]) > (self.n + self.recordingTime) and self.predicted == False:
            self.predict()
            if self.predictedWinner != None:
                self.job = "back_pred_winner"

        if self.predicted == True:
            self.timeSinceLastBet = self.timeSinceLastBet + 1
            if self.timeSinceLastBet >= self.bettingInterval:
                self.predicted = False
                self.timeSinceLastBet = 0

    def getorder(self, time, markets):
        order = None
        if len(self.orders) > 0:
            order = self.orders.pop()
        return order

    def respond(self, time, markets, trade):


        order = None
        if self.predicted == False or self.bettingPeriod == False: return order


        if self.job == 'back_pred_winner':

            if self.predictedWinner != self.chosen_competitor:

                if self.predictedWinner == OPINION_COMPETITOR:
                    self.local_opinion = random.uniform(1/NUM_OF_COMPETITORS, 1)
                else:
                    self.local_opinion = random.uniform(0, 1/NUM_OF_COMPETITORS)

            self.chosen_competitor = self.predictedWinner

            if markets[self.exchange][self.predictedWinner]['backs']['n'] > 0:

                quoteodds = max(MIN_ODDS, markets[self.exchange][self.predictedWinner]['backs']['best'] - 0.1)
            else:

                quoteodds = markets[self.exchange][self.predictedWinner]['backs']['worst']

            order = Order(self.exchange, self.id, self.predictedWinner, 'Back', quoteodds,
                          random.randint(self.stakeLower, self.stakeHigher),
                          markets[self.exchange][self.predictedWinner]['QID'], time)
            self.job = "lay_pred_loser"

        elif self.job == 'lay_pred_loser':

            if markets[self.exchange][self.predictedLoser]['lays']['n'] > 0:
                quoteodds = markets[self.exchange][self.predictedLoser]['lays']['best'] + 0.1
            else:
                quoteodds = markets[self.exchange][self.predictedLoser]['lays']['worst']

            order = Order(self.exchange, self.id, self.predictedLoser, 'Lay', quoteodds,
                          random.randint(self.stakeLower, self.stakeHigher),
                          markets[self.exchange][self.predictedLoser]['QID'], time)
            self.job = None

        if order != None:
            if (order.direction == 'Back'):
                liability = self.amountFromOrders + order.stake
                if liability > self.balance:
                    return
                else:
                    # print("\n LINEX BACKS: ",order.odds)
                    self.orders.append(order)
                    self.amountFromOrders = liability

            elif (order.direction == 'Lay'):
                liability = self.amountFromOrders + ((order.stake * order.odds) - order.stake)
                if liability > self.balance:
                    return
                else:
                    # print("\n LINEX LAYS: ", order.odds)
                    self.orders.append(order)
                    self.amountFromOrders = liability



class Agent_Opinionated_Priviledged(BettingAgent):
    '''
    create reasonable ex ante odds for rest of bettors (no random till in play and then use best back/lay)
    when in play will be able to run one simulation every 10/15 time steps
    this will simulate snap decisions within in-play betting
    greater inefficiencies in in play betting markets because more data point all of which
    have Uncertainty
    '''

    def __init__(self, id, name, lengthOfRace, endOfInPlayBettingPeriod, influenced_by_opinions, local_opinion,
                 uncertainty, lower_op_bound,
                 upper_op_bound):
        BettingAgent.__init__(self, id, name, lengthOfRace, endOfInPlayBettingPeriod, influenced_by_opinions,
                              local_opinion, uncertainty, lower_op_bound,
                              upper_op_bound)
        self.exAnteOdds = getExAnteOdds(self.id)
        self.betPreRace = False
        self.updateInterval = 1
        self.stake = 10
        self.backDelta = 0.1
        self.layDelta = 0.1

        self.BidOdds = []
        self.LayOdds = []

        # plotting code below
        self.oddsData = []
        row = [self.raceTimestep]
        for i in range(len(self.exAnteOdds)):
            row.append(self.exAnteOdds[i])
        self.oddsData.append(row)

        self.competitor_odds = {'time': [], 'odds': [], 'competitor': []}


        self.opinionated = 1
        self.name = 'Agent_Opinionated_Priviledged'
        self.latest_odds = None




    def getExAnteOrder(self, time, markets):
        for i in range(len(self.exAnteOdds)):
            odds = self.exAnteOdds[i]
            direction = 'Back'
            if odds == MAX_ODDS:
                direction = 'Lay'
                if markets[self.exchange][i]['backs']['n'] > 0:
                    odds = markets[self.exchange][i]['backs']['best'] + self.layDelta
                else:
                    continue
            if direction == 'Back': odds = odds - self.backDelta
            order = Order(self.exchange, self.id, i, direction, max(MIN_ODDS, odds),
                          random.randint(self.stakeLower, self.stakeHigher), markets[self.exchange][i]['QID'], time)
            self.orders.append(order)
            # print("AGENT " + str(self.id) + ": " + str(order))

    def getInPlayOrder(self, time, markets):
        order = None

        for i in range(NUM_OF_COMPETITORS):
            self.competitor_odds['time'].append(time)
            self.competitor_odds['competitor'].append(i)
            if markets[0][i]['backs']['n'] > 0:
                self.competitor_odds['odds'].append(markets[0][i]['backs']['best'])
            else:
                self.competitor_odds['odds'].append(markets[0][i]['backs']['worst'])


        if (self.raceTimestep % self.updateInterval) == 0:

            odds = getInPlayOdds(self.raceTimestep, self.id)
            # plotting code
            row = [self.raceTimestep]
            for i in range(len(odds)):
                row.append(odds[i])
            self.oddsData.append(row)


            # print("AGENT ID: " + str(self.id) + " " + str(self.id) + " In Play Odds Pred: " + str(row))
            winner = None
            winnerOdds = MAX_ODDS

            if self.latest_odds is None:
                self.strategy_opinion = 1 / odds[OPINION_COMPETITOR]
                local_op = (1 - self.strategy_weight) * self.local_opinion + self.strategy_opinion * self.strategy_weight
                self.local_opinion = local_op
                self.opinion = self.a1 * self.local_opinion + self.a2 * self.global_opinion + self.a3 * self.event_opinion

            else:
                if odds[OPINION_COMPETITOR] != self.latest_odds[OPINION_COMPETITOR]:
                    self.strategy_opinion = 1 / odds[OPINION_COMPETITOR]
                    local_op = (1 - self.strategy_weight) * self.local_opinion + self.strategy_opinion * self.strategy_weight
                    self.local_opinion = local_op
                    self.opinion = self.a1 * self.local_opinion + self.a2 * self.global_opinion + self.a3 * self.event_opinion

            self.latest_odds = odds

            for i in range(len(odds)):

                quoteodds = odds[i]

                if i == OPINION_COMPETITOR:
                    c_local_opinion = self.local_opinion
                    c_global_opinion = self.global_opinion
                    c_event_opinion = self.event_opinion

                else:
                    c_local_opinion = (1 - self.local_opinion) / (NUM_OF_COMPETITORS-1)
                    c_global_opinion = (1 - self.global_opinion) / (NUM_OF_COMPETITORS-1)

                    if self.event_opinion == 1 or self.event_opinion == 0:
                        c_event_opinion = 1 - self.event_opinion
                    else:
                        if len(self.currentRaceState.values()) > 0:
                            total = 0
                            for c in self.currentRaceState.values():
                                total = total + (self.lengthOfRace / self.lengthOfRace - c) ** 2
                            c_event_opinion = (self.lengthOfRace / (self.lengthOfRace -
                                                                        self.currentRaceState[i])) ** 2 / total
                        else:
                            c_event_opinion = 1/NUM_OF_COMPETITORS

                c_opinion = self.a1 * c_local_opinion + self.a2 * c_global_opinion + self.a3 * c_event_opinion

                if c_opinion == 0:
                    back_opinionated_odds = 0
                else:
                    back_opinionated_odds = 1 / c_opinion

                lay_opinionated_odds = 1 - back_opinionated_odds

                direction = 'Back'
                if quoteodds == MAX_ODDS:
                    direction = 'Lay'
                    if markets[self.exchange][i]['backs']['best'] is not None:
                        quoteodds = markets[self.exchange][i]['backs']['best'] + self.layDelta
                        lay_odds = self.omega * lay_opinionated_odds + (1 - self.omega) * quoteodds
                        order = Order(self.exchange, self.id, i, direction, max(MIN_ODDS, lay_odds),
                                      random.randint(self.stakeLower, self.stakeHigher),
                                      markets[self.exchange][i]['QID'], time)
                    else:
                        continue
                elif markets[self.exchange][i]['backs']['best'] is not None:
                    if (quoteodds < markets[self.exchange][i]['backs']['best']):
                        quoteodds = quoteodds - self.backDelta
                        back_odds = self.omega * back_opinionated_odds + (1 - self.omega) * quoteodds
                        order = Order(self.exchange, self.id, i, direction, max(MIN_ODDS, back_odds),
                                      random.randint(self.stakeLower, self.stakeHigher),
                                      markets[self.exchange][i]['QID'], time)
                else:
                    quoteodds = quoteodds - self.backDelta
                    back_odds = self.omega * back_opinionated_odds + (1 - self.omega) * quoteodds
                    order = Order(self.exchange, self.id, i, direction, max(MIN_ODDS, back_odds),
                                  random.randint(self.stakeLower, self.stakeHigher), markets[self.exchange][i]['QID'],
                                  time)

                self.orders.append(order)

    def getorder(self, time, markets):
        order = None
        if len(self.orders) > 0:
            order = self.orders.pop()
        return order

    def respond(self, time, markets, trade):
        order = None
        if self.bettingPeriod == False: return order
        if self.raceStarted == False and self.betPreRace == False:
            self.getExAnteOrder(time, markets)
            self.betPreRace = True
        elif self.raceStarted == True:
            self.getInPlayOrder(time, markets)


#################
##
#XGBOOST Agent
##
#################

class XGBoostBettingAgent(BettingAgent):
    
    def __init__(self, id, name, lengthOfRace, endOfInPlayBettingPeriod, influenced_by_opinions, 
                 local_opinion, uncertainty, lower_op_bound, upper_op_bound):
        super().__init__(id, name, lengthOfRace, endOfInPlayBettingPeriod, influenced_by_opinions,
                         local_opinion, uncertainty, lower_op_bound, upper_op_bound)
        self.xgb_loaded_model = xgb.Booster()
        self.xgb_loaded_model.load_model('trained_xgboost_model.json')  # the trained XGBoost model
        self.bettingInterval = 2  
        self.bettingTime = random.randint(5, 15)
        self.name = 'XGBoostBettingAgent'

    def getorder(self, time, markets):
        order = None
        if len(self.orders) > 0:
            order = self.orders.pop()
        return order
    
    def make_decision(self, time, stake, distance, rank):
   # """Make a decision (bet/lay) based on the XGBoost model's prediction."""
        df = pd.DataFrame({
            'time': [time],
            'stake': [stake],
            'distance': [distance],
            'rank': [rank]
        })
        dmatrix_data = DMatrix(df)
        #print(df)
        prediction = self.xgb_loaded_model.predict(dmatrix_data)[0]  # get the first prediction value
        decision = 1 if prediction > 0.5 else 0
        if decision == 1:
            print("decision >>> ", decision)
        return decision

    # def make_decision(self, features):
    #     """Make a decision (bet/lay) based on the XGBoost model's prediction."""
    #     prediction = self.xgb_loaded_model.predict([features])
    #     return prediction[0]

    def respond(self, time, markets, trade):
        if self.bettingPeriod == False: return None
        order = None
        if self.raceStarted == False: return order

        if self.bettingTime <= self.raceTimestep and self.raceTimestep % self.bettingInterval == 0:
            sortedComps = sorted((self.currentRaceState.items()), key=operator.itemgetter(1))
            
            for rank, (competitor, distance) in enumerate(sortedComps):
                #print(time,distance,rank+1)
                decision = self.make_decision(time, 15,distance, rank+1)
                if decision == 1: ## Decision = back
                    if markets[self.exchange][competitor]['backs']['n'] > 0:
                        quoteodds = max(MIN_ODDS, markets[self.exchange][competitor]['backs']['best'] - 0.1)
                    else:
                        quoteodds = markets[self.exchange][competitor]['backs']['worst']

                    order = Order(self.exchange, self.id, competitor, 'Back', quoteodds, 
                                random.randint(self.stakeLower, self.stakeHigher), 
                                markets[self.exchange][competitor]['QID'], time)

                    if order.direction == 'Back':
                        liability = self.amountFromOrders + order.stake
                        if liability > self.balance:
                            continue
                        else:
                            self.orders.append(order)
                            self.amountFromOrders = liability

                elif decision == 0: ## Decision = lay 
                    if markets[self.exchange][competitor]['lays']['n'] > 0:
                        quoteodds = markets[self.exchange][competitor]['lays']['best'] + 0.1
                    else:
                        quoteodds = markets[self.exchange][competitor]['lays']['worst']

                    order = Order(self.exchange, self.id, competitor, 'Lay', quoteodds,
                                random.randint(self.stakeLower, self.stakeHigher),
                                markets[self.exchange][competitor]['QID'], time)

                    if order.direction == 'Lay':
                        liability = self.amountFromOrders + ((order.stake * order.odds) - order.stake)
                        if liability > self.balance:
                            continue
                        else:
                            self.orders.append(order)
                            self.amountFromOrders = liability

        return None

