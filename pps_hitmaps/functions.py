import ROOT
from math import exp
from __future__ import annotations

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

def occupancyToEventLossProbability(
        occupancy: list[float],
        minTimeStep: int = 0,
        maxTimeStep: int = 400,
                                         ):
    allTimeSteps = range(minTimeStep, maxTimeStep)

    retData = {
        'time_steps': allTimeSteps,
        'occupancy': occupancy,
    }

    for timeStep in allTimeSteps:
        probability = eventLossProbDistrib(timeStep, occupancy)

        retData["prob_timeStep{}".format(timeStep)] = probability

    return retData

def occupancyGraphToEventLossProbability(
        occupancyGraph: ROOT.TGraph,
        minTimeStep: int = 0,
        maxTimeStep: int = 400,
                                         ):
    import ctypes

    length = []
    occupancy = []
    xVal = ctypes.c_double(0.0)
    yVal = ctypes.c_double(0.0)
    for point in range(occupancyGraph.GetN()):
        occupancyGraph.GetPoint(point, xVal, yVal)
        length    += [xVal.value]
        occupancy += [yVal.value]

    retData = occupancyToEventLossProbability(occupancy, minTimeStep = minTimeStep, maxTimeStep = maxTimeStep)

    retData['length'] = length

    return retData