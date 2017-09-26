from qgis.core import QgsRaster, QgsRasterBlock
import numpy as np
import os

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
        return v is None or v not in [66, 68, 130, 132]

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

        band1 = getB(layer, pt, bands)
        band2 = getG(layer, pt, bands)
        band3 = getR(layer, pt, bands)
        band4 = getNIR(layer, pt, bands)
        band5 = getSWIR1(layer, pt, bands)
        band7 = getSWIR2(layer, pt, bands)

        if None in [band1, band2, band3, band4, band5, band7]:
            return None

        ndi_52 = _bandRatio(band5, band2)
        ndi_43 = _bandRatio(band4, band3)
        ndi_72 = _bandRatio(band7, band2)

        r1 = ndi_52 <= -0.01
        r2 = band1 <= 2083.5
        r3 = band7 <= 323.5
        r4 = ndi_43 <= 0.61
        r5 = band1 <= 1400.5
        r6 = ndi_43 <= -0.01
        r7 = ndi_72 <= -0.23
        r8 = band1 <= 379
        r9 = ndi_43 <= 0.22
        r10 = band1 <= 473
        r11 = ndi_52 <= 0.23
        r12 = band1 <= 334.5
        r13 = ndi_43 <= 0.54
        r14 = ndi_52 <= 0.12
        r15 = band3 <= 364.5
        r16 = band1 <= 129.5
        r17 = band1 <= 300.5
        r18 = ndi_52 <= 0.34
        r19 = band1 <= 249.5
        r20 = ndi_43 <= 0.45
        r21 = band3 <= 364.5
        r22 = band1 <= 129.5

        if r1:
            if not r2:
                return 0 #Node 3
            else:
                if r3:
                    if r4:
                        return 1  #Node 6
                    else:
                        return 0  #Node 7
                else:
                    if not r5:
                        if r6:
                            return  1  #Node 10
                        else:
                            return 0  #Node 11
                    else:
                        if r7:
                            if r9:
                                return 1  #Node 17
                            else:
                                if r10:
                                    return 1  #Node 19
                                else:
                                    return 0  #Node 20
                        else:
                            if r8:
                                return 1  #Node 14
                            else:
                                return 0  #Node 15
        else:
            if r11:
                if r12:
                    if r13:
                        if r14:
                            return 1 #Node 27
                        else:
                            if r15:
                                if r16:
                                    return 1  #Node 31
                                else:
                                    return 0  #Node 32
                            else:
                                if r17:
                                    return 1  #Node 33
                                else:
                                    return 0  #Node 34
                    else:
                        return 0  #Node 25
                else:
                    return 0  #Node 23
            else:
                if r18:
                    if r19:
                        if r20:
                            if r21:
                                if r22:
                                    return 1 #Node 44
                                else:
                                    return 0 #Node 45
                            else:
                                return 0  #Node 42
                        else:
                            return 0  #Node 40
                    else:
                        return 0  #Node 38
                else:
                    return 0  #Node 36



class TSM(PlotParameter):

    name = "TSM"

    def _value(self, layer, pt, bands):
        g = getG(layer, pt, bands)
        r = getR(layer, pt, bands)
        if r is None or g is None:
            return None
        tsmi = (r + g) * 0.0001 / 2
        tsm = 3983 * tsmi**1.6246
        return tsm

csvFilepath = os.path.join(os.path.dirname(__file__), 'data', 'endmembers_landsat.csv')

_endMembers = np.loadtxt(csvFilepath, delimiter=',')  # Creates a 64 x 3 matrix

def fractionalCover(layer, pt, bands):

    b = getB(layer, pt, bands)
    g = getG(layer, pt, bands)
    r = getR(layer, pt, bands)
    nir = getNIR(layer, pt, bands)
    swir1 = getSWIR1(layer, pt, bands)
    swir2 = getSWIR2(layer, pt, bands)

    if None in [r, g, b, nir, swir1, swir2]:
        return None

    endMembers = np.copy(_endMembers)

    band_stack = np.array([[b], [g], [r],[nir],[swir1][swir2]]).transpose()

    for band in range(6):
        band_stack = np.hstack((band_stack, np.expand_dims(np.log(band_stack[:, band]), axis=1)))
    for band in range(6):
        band_stack = np.hstack(
            (band_stack, np.expand_dims(np.multiply(band_stack[:, band], band_stack[:, band + 6]), axis=1)))
    for band in range(6):
        for b2 in range(band + 1, 6):
            band_stack = np.hstack(
                (band_stack, np.expand_dims(np.multiply(band_stack[:, band], band_stack[:, b2]), axis=1)))
    for band in range(6):
        for b2 in range(band + 1, 6):
            band_stack = np.hstack(
                (band_stack, np.expand_dims(np.multiply(band_stack[:, band + 6], band_stack[:, b2 + 6]), axis=1)))
    for band in range(6):
        for b2 in range(band + 1, 6):
            band_stack = np.hstack((band_stack, np.expand_dims(
                np.divide(band_stack[:, b2] - band_stack[:, band], band_stack[:, b2] + band_stack[:, band]), axis=1)))

    band_stack = np.nan_to_num(band_stack)  # Now a n x 63 matrix (assuming one acquisition)

    ones = np.ones(band_stack.shape[0])
    ones = ones.reshape(ones.shape[0], 1)
    band_stack = np.concatenate((band_stack, ones), axis=1)  # Now a n x 64 matrix (assuming one acquisition)

    SumToOneWeight = 0.02
    ones = np.ones(endMembers.shape[1]) * SumToOneWeight
    ones = ones.reshape(1, endMembers.shape[1])
    end_members = np.concatenate((endMembers, ones), axis=0).astype(np.float32)

    result = np.zeros((band_stack.shape[0], end_members.shape[1]), dtype=np.float32)  # Creates an n x 3 matrix

    for i in range(band_stack.shape[0]):
        result[i, :] = (opt.nnls(end_members, band_stack[i, :])[0].clip(0, 2.54) * 100).astype(np.int16)

    pv = result[:, :, 0]
    npv = result[:, :, 1]
    bs = result[:, :, 2]

    return bs, pv, npv



class BS(PlotParameter):

    name = "BS"

    def _value(self, layer, pt, bands):
        fc = fractionalCover(layer, pt, bands)
        if fc is None:
            return None
        return fc[0]

class PV(PlotParameter):

    name = "PV"

    def _value(self, layer, pt, bands):
        fc = fractionalCover(layer, pt, bands)
        if fc is None:
            return None
        return fc[1]

class NPV(PlotParameter):

    name = "NPV"

    def _value(self, layer, pt, bands):
        fc = fractionalCover(layer, pt, bands)
        if fc is None:
            return None
        return fc[2]

def getParameters(bands):
    parameters = [BandValue(b) for b in bands]
    parameters.extend([NDVI(), NDBI(), EVI(), NDWI(), WOFS(), TSM(), BS(), PV(), NPV()])
    return parameters