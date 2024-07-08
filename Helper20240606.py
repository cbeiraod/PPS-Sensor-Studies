import ROOT
from math import ceil

detector_edge = {
    "196": {
        0.15: 9.345,
        0.20: 9.117,
        0.50: 8.609,
    },
    "220": {
        0.15: 4.201,
        0.20: 4.121,
        0.50: 4.022,
    },
    "234": {
        0.15: 1.700,
        0.20: 1.700,
        0.50: 2.025,
    },
}

def getNominalPositions(hitmaps, xSensorSize):
    nominal_positions = {}
    for key in hitmaps:
        offsetX = hitmaps[key].detectorEdge*1000 + xSensorSize/2
        offsetY = hitmaps[key].maxFluence["y"]*1000
        nominal_positions[key] = (offsetX, offsetY)

def getAdjustedPositions(nominal_positions, station):
    adjusted_positions = {}

    position_keys = [
        ("vertical", 250, (0.50, 0.20)),
        ("vertical", 125, (0.50, 0.20)),
        ("horizontal", 250, (0.50, 0.15)),
        ("horizontal", 125, (0.50, 0.15)),
    ]
    for angle_dir, angle, betas in position_keys:
        position_key = f"{angle_dir}-{angle}urad"

        offsetX = 0
        offsetY = 0
        count = 0
        for beta in betas:
            hitmap_key = f"{angle_dir}-{angle}urad-{int(beta*100)}cm"
            count += 1
            offsets = nominal_positions[hitmap_key]

            offsetX += offsets[0]
            offsetY += offsets[1]

        adjusted_positions[position_key] = (offsetX/count, offsetY/count)

    if station == "196":
        adjusted_positions['vertical-250urad'] = (19.558, -10.175 - 3*1.3)
    elif station == "220":
        adjusted_positions['vertical-250urad'] = (19.558, -4.95 - 3*1.3)
        adjusted_positions['vertical-125urad'] = (19.558, -2.4 - 2*1.3)
    elif station == "234":
        pass
    return adjusted_positions

def computeShifts(nominalSensorCenters, shift_info):
    offsets = []

    for sensorCenter in nominalSensorCenters:
        positions = []

        for shift in range(shift_info[0] + 1):
            if shift_info[1] is None:
                shift_offset = 0
            else:
                shift_offset = shift_info[1]/shift_info[0]

            shift_val = -shift_info[0]/2 + shift
            positions += [sensorCenter + shift_val * shift_offset]

        offsets += [positions]

    return offsets

def computeYCenters196(positionY, angle_dir, ySensorSize):
    if angle_dir == "vertical":
        return [positionY, positionY - (0.2 + ySensorSize)]
    else:
        return [(0.2 + ySensorSize)/2, - (0.2 + ySensorSize)/2]

def computeYCenters220(positionY, angle_dir, ySensorSize):
    if angle_dir == "vertical":
        return [positionY]
    else:
        return [0.0]

def computeYCenters234(positionY, angle_dir, ySensorSize):
    if angle_dir == "vertical":
        return [positionY]
    else:
        return [0]

def plotShiftsOnFluxmap(sensor, positions, hitmap, histogram, base_name, title):
    ROOT.gStyle.SetPalette()

    num_pos = len(positions[0])

    if num_pos <= 3:
        xPads = num_pos
        yPads = 1
    elif num_pos <= 4:
        xPads = 2
        yPads = 2
    elif num_pos <= 9:
        xPads = 3
        yPads = ceil(num_pos/3)
    else:
        xPads = 4
        yPads = ceil(num_pos/4)

    persistance = {}
    canv = ROOT.TCanvas(f"{base_name}_sensorPositionShifts", f"{base_name}_sensorPositionShifts", xPads*1300, yPads*1300)
    canv.Divide(xPads,yPads)

    edge = hitmap.detectorEdge * 1000 # Convert to mm for drawing
    yMin = hitmap.yMin * 1000         # Convert to mm for drawing
    yMax = hitmap.yMax * 1000         # Convert to mm for drawing
    edgeLine = ROOT.TLine(edge,yMin,edge,yMax)
    edgeLine.SetLineColor(ROOT.kRed)
    persistance["sensorEdge"] = edgeLine

    persistance["histogram"] = histogram.Clone()
    persistance["histogram"].SetTitle(title)

    pad_idx = 0
    sensorLines = {}
    xSensorSize = sensor.maxX - sensor.minX
    for shift_idx in range(num_pos):
        pad_idx += 1
        pad = canv.cd(pad_idx)

        pad.SetTicks()
        pad.SetLogz()
        pad.SetLeftMargin(0.11)
        pad.SetRightMargin(0.16)
        pad.SetTopMargin(0.07)
        pad.SetBottomMargin(0.14)
        persistance["histogram"].Draw("colz")
        edgeLine.Draw("same")

        sensorLines[pad_idx] = {}
        for sensor_idx in range(len(positions)):
            offsetX = edge + xSensorSize/2
            offsetY = positions[sensor_idx][shift_idx]

            sensorLines[pad_idx][sensor_idx] = {}
            sensorLines[pad_idx][sensor_idx]["Left"]   = ROOT.TLine( sensor.minX + offsetX, sensor.minY + offsetY,
                                                                     sensor.minX + offsetX, sensor.maxY + offsetY)
            sensorLines[pad_idx][sensor_idx]["Right"]  = ROOT.TLine( sensor.maxX + offsetX, sensor.minY + offsetY,
                                                                     sensor.maxX + offsetX, sensor.maxY + offsetY)
            sensorLines[pad_idx][sensor_idx]["Top"]    = ROOT.TLine( sensor.minX + offsetX, sensor.minY + offsetY,
                                                                     sensor.maxX + offsetX, sensor.minY + offsetY)
            sensorLines[pad_idx][sensor_idx]["Bottom"] = ROOT.TLine( sensor.minX + offsetX, sensor.maxY + offsetY,
                                                                     sensor.maxX + offsetX, sensor.maxY + offsetY)
            for key in sensorLines[pad_idx][sensor_idx]:
                sensorLines[pad_idx][sensor_idx][key].SetLineColor(ROOT.kRed)

            padID = 0
            for pad in sensor.padVec:
                minX = pad.minX
                maxX = pad.maxX
                minY = pad.minY
                maxY = pad.maxY

                sensorLines[pad_idx][sensor_idx][f"pad{padID}_Left"]   = ROOT.TLine( minX + offsetX, minY + offsetY,
                                                                        minX + offsetX, maxY + offsetY)
                sensorLines[pad_idx][sensor_idx][f"pad{padID}_Right"]  = ROOT.TLine( maxX + offsetX, minY + offsetY,
                                                                        maxX + offsetX, maxY + offsetY)
                sensorLines[pad_idx][sensor_idx][f"pad{padID}_Top"]    = ROOT.TLine( minX + offsetX, minY + offsetY,
                                                                        maxX + offsetX, minY + offsetY)
                sensorLines[pad_idx][sensor_idx][f"pad{padID}_Bottom"] = ROOT.TLine( minX + offsetX, maxY + offsetY,
                                                                        maxX + offsetX, maxY + offsetY)

                sensorLines[pad_idx][sensor_idx][f"pad{padID}_Left"].SetLineColor(ROOT.kBlue)
                sensorLines[pad_idx][sensor_idx][f"pad{padID}_Right"].SetLineColor(ROOT.kBlue)
                sensorLines[pad_idx][sensor_idx][f"pad{padID}_Top"].SetLineColor(ROOT.kBlue)
                sensorLines[pad_idx][sensor_idx][f"pad{padID}_Bottom"].SetLineColor(ROOT.kBlue)

                padID += 1

            for key in sensorLines[pad_idx][sensor_idx]:
                sensorLines[pad_idx][sensor_idx][key].Draw("same")

        persistance[f"sensorLines_shift{shift_idx}"] = sensorLines

    return canv, persistance

def plotOccupancy(sensor, positions, hitmap, name, minV, maxV):
    ROOT.gStyle.SetPalette()

    num_sensors = len(positions)

    edge = hitmap.detectorEdge * 1000 # Convert to mm for drawing
    xSensorSize = sensor.maxX - sensor.minX
    offsetX = edge + xSensorSize/2

    canvas = []
    persistance = []

    for sensor_idx in range(num_sensors):
        shifted_positions = [
                (offsetX, offsetY)
                for offsetY in positions[sensor_idx]
            ]

        sensor.setShifts(shifted_positions)
        sensor.calculateFlux(hitmap)

        c, p = sensor.plotSensorQuantity("occupancy", minV = minV, maxV = maxV)
        c.SetName(c.GetName() + name + f"_Sensor{sensor_idx}")
        canvas.append(c)
        persistance.append(p)

        #c, p = sensor.plotSensorQuantity("loss_probability")
        #c.SetName(c.GetName() + f"_{angle_dir}-{angle}urad-{int(beta*100)}cm_Sensor{sensor_idx}")
        #canvas.append(c)
        #persistance.append(p)

    return canvas, persistance