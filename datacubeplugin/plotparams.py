from landsat import *

from qgis.core import QgsRaster

def getBand(layer, pt, band):
    try:
        value = layer.dataProvider().identify(pt,
            QgsRaster.IdentifyFormatValue).results().values()[band]
        return value
    except IndexError:
        return None

def getR(layer,pt):
    return getBand(layer, pt, RED_BAND)

def getG(layer,pt):
    return getBand(layer, pt, GREEN_BAND)

def getB(layer,pt):
    return getBand(layer, pt, BLUE_BAND)

def getNIR(layer, pt):
    return getBand(layer, pt, NIR_BAND)

def getSWIR1(layer, pt):
    return getBand(layer, pt, SWIR1_BAND)

def getCfmask(layer, pt):
    return getBand(layer, pt, CFMASK_BAND)

class PlotParameter():

    def __str__(self):
        return self.name

    def value(self, layer, pt):
        if self.checkMask(layer, pt):
            return self._value(pt)
        else:
            return None

    def checkMask(self, layer, pt):
        v = getCfmask(layer, pt)
        return v not in [2, 4, 255]

class Band_Value(PlotParameter):

    def __init__(self, idx):
        self.idx = idx
        self.name =  "Band " + str(self.idx + 1)

    def _value(self, layer, pt):
        return getBand(layer, pt, self.idx)


class NDVI(PlotParameter):

    name = "NDVI"

    def _value(self, layer, pt):
        r = getR(layer, pt)
        nir = getNIR(layer, pt)
        if nir is None or r is None:
            return None
        return (r - nir)/ (r + nir)

class EVI(PlotParameter):

    name = "EVI"

    def _value(self, layer, pt):
        L=1
        C1 = 6
        C2 = 7.5
        G = 2.5
        r = getR(layer, pt)
        nir = getNIR(layer, pt)
        b = getB(layer, pt)
        if nir is None or r is None or b is None:
            return None
        return G * (nir- r)/ (nir + C1 * r - C2 + b + L)

class NDWI(PlotParameter):

    name = "NDWI"

    def _value(self, layer, pt):
        nir = getNIR(layer, pt)
        g = getG(layer, pt)
        if nir is None or g is None:
            return None
        return (g - nir)/ (g + nir)

class NDBI(PlotParameter):

    name = "NDBI"

    def _value(self, layer, pt):
        nir = getNIR(layer, pt)
        swir = getSWIR1(layer, pt)
        if nir is None or swir is None:
            return None
        return (nir - swir)/ (nir + swir)

class WOFS(PlotParameter):

    name = "WOFS"

    def _value(self, layer, pt):
        pass

class TSM(PlotParameter):

    name = "TSM"

    def _value(self, layer, pt):
        pass

class BS(PlotParameter):

    name = "BS"

    def _value(self, layer, pt):
        pass

class PV(PlotParameter):

    name = "PV"

    def _value(self, layer, pt):
        pass

class NPV(PlotParameter):

    name = "NPV"

    def _value(self, layer, pt):
        pass


parameters = [Band_Value(i) for i in range(9)]
parameters.extend([NDVI(), NDBI(), EVI(), NDWI(), WOFS(), TSM(), BS(), PV(), NPV()])