import sys, math, threading, time, queue, random, csv, config, random, operator
from message_protocols import Order
from system_constants import *
import pandas as pd 
# from ex_ante_odds_generator import *

# getExAnteOdds, getInPlayOdds


def recordPrices(timestep, exchanges, record):
    for id, ex in exchanges.items():
        compData = {}
        for orderbook in ex.compOrderbooks:
            ob = orderbook.backs.bestOdds
            ol = orderbook.lays.bestOdds

            if(ob == None and ol == None):
                compData[orderbook.competitorId] = MAX_ODDS
            elif(ob == None):
                compData[orderbook.competitorId] = ol
            elif(ol == None):
                compData[orderbook.competitorId] = ob
            else:
                print(ob)
                print(ol)
                print(orderbook.backs.market)
                print("BANG")
                print(orderbook.lays.market)
                qtyB = orderbook.backs.market[ob][0]
                qtyL = orderbook.lays.market[ol][0]

                microprice = ((ob * qtyL) + (ol * qtyB)) / (qtyB + qtyL)
                #if ob == None: ob = MAX_ODDS
                compData[orderbook.competitorId] = microprice

        record[timestep] = compData

def recordSpread(timestep, exchanges, record):
    for id, ex in exchanges.items():
        compData = {}
        for orderbook in ex.compOrderbooks:
            ob = orderbook.backs.bestOdds
            ol = orderbook.lays.bestOdds


            # if(ob == None and ol == None):
            #     compData[orderbook.competitorId] = None
            # elif(ob == None):
            #     compData[orderbook.competitorId] = None
            # elif(ol == None):
            #     compData[orderbook.competitorId] = None
            if(ob != None and ol != None):
                spread = abs((1/ob) - (1/ol))
                #if ob == None: ob = MAX_ODDS
                if spread != 0:
                    compData[orderbook.competitorId] = spread

        record[timestep] = compData

def price_histories(priceHistory, simId):
    history = []
    for id, items in priceHistory.items():
        history.append(items)

    rows = [ [k] + [ (MAX_ODDS if (z == None) else z) for c, z in v.items() ] for k, v in priceHistory.items() ]

    header = ["Time"]
    for c in range(NUM_OF_COMPETITORS):
        header.append(str(c))

    # print(priceHistory)
    print(rows)



    fileName = "price_histories_" + str(simId) + ".csv"
    with open(fileName, 'w', newline = '') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(rows)

def price_spread(spreadHistory, simId):

    rows = [ [k] + [ (MAX_ODDS if (z == None) else z) for c, z in v.items() ] for k, v in spreadHistory.items() ]

    header = ["Time"]
    for c in range(NUM_OF_COMPETITORS):
        header.append(str(c))

    # print(priceHistory)
    print(rows)

    fileName = "price_spreads_" + str(simId) + ".csv"
    with open(fileName, 'w', newline = '') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(rows)


def priv_bettor_odds(bettingAgents):
    privBettors = []
    for id, agent in bettingAgents.items():
        if agent.name == 'Priveledged' or agent.name=='Agent_Opinionated_Priviledged': privBettors.append(agent)

    oddsdata = {}
    for b in privBettors:
        oddsdata[b.id] = b.oddsData

    header = ["Time"]
    for c in range(NUM_OF_COMPETITORS):
        header.append(str(c))

    for b in privBettors:
        fileName = "comp_odds_by_" + str(b.id) + ".csv"
        with open(fileName, 'w', newline = '') as file:
            writer = csv.writer(file)
            writer.writerow(header)
            writer.writerows(b.oddsData)


def final_balances(bettingAgents, simId):
    bettors = []
    for id, agent in bettingAgents.items():
        bettors.append(agent)

    header = []
    for i in range(len(bettors)):
        header.append(str(i))

    data = []
    for i in range(len(bettors)):
        data.append(bettors[i].balance)
    
    fileName = "200_new_final_balance_" + str(simId) + ".csv"
    with open(fileName, 'w', newline = '') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerow(data)

    # for b in bettors:
    #     fileName = "final_balance_" + str(simId) + "_" + str(b.id) + ".csv"
    #     with open(fileName, 'w', newline = '') as file:
    #         writer = csv.writer(file)
    #         writer.writerow(header)
    #         writer.writerow(data)


def transactions(trades, simId):
    header = ["type", "time", "exchange", "competitor", "odds", "backer", "layer", "stake"]
    tape = []
    for val in trades:
        temp = []
        for i, v in val.items():
            temp.append(v)
        tape.append(temp)


    fileName = "transactions_" + str(simId) + ".csv"
    with open(fileName, 'w', newline = '') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        writer.writerows(tape)

##########

# def getBalance(bettingAgents):
#     bettors = []
#     for id, agent in bettingAgents.items():
#         bettors.append(agent)

#     balances = {}
#     for i, bettor in enumerate(bettors):
#         balances[i] = bettor.balance

#     return balances

# def getXGboostTrainData(trades, simId, bettingAgents, agentDistances):
#     balances = getBalance(bettingAgents)

#     # Compute the ranks for each competitor and time
#     agentDistances['rank'] = agentDistances.groupby('time')['distance'].rank(ascending=False, method='first').astype(int)
#     print(agentDistances)
#     new_header = ["type", "time", "exchange", "competitor", "odds", "agentID", "decision", "stake", "balance", "distance", "rank"]
#     tape = []
#     for val in trades:
#         competitor = val["competitor"]
#         time = val["time"]

#         epsilon = 1e-1
#         mask = (agentDistances['competitor'] == competitor) & (abs(agentDistances['time'] - time) < epsilon)
#         filtered_df = agentDistances[mask]
#         distance = filtered_df['distance'].values[0] if len(filtered_df) > 0 else 0 
#         rank = filtered_df['rank'].values[0] if len(filtered_df) > 0 else 0 

#         # For backer   
#         backer_balance = balances[val["backer"]]
#         backer_row = [val["type"], val["time"], val["exchange"], val["competitor"], val["odds"], val["backer"], "backer", val["stake"], backer_balance, distance, rank]
#         tape.append(backer_row)
#         # For layer
#         layer_balance = balances[val["layer"]]
#         layer_row = [val["type"], val["time"], val["exchange"], val["competitor"], val["odds"], val["layer"], "layer", val["stake"], layer_balance, distance, rank]
#         tape.append(layer_row)

#     fileName = "getXGBOOstTrainingData_" + str(simId) + ".csv"
#     with open(fileName, 'w', newline='') as file:
#         writer = csv.writer(file)
#         writer.writerow(new_header)
#         writer.writerows(tape)

def getBalance(bettingAgents):
    """
    Retrieve the balance for each betting agent.
    """
    bettors = [agent for _, agent in bettingAgents.items()]

    balances = {}
    for i, bettor in enumerate(bettors):
        balances[i] = bettor.balance

    return balances

def getXGboostTrainData(trades, simId, bettingAgents, agentDistances):
    """
    Process and format trade data for XGBoost training.
    :trades: List of trade data.
    :simId: Simulation ID.
    :bettingAgents: Dictionary of betting agents.
    :agentDistances: DataFrame containing distances for each competitor and time.
    """
    # Get the balances for each agent
    balances = getBalance(bettingAgents)

    # Compute the ranks for each competitor and time
    agentDistances['rank'] = agentDistances.groupby('time')['distance'].rank(ascending=False, method='first').astype(int)

    # Adjust the order of columns
    new_header = ["type","competitorID", "time", "exchange", "odds",  "agentID", "stake", "distance", "rank", "balance", "decision"]

    tape = [] # This will hold our final data rows
    for val in trades:
        competitor = val["competitor"]
        time = val["time"]

        # Define a tolerance level to match times approximately
        tolerance = 1e-1
        
        # Filter the distances dataframe for matching competitor and times
        mask = (agentDistances['competitor'] == competitor) & (abs(agentDistances['time'] - time) < tolerance)
        filtered_df = agentDistances[mask]
        distance = filtered_df['distance'].values[0] if len(filtered_df) > 0 else 0 
        rank = filtered_df['rank'].values[0] if len(filtered_df) > 0 else 0 

        # Extract and format data for backer
        backer_balance = balances[val["backer"]]
        backer_row = [val["type"], val["competitor"], val["time"], val["exchange"], val["odds"], val["backer"], val["stake"], distance, rank, backer_balance, "backer"]
        tape.append(backer_row)

        # Extract and format data for layer
        layer_balance = balances[val["layer"]]
        layer_row = [val["type"], val["competitor"], val["time"], val["exchange"], val["odds"],  val["layer"], val["stake"], distance, rank, layer_balance, "layer"]
        tape.append(layer_row)

    # Write the final data rows to a CSV file
    fileName = "getXGBOOstTrainingData_" + str(simId) + ".csv"
    with open(fileName, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(new_header)
        writer.writerows(tape)


def createstats(bettingAgents, simId, trades, priceHistory, spreadHistory,AgentDistance):
    #priv_bettor_odds(bettingAgents)
    final_balances(bettingAgents, simId)
    #price_histories(priceHistory, simId)
    #price_spread(spreadHistory, simId)
    transactions(trades, simId)
    #getTrainingData(trades, simId,bettingAgents)
    getXGboostTrainData(trades, simId,bettingAgents,pd.DataFrame.from_dict(AgentDistance))




# def getTrainingData2(trades, simId, bettingAgents,agentDistances):
#     balances = final_balances2(bettingAgents)
#     new_header = ["type", "time", "exchange", "competitor", "odds", "agentID", "decision", "stake", "balance","distance"]
#     tape = []
#     for val in trades:

#         competitor = val["competitor"]
#         time = val["time"]
#         # print(competitor,time)
#         # print(agentDistances['time'])
#         # distance = agentDistances[(agentDistances['competitor'] == competitor) & (agentDistances['time'] == time)]['distance'].values
#         # print(distance)
#         # distance = distance[0] if len(distance) > 0 else 0
#         epsilon = 1e-2

#         # Filter for rows where the competitor matches and the difference between the times is less than epsilon
#         mask = (agentDistances['competitor'] == competitor) & (abs(agentDistances['time'] - time) < epsilon)
#         print(time)

#         print(abs(agentDistances['time'] - time))
#         distance = agentDistances[mask]['distance'].values
#         distance = distance[0] if len(distance) > 0 else 0 

#         # For backer   
#         backer_balance = balances[val["backer"]]
#         backer_row = [val["type"], val["time"], val["exchange"], val["competitor"], val["odds"], val["backer"], "backer", val["stake"], backer_balance,distance]
#         tape.append(backer_row)
#         # For layer
#         layer_balance = balances[val["layer"]]
#         layer_row = [val["type"], val["time"], val["exchange"], val["competitor"], val["odds"], val["layer"], "layer", val["stake"], layer_balance,distance]
#         tape.append(layer_row)

#     fileName = "getTrainingData2" + str(simId) + ".csv"
#     with open(fileName, 'w', newline='') as file:
#         writer = csv.writer(file)
#         writer.writerow(new_header)
#         writer.writerows(tape)
# def getTrainingData(trades, simId, bettingAgents):
#     balances = final_balances2(bettingAgents)
#     new_header = ["type", "time", "exchange", "competitor", "odds", "agentID", "decision", "stake", "balance"]
#     tape = []
#     for val in trades:
#         # For backer
#         backer_balance = balances[val["backer"]]
#         backer_row = [val["type"], val["time"], val["exchange"], val["competitor"], val["odds"], val["backer"], "backer", val["stake"], backer_balance]
#         tape.append(backer_row)
#         # For layer
#         layer_balance = balances[val["layer"]]
#         layer_row = [val["type"], val["time"], val["exchange"], val["competitor"], val["odds"], val["layer"], "layer", val["stake"], layer_balance]
#         tape.append(layer_row)

    # fileName = "getTrainingData" + str(simId) + ".csv"
    # with open(fileName, 'w', newline='') as file:
    #     writer = csv.writer(file)
    #     writer.writerow(new_header)
    #     writer.writerows(tape)

