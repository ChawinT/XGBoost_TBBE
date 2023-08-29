import random
from system_constants import *


def calculate_ema(odds, timesteps, smoothing=2):
    if len(odds) < timesteps:
        answer = 1 / NUM_OF_COMPETITORS
    else:
        ema = [sum(odds[:timesteps]) / timesteps]
        for odd in odds[timesteps:]:
            ema.append((odd * (smoothing / (1 + timesteps))) + ema[-1] * (1 - (smoothing / (1 + timesteps))))
        answer = 1 / ema[-1]
    return answer


class LocalConversation:

    def __init__(self, id, bettor1, bettor2, start_time, model):
        self.id = id
        self.bettor1 = bettor1
        self.bettor2 = bettor2
        self.start_time = start_time
        self.model = model
        self.conversation_length = random.uniform(2, 6)
        self.in_progress = 1
        self.bettor1.in_conversation = 1
        self.bettor2.in_conversation = 1

    def change_local_opinions(self):
        if self.model == 'BC':
            self.bounded_confidence_step(mu, delta)
        elif self.model == 'RA':
            self.relative_agreement_step(mu)
        elif self.model == 'RD':
            self.relative_disagreement_step(mu, lmda)
        else:
            return print('OD model does not exist')

    # # Opinion dynamics models

    # bounded confidence model
    # (w, delta) are confidence factor and deviation threshold  respectively
    def bounded_confidence_step(self, w, delta):

        X_i = self.bettor1.local_opinion
        X_j = self.bettor2.local_opinion

        # if difference in opinion is within deviation threshold
        if abs(X_i - X_j) <= delta:
            if self.bettor1.influenced_by_opinions == 1:
                i_update = w * X_i + (1 - w) * X_j
                self.bettor1.set_opinion(i_update)
            if self.bettor2.influenced_by_opinions == 1:
                j_update = w * X_j + (1 - w) * X_i
                self.bettor2.set_opinion(j_update)

    def relative_agreement_step(self, weight):

        X_i = self.bettor1.local_opinion
        u_i = self.bettor1.uncertainty

        X_j = self.bettor2.local_opinion
        u_j = self.bettor2.uncertainty

        h_ij = min((X_i + u_i), (X_j + u_j)) - max((X_i - u_i), (X_j - u_j))
        h_ji = min((X_j + u_j), (X_i + u_i)) - max((X_j - u_j), (X_i - u_i))

        if (h_ji > u_j):
            if self.bettor1.influenced_by_opinions == 1:
                RA_ji = (h_ji / u_j) - 1
                self.bettor1.set_opinion(X_i + (weight * RA_ji * (X_j - X_i)))
                self.bettor1.set_uncertainty(u_i + (weight * RA_ji * (u_j - u_i)))
        if (h_ij > u_i):
            if self.bettor2.influenced_by_opinions == 1:
                RA_ij = (h_ij / u_i) - 1
                self.bettor2.set_opinion(X_j + (weight * RA_ij * (X_i - X_j)))
                self.bettor2.set_uncertainty(u_j + (weight * RA_ij * (u_i - u_j)))

    def relative_disagreement_step(self, weight, prob):

        X_i = self.bettor1.local_opinion
        u_i = self.bettor1.uncertainty

        X_j = self.bettor2.local_opinion
        u_j = self.bettor2.uncertainty

        # Calculate overlap
        # g_ij = max((X_i - u_i), (X_j - u_j)) - min((X_i + u_i), (X_j + u_j))
        g_ij = min((X_i + u_i), (X_j + u_j)) - max((X_i - u_i), (X_j - u_j))
        # g_ji = max((X_j - u_j), (X_i - u_i)) - min((X_j + u_j), (X_i + u_i))
        g_ji = min((X_j + u_j), (X_i + u_i)) - max((X_j - u_j), (X_i - u_i))

        # update with prob λ
        if random.random() <= prob:
            if (g_ji > u_j):
                if self.bettor1.influenced_by_opinions == 1:
                    RD_ji = (g_ji / u_j) - 1
                    self.bettor1.set_opinion(X_i - (weight * RD_ji * (X_j - X_i)))
                    self.bettor1.set_uncertainty(u_i + (weight * RD_ji * (u_j - u_i)))
            if (g_ij > u_i):
                if self.bettor2.influenced_by_opinions == 1:
                    RD_ij = (g_ij / u_i) - 1
                    self.bettor2.set_opinion(X_j - (weight * RD_ij * (X_i - X_j)))
                    self.bettor2.set_uncertainty(u_j + (weight * RD_ij * (u_i - u_j)))


class OpinionDynamicsPlatform:
    def __init__(self, bettors, model):
        self.bettors = bettors
        self.model = model
        self.conversations = []
        self.number_of_conversations = 0

        self.all_influenced_by_opinions = [bettor for bettor in bettors if bettor.influenced_by_opinions == 1]
        self.all_opinionated = [bettor for bettor in bettors if bettor.opinionated == 1]

        self.available_influenced_by_opinions = [bettor for bettor in self.all_influenced_by_opinions if
                                                 bettor.in_conversation == 0]
        self.available_opinionated = [bettor for bettor in self.all_opinionated if
                                      bettor.in_conversation == 0]
        #
        # self.unavailable_influenced_by_opinions = [bettor for bettor in self.all_influenced_by_opinions if
        #                                            bettor.in_conversation == 1]
        # self.unavailable_opinionated = [bettor for bettor in self.all_opinionated if
        #                                 bettor.in_conversation == 1]

    def initiate_conversations(self, time):

        for bettor in self.available_influenced_by_opinions:

            bettor1 = bettor
            bettor2 = bettor

            while bettor1 == bettor2:
                if len(self.available_influenced_by_opinions) == 0 or len(self.available_opinionated) < 2:
                    return
                else:
                    bettor2 = random.sample(self.available_opinionated, 1)[0]

            id = self.number_of_conversations

            Conversation = LocalConversation(id, bettor1, bettor2, time, self.model)

            self.available_influenced_by_opinions = [bettor for bettor in self.all_influenced_by_opinions if
                                                     bettor.in_conversation == 0]
            self.available_opinionated = [bettor for bettor in self.all_opinionated if
                                          bettor.in_conversation == 0]

            self.conversations.append(Conversation)
            self.number_of_conversations = self.number_of_conversations + 1

    def settle_opinions(self, winningCompetitor):

        for bettor in self.all_influenced_by_opinions:

            bettor.a3 = 1
            bettor.a2 = 0
            bettor.a1 = 0

            if OPINION_COMPETITOR == winningCompetitor:
                bettor.event_opinion = 1
            else:
                bettor.event_opinion = 0

            bettor.opinion = bettor.a1 * bettor.local_opinion + bettor.a2 * bettor.global_opinion + bettor.a3 * bettor.event_opinion

    def change_opinion(self, bettor, markets):

        if len(bettor.currentRaceState) > 0:

            # Update opinion weights a1, a2, a3

            bettor.a3 = max(bettor.currentRaceState.values()) / bettor.lengthOfRace
            a2 = (1 - bettor.a3) * bettor.start_a2
            bettor.a2 = a2
            bettor.a1 = 1 - bettor.a3 - bettor.a2

            if round(bettor.a1 + bettor.a2 + bettor.a3, 0) != 1:
                print('Warning: the starting weights of opinions are incorrect. '
                      '(bettor.a1, bettor.a2 and bettor.a3 should add up to 1): ',
                      round(bettor.a1 + bettor.a2 + bettor.a3, 0))
                print('\n bettor.a1: ', bettor.a1)
                print('\n bettor.a2: ', bettor.a2)
                print('\n bettor.a3: ', bettor.a3)


            # Update global opinion

            odds = [x for i, x in enumerate(bettor.competitor_odds['odds']) if
                    bettor.competitor_odds['competitor'][i] == OPINION_COMPETITOR]

            bettor.global_opinion = calculate_ema(odds, 80)

            # Update event opinion
            if bettor.bettingPeriod:
                total = 0
                for c in bettor.currentRaceState.values():
                    total = total + (bettor.lengthOfRace / (bettor.lengthOfRace - c)) ** 2

                bettor.event_opinion = (bettor.lengthOfRace / (
                    bettor.lengthOfRace - bettor.currentRaceState[OPINION_COMPETITOR])) ** 2 / total

        # Update overall bettor opinion
        bettor.opinion = bettor.a1 * bettor.local_opinion + \
                         bettor.a2 * bettor.global_opinion + bettor.a3 * bettor.event_opinion

    def update_opinions(self, time, markets):
        active_conversations = [c for c in self.conversations if c.in_progress == 1]

        # Update bettor local opinions (where conversation has reached an end)
        for c in active_conversations:

            if c.start_time + c.conversation_length <= time:

                c.change_local_opinions()
                c.in_progress = 0
                c.bettor1.in_conversation = 0
                c.bettor2.in_conversation = 0

                self.available_influenced_by_opinions = [bettor for bettor in self.all_influenced_by_opinions if
                                                         bettor.in_conversation == 0]
                self.available_opinionated = [bettor for bettor in self.all_opinionated if
                                              bettor.in_conversation == 0]

            else:
                continue

        # Update bettor global opinion, opinion weights, event opinion and finally calculate overall bettor opinion.
        for bettor in self.all_influenced_by_opinions:
            self.change_opinion(bettor, markets)
