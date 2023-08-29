class XGBoostBettingAgent(BettingAgent):
    
    def __init__(self, id, name, lengthOfRace, endOfInPlayBettingPeriod, influenced_by_opinions, 
                 local_opinion, uncertainty, lower_op_bound, upper_op_bound):
        super().__init__(id, name, lengthOfRace, endOfInPlayBettingPeriod, influenced_by_opinions,
                         local_opinion, uncertainty, lower_op_bound, upper_op_bound)
        self.xgb_loaded_model = xgb.Booster()
        self.xgb_loaded_model.load_model('xgb_bbe_model_1.json')  # the trained XGBoost model
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
        #print("decision >>> ", decision)
        return decision

    # def make_decision(self, features):
    #     """Make a decision (bet/lay) based on the XGBoost model's prediction."""
    #     prediction = self.xgb_loaded_model.predict([features])
    #     return prediction[0]

    def respond(self, time, markets, trade):
        if self.bettingPeriod == False: 
            return None
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

