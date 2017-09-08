class MosaicFunction():

    def compute(self, values, times):
        pass


class MostRecent(MosaicFunction):

    name = "Most recent"

    def compute(self, values, times):
        return values[-1][0]

class LeastRecent(MosaicFunction):

    name = "Least recent"

    def compute(self, values, times):
        return values[0][0]

mosaicFunctions = [MostRecent(), LeastRecent()]
