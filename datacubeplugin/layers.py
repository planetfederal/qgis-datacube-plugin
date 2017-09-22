from collections import defaultdict
from qgis.core import  QgsDataSourceURI
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly

_layers = {}
_coverages = {}
_rendering = defaultdict(defaultdict)


def uriFromComponents(url, coverageName, time):
    uri = QgsDataSourceURI()
    uri.setParam("url", url)
    uri.setParam("identifier", coverageName)
    uri.setParam("time", time)
    return uri

def getRowArray(filename, bandidx, row, width):
    ds = gdal.Open(filename, GA_ReadOnly)
    band = ds.GetRasterBand(bandidx)
    array = band.ReadAsArray(0, row, width, 1)
    return array

def getArray(filename, bandidx):
    ds = gdal.Open(filename, GA_ReadOnly)
    band = ds.GetRasterBand(bandidx)
    array = band.ReadAsArray()
    return array

def getBandArrays(filename):
    ds = gdal.Open(filename, GA_ReadOnly)
    arrays = []
    for b in range(ds.RasterCount):
        band = ds.GetRasterBand(b+1)
        arrays.append(band.ReadAsArray())
    return arrays