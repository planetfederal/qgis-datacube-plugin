from landsat import *

from qgis.core import QgsRaster

def getBand(layer, pt, band, bands):

    try:
        idx = bands.index(band)
        value = layer.dataProvider().identify(pt,
            QgsRaster.IdentifyFormatValue).results().values()[idx]
        return value
    except:
        return None

def getR(layer, pt, bands):
    return getBand(layer, pt, "red", bands)

def getG(layer,pt, bands):
    return getBand(layer, pt, "green", bands)

def getB(layer,pt, bands):
    return getBand(layer, pt, "blue", bands)

def getNIR(layer, pt, bands):
    return getBand(layer, pt, "nir", bands)

def getSWIR1(layer, pt, bands):
    return getBand(layer, pt, "swir1", bands)

def getPixelQA(layer, pt, bands):
    return getBand(layer, pt, "pixel_qa", bands)

class PlotParameter():

    def __str__(self):
        return self.name

    def value(self, layer, pt, bands):
        if self.checkMask(layer, pt, bands):
            return self._value(layer, pt, bands)
        else:
            return None

    def checkMask(self, layer, pt, bands):
        v = getPixelQA(layer, pt, bands)
        return v is None or v not in [2, 4, 255]

class BandValue(PlotParameter):

    def __init__(self, name):
        self.name = name

    def _value(self, layer, pt, bands):
        return getBand(layer, pt, self.name, bands)


class NDVI(PlotParameter):

    name = "NDVI"

    def _value(self, layer, pt, bands):
        r = getR(layer, pt, bands)
        nir = getNIR(layer, pt, bands)
        if nir is None or r is None:
            return None
        return (r - nir)/ (r + nir)

class EVI(PlotParameter):

    name = "EVI"

    def _value(self, layer, pt, bands):
        L=1
        C1 = 6
        C2 = 7.5
        G = 2.5
        r = getR(layer, pt, bands)
        nir = getNIR(layer, pt, bands)
        b = getB(layer, pt, bands)
        if nir is None or r is None or b is None:
            return None
        return G * (nir- r)/ (nir + C1 * r - C2 + b + L)

class NDWI(PlotParameter):

    name = "NDWI"

    def _value(self, layer, pt, bands):
        nir = getNIR(layer, pt, bands)
        g = getG(layer, pt, bands)
        if nir is None or g is None:
            return None
        return (g - nir)/ (g + nir)

class NDBI(PlotParameter):

    name = "NDBI"

    def _value(self, layer, pt, bands):
        nir = getNIR(layer, pt, bands)
        swir = getSWIR1(layer, pt, bands)
        if nir is None or swir is None:
            return None
        return (nir - swir)/ (nir + swir)

class WOFS(PlotParameter):

    name = "WOFS"

    def _value(self, layer, pt, bands):
        pass

class TSM(PlotParameter):

    name = "TSM"

    def _value(self, layer, pt, bands):
        pass

class BS(PlotParameter):

    name = "BS"

    def _value(self, layer, pt, bands):
        pass

class PV(PlotParameter):

    name = "PV"

    def _value(self, layer, pt, bands):
        pass

class NPV(PlotParameter):

    name = "NPV"

    def _value(self, layer, pt, bands):
        pass

def getParameters(bands):
    parameters = [BandValue(b) for b in bands]
    parameters.extend([NDVI(), NDBI(), EVI(), NDWI(), WOFS(), TSM(), BS(), PV(), NPV()])
    return parameters