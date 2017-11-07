import numpy as np
import math
try:   
    import hdmedians as hd
    geomMedianOk = True
except:
    geoMedianOk = False

#to be able to use the geomedian library if numpy < 1.9
np.nanmedian=np.median

NO_DATA = -99999

class MosaicFunction():
    
    bandByBand=True

    def computeQAMask(self, qas):
        resultRows = []
        for y in xrange(qas[0].shape[0]):
            resultRow = []
            for x in xrange(qas[0].shape[1]):
                res  = 255
                for qa in qas:
                    valid = self.checkMask(qa.item(y, x))
                    if valid:
                        res = 1
                        break
                resultRow.append(res)
            resultRows.append(resultRow)
        return np.array(resultRows)
    
    def compute(self, values, qa):
        if self.bandByBand:
            resultRows = []
            for y in xrange(values[0].shape[0]):
                resultRow = []
                for x in xrange(values[0].shape[1]):
                    validValues = []
                    for idx, tpos in enumerate(values):
                        v = tpos.item(y, x)
                        valid = True
                        if qa is not None:
                            valid = self.checkMask(qa[idx].item(y, x))
                        if valid:
                            validValues.append(v)
                    if validValues:
                        resultRow.append(self._compute(validValues))
                    else:
                        resultRow.append(NO_DATA)
                resultRows.append(resultRow)
            return np.array(resultRows)
        else:
            resultRows = [[] for _ in range(len(values))]
            for y in xrange(values[0][0].shape[0]):
                resultRow = [[] for _ in range(len(values))]
                for x in xrange(values[0][0].shape[1]):
                    validValues = []
                    for band in values:
                        bandValidValues = []
                        for idx, tpos in enumerate(band):
                            v = tpos.item(y, x)
                            valid = True
                            if qa is not None:
                                valid = self.checkMask(qa[idx].item(y, x))
                            if valid:
                                bandValidValues.append(float(v))
                        validValues.append(bandValidValues)
                    if len(validValues[0]):
                        result = self._compute(validValues)
                    else:
                        result = [NO_DATA] * len(values)

                    for i,v in enumerate(result):                                                
                        resultRow[i].append(v)
                for i in range(len(values)):
                    resultRows[i].append(resultRow[i])
            return [np.array(b) for b in resultRows]

    def checkMask(self, v):
        return v is None or v not in [2, 4, 255]


class MostRecent(MosaicFunction):

    name = "Most recent"

    def _compute(self, values):
        return values[-1]

class LeastRecent(MosaicFunction):

    name = "Least recent"

    def _compute(self, values):
        return values[0]

class Median(MosaicFunction):

    name = "Median"

    def _compute(self, values):
        return np.median(values)

class GeoMedian(MosaicFunction):

    name = "GeoMedian"
    bandByBand = False

    def _compute(self, values):
        return hd.nangeomedian(np.array(values))

mosaicFunctions = [MostRecent(), LeastRecent(), Median()]
if geoMedianOk:
    mosaicFunctions.append(GeoMedian())
