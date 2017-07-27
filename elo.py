# Modified ELO algorithm implemented by Stephen Slater on 7/26/17
# Considers game point differential and ELO percentile when calculating new ELO
# The function expected() was taken from https://github.com/rshk/elo/blob/master/elo.py
# See https://en.wikipedia.org/wiki/Elo_rating_system

from __future__ import division

def expected(eloA, eloB):
    """
    Calculate expected score of A in a match against B
    Values are in the range [0, 1], where 1 represents 100% expected win
    :param A: Elo rating for player A
    :param B: Elo rating for player B
    """
    return 1 / (1 + 10 ** ((eloB - eloA) / 400))

# Returns the two new elo values in a tuple: (newA, newB)
def elo(eloA, eloB, scoreA, scoreB, k=32, eloMax=3000):
    """
    Calculate the new Elo rating for a player
    :param eloA: The previous Elo rating for player A
    :param eloB: The previous Elo rating for player B
    :scoreA: Score of Player A
    :scoreB: Score of Player B
    :param k: The k-factor for Elo (default: 32)
    :eloMax: The max rating achievable
    """

    # Calculated expected score of this match
    expA = expected(eloA, eloB)
    expB = 1 - expA
    wonA = int(scoreA > scoreB)
    wonB = 1 - wonA
    scoreMax = max(scoreA, scoreB)
    diff = abs(scoreA - scoreB)
    flag = 1

    # Calculate new base ELO score before factoring in game score
    baseA = eloA + k * (wonA - expA) * (1 - (wonA * (eloA / eloMax)))
    baseB = eloB + k * (wonB - expB) * (1 - (wonB * (eloB / eloMax)))

    # Span is the distance beyond the base score
    spanA = abs(baseA - eloA) / 3
    spanB = abs(baseB - eloB) / 3

    # Step is the number of ELO points gained/lost per ping-pong point
    stepA = spanA / (0.5 * scoreMax)
    stepB = spanB / (0.5 * scoreMax)

    score = scoreA if scoreA < scoreB else scoreB
    changeA = stepA * (score - 0.5 * scoreMax)
    changeB = stepB * (score - 0.5 * scoreMax)
    if scoreA > scoreB:
        flag *= -1

    # New ELO scores factoring in game point differential
    newA = baseA + flag * changeA
    newB = baseB - (flag * changeB)

    # Calculated ELO scores without factoring in game point differential
    # newA = baseA
    # newB = baseB

    # Output for testing
    # print "baseA " + str(baseA)
    # print "baseB " + str(baseB)
    # print "spanA " + str(spanA)
    # print "spanB " + str(spanB)
    # print "stepA " + str(stepA)
    # print "stepB " + str(stepB)
    # print "expA " + str(expA)
    # print "expB " + str(expB)
    # print "wonA " + str(wonA)
    # print "wonB " + str(wonB)
    # print "lower score: " + str(score)
    # print "score diff " + str(diff)
    # print "oldA " + str(eloA)
    # print "newA, newA2: " + str(newA) + ", " + str(newA3)
    # print "oldB " + str(eloB)
    # print "newB, newB2: " + str(newB) + ", " + str(newB3)

    return newA, newB 

# print "Match 1: higher rank A wins big"
# elo(1200, 1000, 11, 0)
# print "\n" + "Match 2: higher rank A wins small"
# elo(1200, 1000, 11, 9)
# print "\n" + "Match 3: smaller rank A wins big"
# elo(1200, 1000, 0, 11)
# print "\n" + "Match 4: smaller rank A wins small"
# elo(1200, 1000, 9, 11)
# print "\n" + "Match 5: expert player A wins with 0.75 exp"
# elo(2900, 2700, 11, 7)
# print "\n" + "Match 6: normal player A wins with 0.75 exp"
# elo(1800, 1600, 11, 7)
# print "\n" + "Match 7: expert player A loses with 0.75 exp"
# elo(2900, 2700, 0, 11)
# print "\n" + "Match 8: normal player A loses with 0.75 exp"
# elo(1800, 1600, 5, 11)
# print "\n" + "Match 9: normal player A loses 0-11 with 0.75 exp"
# elo(1800, 1600, 0, 11)
# print "\n" + "Match 10: normal player A loses 1-11 with 0.75 exp"
# elo(1800, 1600, 1, 11)
# print "\n" + "Match 11: normal player A loses 5-11 with 0.75 exp"
# elo(1800, 1600, 5, 11)
# print "\n" + "Match 12: normal player A loses 6-11 with 0.75 exp"
# elo(1800, 1600, 6, 11)
# print "\n" + "Match 13: normal player A loses 9-11 with 0.75 exp"
# elo(1800, 1600, 9, 11)
# print "\n" + "Match 14: normal player A wins 11-9 with 0.75 exp"
# elo(1800, 1600, 11, 9)
# print "\n" + "Match 15: normal player A wins 11-6 with 0.75 exp"
# elo(1800, 1600, 11, 6)
# print "\n" + "Match 16: normal player A wins 11-5 with 0.75 exp"
# elo(1800, 1600, 11, 5)
# print "\n" + "Match 17: normal player A wins 11-1 with 0.75 exp"
# elo(1800, 1600, 11, 1)
# print "\n" + "Match 18: normal player A wins 11-0 with 0.75 exp"
# elo(1800, 1600, 11, 0)



