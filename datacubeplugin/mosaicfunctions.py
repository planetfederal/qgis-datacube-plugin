import numpy as np

class MosaicFunction():

    def compute(self, values, qa):
        resultRow = []
        for x in xrange(values[0].shape[1]):
            validValues = []
            for idx, tpos in enumerate(values):
                v = tpos.item(0, x)
                valid = True
                if qa is not None:
                    valid = self.checkMask(qa[idx].item(1, x))
                if valid:
                    validValues.append(v)
            resultRow.append(self._compute(validValues))
        return np.array(resultRow)

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

    def _compute(self, values):
        return np.median(values)

mosaicFunctions = [MostRecent(), LeastRecent()]
