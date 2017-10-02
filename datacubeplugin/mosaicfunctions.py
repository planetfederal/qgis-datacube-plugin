import numpy as np

class MosaicFunction():

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
                resultRow.append(self._compute(validValues))
            resultRows.append(resultRow)
        return np.array(resultRows)

    def checkMask(self, v):
        return True
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

    def _compute(self, values):
        return np.median(values)

mosaicFunctions = [MostRecent(), LeastRecent(), Median()]
