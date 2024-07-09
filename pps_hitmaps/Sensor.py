#############################################################################
# zlib License
#
# (C) 2023 Cristóvão Beirão da Cruz e Silva <cbeiraod@cern.ch>
#
# This software is provided 'as-is', without any express or implied
# warranty.  In no event will the authors be held liable for any damages
# arising from the use of this software.
#
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
#
# 1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
# 2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
# 3. This notice may not be removed or altered from any source distribution.
#############################################################################

from __future__ import annotations

from .ClassFields import *
from .PPSHitmap import PPSHitmap
from .SensorPad import SensorPad

import pandas
import numpy
import hist
import matplotlib
import matplotlib.pyplot as plt
import mplhep
from math import ceil

def calcLossProb(deadtime, occupancy, bunchSpacing=25.):
    from math import exp, floor
    timeStep = floor(deadtime/float(bunchSpacing))
    return 1 - (occupancy ** 2)/((1 - exp(-occupancy))**2) * exp(-2*occupancy * (timeStep + 1))

# TODO: Check what is using so much memory

class Sensor:
    numPads = NonNegativeIntField()
    shifts = FloatPairListField()
    minX = FloatField()
    maxX = FloatField()
    minY = FloatField()
    maxY = FloatField()
    padVec : list[SensorPad]

    def __init__(self, shifts:list = []):
        self.shifts = shifts
        self.numPads = 0
        self.padVec = []

        self.minX = 0
        self.maxX = 0
        self.minY = 0
        self.maxY = 0

        self.hasFlux = False
        self._hist_stepping = None

    def _getAllPadCategories(self):
        return ["all"]

    def _getPadCategory(self, padID):
        return "all"

    def simulateToys(self, numToys: int = 1000, seed: int | None = None):
        rng = numpy.random.default_rng(seed = seed)
        toyCache = []

        all_categories = self._getAllPadCategories()
        extra_cols = []
        for cat in all_categories:
            extra_cols += ["event_loss_"+cat, "active_pads_"+cat, "sensor_occupancy_"+cat, "bit_length_"+cat]

        for epoch in range(len(self.shifts)):
            data = []
            for toyIdx in range(numToys):
                extra_col_data = []
                hits = []
                hits_per_cat = {}
                for cat in all_categories:
                    hits_per_cat[cat] = []

                for padID in range(len(self.padVec)):
                    pad = self.padVec[padID]
                    pad_hits = rng.poisson(pad.doses[epoch]["occupancy"])
                    hits += [pad_hits]
                    pad_cat = self._getPadCategory(padID)
                    hits_per_cat[pad_cat] += [pad_hits]

                singleHits = [1 if hit >= 1 else 0 for hit in hits]
                eventLoss = any([True if hit >= 2 else False for hit in hits])
                activePads = sum(singleHits)
                sensorOccupancy = float(activePads)/len(self.padVec)
                bitLength = 40 * (activePads + 2)  # We add 2 because each event needs a header and a trailer and each data word is 40 bits

                for cat in all_categories:
                    catSingleHits = [1 if hit >= 1 else 0 for hit in hits_per_cat[cat]]
                    catEventLoss = any([True if hit >= 2 else False for hit in hits_per_cat[cat]])
                    catActivePads = sum(catSingleHits)
                    catSensorOccupancy = float(catActivePads)/len(hits_per_cat[cat])
                    catBitLength = 40 * (catActivePads + 2)

                    extra_col_data += [catEventLoss, catActivePads, catSensorOccupancy*100, catBitLength]

                data += [[toyIdx, f'{hits}'[1:-1], eventLoss, activePads, sensorOccupancy*100, bitLength]+extra_col_data]
            toyCache += [pandas.DataFrame(data, columns=['event', 'hitmap', 'event_loss', 'active_pads', 'sensor_occupancy', 'bit_length']+extra_cols)]
            del data

        return toyCache

    def plotToyInfo(self, toyCache: list[pandas.DataFrame], column: str, minX: float, maxX: float, bins: int, title: str, label: str = None):
        plt.style.use(mplhep.style.CMS)

        numTPads = len(self.shifts)

        if numTPads <= 3:
            nCols = numTPads
            nRows = 1
        elif numTPads <= 6:
            nCols = ceil(numTPads/2.)
            nRows = 2
        else:
            nCols = 3
            nRows = ceil(numTPads/3.)

        #fig, axes = plt.subplots(nRows, nCols, figsize=(nRows*10, nCols*10))
        fig = plt.figure(dpi=100, figsize=(nRows*10, nCols*10))
        gs = fig.add_gridspec(nRows, nCols)

        for i, plot_info in enumerate(gs):
            if i >= len(self.shifts):
                break
            ax = fig.add_subplot(plot_info)
            mplhep.cms.text(loc=0, ax=ax, text="PPS2 Preliminary", fontsize=18)

            histogram = hist.Hist.new.Reg(bins, minX, maxX, name=column, label=label).Double()
            histogram.fill(toyCache[i][column])

            ax.set_title(title + f" - Position {i}", loc="right", size=16)
            histogram.plot1d(ax=ax, lw=2)
            #histogram.project(column)[:].plot1d(ax=ax, lw=2)

        plt.tight_layout()

        return fig

    def plotToyActivePads(self, numToys: int = 1000, toyCache: list[pandas.DataFrame] | None = None):
        if toyCache is not None:
            numToys = len(toyCache[0])
        else:
            toyCache = self.simulateToys(numToys = numToys)

        return self.plotToyInfo(toyCache, "active_pads", 0, 257, 257, "Active Pads", label = "# Active Pads")

    def plotToySensorOccupancy(self, numToys: int = 1000, toyCache: list[pandas.DataFrame] | None = None):
        if toyCache is not None:
            numToys = len(toyCache[0])
        else:
            toyCache = self.simulateToys(numToys = numToys)

        return self.plotToyInfo(toyCache, "sensor_occupancy", 0, 100, 100, "Sensor Occupancy", label = "Sensor Pad Occupancy [%]")

    def plotToyEventSize(self, numToys: int = 1000, toyCache: list[pandas.DataFrame] | None = None):
        if toyCache is not None:
            numToys = len(toyCache[0])
        else:
            toyCache = self.simulateToys(numToys = numToys)

        return self.plotToyInfo(toyCache, "bit_length", 0, 4000, 100, "Event Size", label = "Event Bit Length")

    def setShifts(self, shifts:list):
        self.shifts = shifts
        for pad in self.padVec:
            pad.setEpochs(len(shifts))

        self.hasFlux = False

    def calculateFlux(self, hitmap:PPSHitmap):
        if not isinstance(hitmap, PPSHitmap):
            raise ValueError(f'expecting PPSHitmap to calculate the dose')

        hitmap._checkMap()

        for pad in self.padVec:
            pad.calculateFlux(self.shifts, hitmap) # Remember PPSHitmap is in m, sensor is in mm

        self.hasFlux = True
        self._hist_stepping = hitmap.xStep * hitmap.yStep *1000 *1000  ## Convert m to mm
        # TODO: this function needs to be called before some of the others make sense... add a check
        # Also, modifying the shifts, invalidates previous flux call, so double check that too

    def findMaxOccupancy(self, usePadSpacing=True):
        if not self.hasFlux:
            raise RuntimeError("You must calculate the fluxes before retrieving the max occupancy")

        occupancy = []
        pads = []
        for epoch in range(len(self.shifts)):
            padIdx = None

            for idx in range(len(self.padVec)):
                if padIdx is None:
                    padIdx = idx
                else:
                    if usePadSpacing:
                        if self.padVec[idx].doses[epoch]["occupancy"] > self.padVec[padIdx].doses[epoch]["occupancy"]:
                            padIdx = idx
                    else:
                        if self.padVec[idx].doses_extra[epoch]["occupancy"] > self.padVec[padIdx].doses_extra[epoch]["occupancy"]:
                            padIdx = idx

            if padIdx is None:
                raise RuntimeError("Unable to find pad with max occupancy for epoch {}".format(epoch))

            if usePadSpacing:
                occupancy += [self.padVec[padIdx].doses[epoch]["occupancy"]]
            else:
                occupancy += [self.padVec[padIdx].doses_extra[epoch]["occupancy"]]
            pads += [padIdx]

        return (occupancy, pads)

    def plotSensorQuantity(self, quantity: str, margin: float = 0.8, minV = None, maxV = None, logz = False):
        if not self.hasFlux:
            raise RuntimeError("You must calculate the fluxes before retrieving the max occupancy")

        quantity_options = {
            'flux': {
                'zTitle': '#Phi [p / (cm^{2} fb^{-1})]',
                'title': 'Average Flux',
            },
            'protons': {
                'zTitle': '#Phi [p / pad]',
                'title': 'Flux per pad',
            },
            'occupancy': {
                'zTitle': '#mu [p / BX]',
                'title': 'Occupancy',
            },
            'loss_probability': {
                'zTitle': 'p',
                'title': 'Loss Probability',
            },
        }
        if quantity not in quantity_options:
            raise RuntimeError("You must ask to plot a valid quantity")

        from ROOT import TCanvas, TH2Poly, TLine, kRed, kBlack, kFALSE
        from array import array
        from math import ceil
        from .functions import calcEventLossProb

        numTPads = len(self.shifts)
        if numTPads <= 3:
            padX = numTPads
            padY = 1
        elif numTPads <= 6:
            padX = ceil(numTPads/2.)
            padY = 2
        else:
            padX = 3
            padY = ceil(numTPads/3.)

        persistance = {}

        canv = TCanvas(f"sensor_{quantity}", f"Sensor {quantity}", padX * 1300, padY * 1300)
        canv.Divide(padX, padY)

        base_hist = TH2Poly("base_hist", "base_hist", self.minX-margin, self.maxX+margin, self.minY-margin, self.maxY+margin)
        base_hist.SetStats(kFALSE)
        base_hist.GetXaxis().SetTitle( "x [mm]" )
        base_hist.GetYaxis().SetTitle( "y [mm]" )
        base_hist.GetZaxis().SetTitle( quantity_options[quantity]['zTitle'] )
        base_hist.GetXaxis().SetTitleOffset(0.9)
        base_hist.GetYaxis().SetTitleOffset(1.2)
        base_hist.GetZaxis().SetTitleOffset(1.6)
        base_hist.GetYaxis().SetLabelOffset(0.01)
        if minV is not None and maxV is not None:
            base_hist.SetMinimum(minV)
            base_hist.SetMaximum(maxV)

        sensorLines = {}
        sensorLines["Left"]   = TLine( self.minX, self.minY,
                                       self.minX, self.maxY)
        sensorLines["Right"]  = TLine( self.maxX, self.minY,
                                       self.maxX, self.maxY)
        sensorLines["Top"]    = TLine( self.minX, self.minY,
                                       self.maxX, self.minY)
        sensorLines["Bottom"] = TLine( self.minX, self.maxY,
                                       self.maxX, self.maxY)
        for key in sensorLines:
            sensorLines[key].SetLineColor(kRed)

        padID = 0
        for pad in self.padVec:
            minX = pad.minX
            maxX = pad.maxX
            minY = pad.minY
            maxY = pad.maxY

            sensorLines[f"pad{padID}_Left"]   = TLine( minX, minY, minX, maxY)
            sensorLines[f"pad{padID}_Right"]  = TLine( maxX, minY, maxX, maxY)
            sensorLines[f"pad{padID}_Top"]    = TLine( minX, minY, maxX, minY)
            sensorLines[f"pad{padID}_Bottom"] = TLine( minX, maxY, maxX, maxY)

            sensorLines[f"pad{padID}_Left"].SetLineColor(kBlack)
            sensorLines[f"pad{padID}_Right"].SetLineColor(kBlack)
            sensorLines[f"pad{padID}_Top"].SetLineColor(kBlack)
            sensorLines[f"pad{padID}_Bottom"].SetLineColor(kBlack)

            xVals = array( 'd' )
            yVals = array( 'd' )
            xVals.append(minX)
            yVals.append(minY)
            xVals.append(minX)
            yVals.append(maxY)
            xVals.append(maxX)
            yVals.append(maxY)
            xVals.append(maxX)
            yVals.append(minY)
            base_hist.AddBin(4, xVals, yVals)

            padID += 1

        histograms = {}
        idx = 0
        for idx in range(numTPads):
            idx += 1
            if numTPads > 1:
                pad = canv.cd(idx)
            else:
                pad = canv

            pad.SetTicks()
            #pad.SetLogz()
            pad.SetLeftMargin(0.11)
            pad.SetRightMargin(0.16)
            pad.SetTopMargin(0.07)
            pad.SetBottomMargin(0.14)
            if logz:
                pad.SetLogz()

            this_hist = base_hist.Clone(f'{quantity}_pos_{idx-1}')
            this_hist.SetTitle(f"{quantity_options[quantity]['title']} - Position {idx-1}")

            padID = 0
            for pad in self.padVec:
                try:
                    loss_prob = calcEventLossProb(0, pad.doses[idx - 1]['occupancy'])
                except ZeroDivisionError as e:
                    loss_prob = 0
                quantity_values = {
                    'flux': pad.doses[idx - 1]['totalFlux']/(pad.area / self._hist_stepping),
                    'protons': pad.doses[idx - 1]['totalFlux'] * pad.doses[idx - 1]['occupancyNorm'],
                    'occupancy': pad.doses[idx - 1]['occupancy'],
                    'loss_probability': loss_prob,
                }
                this_hist.SetBinContent(padID + 1, quantity_values[quantity])
                padID += 1

            this_hist.Draw("colz")
            histograms[f'pos_{idx-1}'] = this_hist

            for key in sensorLines:
                sensorLines[key].Draw("same")

        persistance["sensorLines"] = sensorLines
        persistance["histograms"] = histograms
        persistance["canvas"] = canv

        return (canv, persistance)

    def plotOccupancy(self, usePadSpacing=True):
        if not self.hasFlux:
            raise RuntimeError("You must calculate the fluxes before retrieving the max occupancy")
        #occupancy = self.findMaxOccupancy(usePadSpacing=usePadSpacing)
        numTPads = len(self.shifts)

        from math import ceil

        if numTPads <= 3:
            padX = numTPads
            padY = 1
        elif numTPads <= 6:
            padX = ceil(numTPads/2.)
            padY = 2
        else:
            padX = 3
            padY = ceil(numTPads/3.)

        from ROOT import TCanvas, TH2D  # type: ignore
        from array import array

        edgesX = []
        edgesY = []
        for pad in self.padVec:
            if pad.minX_extra not in edgesX:
                edgesX += [pad.minX_extra]
            if pad.maxX_extra not in edgesX:
                edgesX += [pad.maxX_extra]
            if pad.minY_extra not in edgesY:
                edgesY += [pad.minY_extra]
            if pad.maxY_extra not in edgesY:
                edgesY += [pad.maxY_extra]
        edgesX.sort()
        edgesY.sort()

        xArr, yArr = array( 'd' ), array( 'd' )
        for edge in edgesX:
            xArr.append(edge)
        for edge in edgesY:
            yArr.append(edge)

        persistance = {}
        canv = TCanvas("epoch_Occupancy", "Epoch Occupancy", padX * 400, padY * 400)
        canv.Divide(padX, padY)

        histTemplate = TH2D("template", "Sensor Occupancy", len(xArr)-1, xArr, len(yArr)-1, yArr)
        histTemplate.SetStats(False)
        histTemplate.GetXaxis().SetTitle("x [mm]")
        histTemplate.GetYaxis().SetTitle("y [mm]")
        histTemplate.GetZaxis().SetTitle("#mu")

        numBinsX = len(xArr)-1
        numBinsY = len(yArr)-1

        for epoch in range(len(self.shifts)):
            pad = canv.cd(epoch+1)
            #pad.SetLogz()
            pad.SetTicks()
            #pad.SetLeftMargin(0.11)
            pad.SetRightMargin(0.16)
            pad.SetTopMargin(0.07)
            #pad.SetBottomMargin(0.14)

            hist = histTemplate.Clone("occupancy-epoch{}".format(epoch))
            hist.SetTitle("Occupancy Position {}".format(self.shifts[epoch]))

            for binX in range(numBinsX):
                binXPos = (edgesX[binX] + edgesX[binX+1])/2
                for binY in range(numBinsY):
                    binYPos = (edgesY[binY] + edgesY[binY+1])/2

                    occupancy = 0
                    for pad in self.padVec:
                        padMinX = pad.minX_extra
                        padMaxX = pad.maxX_extra
                        padMinY = pad.minY_extra
                        padMaxY = pad.maxY_extra
                        if ((binXPos > padMinX and binXPos < padMaxX) and
                            (binYPos > padMinY and binYPos < padMaxY)):
                            if usePadSpacing:
                                occupancy = pad.doses[epoch]["occupancy"]
                            else:
                                occupancy = pad.doses_extra[epoch]["occupancy"]
                            break

                    binx = hist.GetXaxis().FindBin(binXPos)
                    biny = hist.GetYaxis().FindBin(binYPos)
                    hist.SetBinContent(binx, biny, occupancy)

            hist.Draw("colz")

            persistance["occupancy-{}".format(epoch)] = hist

        return (canv, persistance)

    def plotLossProbabilityVsDeadtime(self, timeSteps=1000, minTime=0, maxTime=10000, usePadSpacing=True): # Time in ns
        occupancy = self.findMaxOccupancy(usePadSpacing=usePadSpacing)
        numTPads = len(occupancy)

        from math import ceil

        if numTPads <= 3:
            padX = numTPads
            padY = 1
        elif numTPads <= 6:
            padX = ceil(numTPads/2.)
            padY = 2
        else:
            padX = 3
            padY = ceil(numTPads/3.)

        from ROOT import TCanvas, TH2D, TGraph  # type: ignore
        from array import array

        persistance = {}
        canv = TCanvas("epoch_loss_probability", "Epoch Loss Probability", padX * 400, padY * 400)
        canv.Divide(padX, padY)

        # Create an empty histogram to serve as the frame for the graphs
        frame = TH2D("frame", "", 100, minTime, maxTime, 100, 0.001, 1.1)
        frame.SetStats(False)
        frame.GetXaxis().SetTitle("#tau ns")
        frame.GetYaxis().SetTitle("Event Loss Probability")

        for epoch in range(len(self.shifts)):
            pad = canv.cd(epoch+1)
            if minTime != 0:
                pad.SetLogx()
            pad.SetLogy()
            pad.SetTicks()

            persistance[self.shifts[epoch]] = {}

            persistance[self.shifts[epoch]]["frame"] = frame.Clone("frame-{}".format(epoch))
            persistance[self.shifts[epoch]]["frame"].SetTitle("Position {}".format(self.shifts[epoch]))
            persistance[self.shifts[epoch]]["frame"].Draw()

            timeArr, lossProb = array( 'd' ), array( 'd' )
            for i in range(timeSteps):
                time = minTime + i * float(maxTime - minTime)/timeSteps
                timeArr.append(time)
                lossProb.append(calcLossProb(time, occupancy[epoch]))
            persistance[self.shifts[epoch]]["graph"] = TGraph(timeSteps, timeArr, lossProb)
            persistance[self.shifts[epoch]]["graph"].Draw("l same")

        return (canv, persistance)

    def preview(self, margin=0.8, fontscale=1.0, doSquare=False):
        if self.numPads == 0:
            return None

        import matplotlib.pyplot as plt
        import matplotlib.patches as patches

        plt.style.use(mplhep.style.CMS)

        fig = plt.figure(figsize=(9, 9))
        ax1 = plt.subplot2grid((1,1),(0,0))

        mplhep.cms.text(loc=0, ax=ax1, text="PPS2 Preliminary", fontsize=18)

        if doSquare:
            minV = min(self.minX-margin, self.minY-margin)
            maxV = max(self.maxX+margin, self.maxY+margin)
            plt.xlim([minV, maxV])
            plt.ylim([minV, maxV])
        else:
            plt.xlim([self.minX-margin, self.maxX+margin])
            plt.ylim([self.minY-margin, self.maxY+margin])

        rect = patches.Rectangle((self.minX, self.minY),
                                    self.maxX-self.minX,
                                    self.maxY-self.minY,
                                    linewidth=1,
                                    edgecolor='r',
                                    facecolor='none')
        ax1.add_patch(rect)

        pad_idx = 0
        for pad in self.padVec:
            rect = patches.Rectangle((pad.minX, pad.minY),
                                        pad.maxX-pad.minX,
                                        pad.maxY-pad.minY,
                                        linewidth = 1,
                                        edgecolor='b',
                                        facecolor='none'
                                    )
            ax1.add_patch(rect)
            ax1.text((pad.minX + pad.maxX)/2,
                        (pad.minY + pad.maxY)/2,
                        f'{pad_idx}',
                        ha='center',
                        va='center',
                        fontsize=10*fontscale
                    )
            pad_idx += 1

        return fig

    def maxDoseEOL(self, integratedLuminosity=300, usePadSpacing = True):
        maxDose = None

        for pad in self.padVec:
            padDose = pad.maxDoseEOL(integratedLuminosity=integratedLuminosity, usePadSpacing=usePadSpacing)
            if maxDose is None:
                maxDose = padDose
            else:
                if padDose > maxDose:
                    maxDose = padDose

        return maxDose