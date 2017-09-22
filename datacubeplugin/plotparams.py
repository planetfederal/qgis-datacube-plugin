from qgis.core import QgsRaster, QgsRasterBlock

def getBand(layer, pt, band, bands):
    try:
        idx = bands.index(band)
    except ValueError:
        return None
    try:
        if isinstance(layer, list):
            block = layer[idx]
            value = block.item(int(pt.y()), int(pt.x()))
        else:
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

def getSWIR2(layer, pt, bands):
    return getBand(layer, pt, "swir2", bands)

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

        def _bandRatio(a, b):
            return (a - b) / (a + b)

        band1 = self.getB(layer, pt, bands)
        band2 = self.getG(layer, pt, bands)
        band3 = self.getR(layer, pt, bands)
        band4 = self.getNIR(layer, pt, bands)
        band5 = self.getSWIR1(layer, pt, bands)
        band7 = self.getSWIR2(layer, pt, bands)

        if None in [band1, band2, band3, band4, band5, band7]:
            return None

        # Compute normalized ratio indices
        ndi_52 = _bandRatio(band5, band2)
        ndi_43 = _bandRatio(band4, band3)
        ndi_72 = _bandRatio(band7, band2)

        # Start with the tree's left branch, finishing nodes as needed

        # Left branch
        r1 = ndi_52 <= -0.01

        r2 = band1 <= 2083.5

        if r1 and not r2:
            return 0 #Node 3

        classified[r1 & ~r2] = 0

        r3 = band7 <= 323.5
        _tmp = r1 & r2
        _tmp2 = _tmp & r3
        _tmp &= ~r3

        r4 = ndi_43 <= 0.61
        classified[_tmp2 & r4] = 1  #Node 6
        classified[_tmp2 & ~r4] = 0  #Node 7

        r5 = band1 <= 1400.5
        _tmp2 = _tmp & ~r5

        r6 = ndi_43 <= -0.01
        classified[_tmp2 & r6] = 1  #Node 10
        classified[_tmp2 & ~r6] = 0  #Node 11

        _tmp &= r5

        r7 = ndi_72 <= -0.23
        _tmp2 = _tmp & ~r7

        r8 = band1 <= 379
        classified[_tmp2 & r8] = 1  #Node 14
        classified[_tmp2 & ~r8] = 0  #Node 15

        _tmp &= r7

        r9 = ndi_43 <= 0.22
        classified[_tmp & r9] = 1  #Node 17
        _tmp &= ~r9

        r10 = band1 <= 473
        classified[_tmp & r10] = 1  #Node 19
        classified[_tmp & ~r10] = 0  #Node 20

        # Left branch complete; cleanup
        del r2, r3, r4, r5, r6, r7, r8, r9, r10
        gc.collect()

        # Right branch of regression tree
        r1 = ~r1

        r11 = ndi_52 <= 0.23
        _tmp = r1 & r11

        r12 = band1 <= 334.5
        _tmp2 = _tmp & ~r12
        classified[_tmp2] = 0  #Node 23

        _tmp &= r12

        r13 = ndi_43 <= 0.54
        _tmp2 = _tmp & ~r13
        classified[_tmp2] = 0  #Node 25

        _tmp &= r13

        r14 = ndi_52 <= 0.12
        _tmp2 = _tmp & r14
        classified[_tmp2] = 1  #Node 27

        _tmp &= ~r14

        r15 = band3 <= 364.5
        _tmp2 = _tmp & r15

        r16 = band1 <= 129.5
        classified[_tmp2 & r16] = 1  #Node 31
        classified[_tmp2 & ~r16] = 0  #Node 32

        _tmp &= ~r15

        r17 = band1 <= 300.5
        _tmp2 = _tmp & ~r17
        _tmp &= r17
        classified[_tmp] = 1  #Node 33
        classified[_tmp2] = 0  #Node 34

        _tmp = r1 & ~r11

        r18 = ndi_52 <= 0.34
        classified[_tmp & ~r18] = 0  #Node 36
        _tmp &= r18

        r19 = band1 <= 249.5
        classified[_tmp & ~r19] = 0  #Node 38
        _tmp &= r19

        r20 = ndi_43 <= 0.45
        classified[_tmp & ~r20] = 0  #Node 40
        _tmp &= r20

        r21 = band3 <= 364.5
        classified[_tmp & ~r21] = 0  #Node 42
        _tmp &= r21

        r22 = band1 <= 129.5
        classified[_tmp & r22] = 1  #Node 44
        classified[_tmp & ~r22] = 0  #Node 45

        # Completed regression tree

        return classified

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