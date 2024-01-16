import ROOT
from math import exp

def calcEventLossProb(
        timeStep: float,
        occupancy: float,
                      ):
    return 1 - (occupancy ** 2)/((1 - exp(-occupancy))**2) * exp(-2*occupancy * (timeStep + 1))

def eventLossProbDistrib(
        timeStep: float,
        occupancy: list[float],
                         ):
    lossProb = []

    for val in occupancy:
        lossProb += [calcEventLossProb(timeStep, val)]

    return lossProb

def occupancyGraphToEventLossProbability(
        occupancy: ROOT.TGraph,
        minTimeStep: int = 0,
        maxTimeStep: int = 400,
                                         ):
    allTimeSteps = range(minTimeStep, maxTimeStep)

    retData = {
        'length': [],
        'occupancy': [],
    }

    return retData