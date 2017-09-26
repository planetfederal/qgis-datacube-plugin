from qgis.core import QgsRasterLayer, QgsRasterFileWriter, QgsRasterPipe, QgsPoint, QgsRectangle
from datacubeplugin.layers import uriFromComponents
from qgiscommons2.files import tempFilename, tempFolderInTempFolder
from qgiscommons2.gui import startProgressBar, closeProgressBar, setProgressValue
import owslib.wcs as wcs
import os
from dateutil import parser
import json
import math
from qgis.PyQt.QtCore import pyqtSignal, QObject

class Layer():

    def __init__(self):
        self._files = {}

    def layerFile(self, extent=None):
        if extent in self._files:
            return self._files[extent]
        else:
            filename = tempFilename("tif")
            self._save(filename, extent)
            self._files[extent] = filename
            return filename

    def _save(self, filename, extent=None):
        filewriter = QgsRasterFileWriter(filename)
        pipe = QgsRasterPipe()
        layer = self.layer()
        provider = layer.dataProvider()
        extent = extent or layer.extent()
        xSize = extent.width() / layer.rasterUnitsPerPixelX()
        ySize = extent.height() / layer.rasterUnitsPerPixelY()
        pipe.set(provider.clone())
        filewriter.writeRaster(pipe, xSize, ySize, extent, provider.crs())

    def saveTo(self, folder):
        filename = os.path.join(folder, self.name.replace(":", "_"))
        self._save(filename)

    TILESIZE = 256
    def saveTiles(self, extent):
        folder = tempFolderInTempFolder()
        layer = self.layer()
        xSize = extent.width() / layer.rasterUnitsPerPixelX()
        ySize = extent.height() / layer.rasterUnitsPerPixelY()
        xTiles = math.ceil(xSize / self.TILESIZE)
        yTiles = math.ceil(ySize / self.TILESIZE)
        i = 0
        startProgressBar("Retrieving and preparing data [layer %s]" % self.name(), xTiles * yTiles)
        for x in xrange(xTiles):
            for y in xrange(yTiles):
                minX = extent.xMinimum() + x * layer.rasterUnitsPerPixelX() * self.TILESIZE
                maxX = min(extent.xMaximum(), extent.xMinimum() + (x + 1) * layer.rasterUnitsPerPixelX() * self.TILESIZE)
                minY = extent.yMinimum() + y * layer.rasterUnitsPerPixelY() * self.TILESIZE
                maxY = min(extent.yMaximum(), extent.yMinimum() + (y + 1) * layer.rasterUnitsPerPixelY() * self.TILESIZE)
                pt1 = QgsPoint(minX, minY)
                pt2 = QgsPoint(maxX, maxY)
                tileExtent = QgsRectangle(pt1, pt2)
                filename = os.path.join(folder, "%i_%i.tif" % (x, y))
                self._save(filename, tileExtent)
                i += 1
                setProgressValue(i)
        closeProgressBar()
        return folder

    def tilesCount(self, extent):
        layer = self.layer()
        xSize = extent.width() / layer.rasterUnitsPerPixelX()
        ySize = extent.height() / layer.rasterUnitsPerPixelY()
        xTiles = math.ceil(xSize / self.TILESIZE)
        yTiles = math.ceil(ySize / self.TILESIZE)
        return xTiles * yTiles

class WCSConnector():

    def __init__(self, url):
        self.url = url
        self._coverages = {}
        self.service = wcs.WebCoverageService(url, version='1.0.0')
        coverages = self.service.contents.keys()
        for name in coverages:
            coverage = self.service[name]
            self._coverages[name] = WCSCoverage(self.service, url, name, coverage)


    def coverages(self):
        return self._coverages.keys()

    def coverage(self, name):
        return self._coverages[name]

    def name(self):
        return self.url

    @staticmethod
    def isCompatible(endpoint):
        return endpoint.startswith("http")



class WCSCoverage():

    def __init__(self, service, url, coverageName, coverage):
        self.service = service
        self.url = url
        self.coverageName = coverageName
        self._timepositions = [s.replace("Z", "") for s in coverage.timepositions]
        self.bands = coverage.axisDescriptions[0].values
        print self.bands
        self.crs = coverage.supportedCRS[0]

    def name(self):
        return self.coverageName

    def timePositions(self):
        return self._timepositions

    def layerForTimePosition(self, time):
        return WCSLayer(self, time)

class WCSLayer(Layer):

    def __init__(self, coverage, time):
        Layer.__init__(self)
        self.coverage = coverage
        self._time = time
        self._layer = None

    def source(self):
        uri = uriFromComponents(self.coverage.url, self.coverage.name(), self.time())
        return str(uri.encodedUri())

    def name(self):
        return self.time()

    def time(self):
        return self._time

    def datasetName(self):
        return self.coverage.url

    def coverageName(self):
        return self.coverage.name()

    def bands(self):
        return self.coverage.bands

    def layer(self):
        if self._layer is None:
            self._layer = QgsRasterLayer(self.source(), self.name(), "wcs")
        return self._layer


class FileConnector():

    def __init__(self, folder):
        self.folder = folder
        self._coverages = {}
        for f in os.listdir(folder):
            path = os.path.join(folder, f)
            if os.path.isdir(path) and os.path.exists(os.path.join(path, 'bands.json')):
                self._coverages[f] = FileCoverage(path)

    def coverages(self):
        return self._coverages.keys()

    def coverage(self, name):
        return self._coverages[name]

    def name(self):
        return self.folder

    @staticmethod
    def isCompatible(endpoint):
        return os.path.exists(endpoint)


class FileCoverage():

    def __init__(self, folder):
        self.folder = folder
        self._timepositions = []
        with open(os.path.join(folder, 'bands.json')) as f:
            self.bands = json.load(f)
        self._exts = {}
        for f in os.listdir(folder):
            path = os.path.join(folder, f)
            if not os.path.isdir(path):
                root, ext = os.path.splitext(f)
                try:
                    dt = parser.parse(root.replace("_", ":"))
                    self._exts[root] = ext
                    self._timepositions.append(root)
                except ValueError:
                    pass

    def name(self):
        return os.path.basename(self.folder)

    def timePositions(self):
        return self._timepositions

    def layerForTimePosition(self, time):
        return FileLayer(self.folder, time  + self._exts[time], self)

class FileLayer(Layer):

    def __init__(self, folder, filename, coverage):
        Layer.__init__(self)
        self.folder = folder
        self._time = os.path.splitext(filename)[0].replace("_", ":").replace("Z", "")
        self._filename = filename
        self.coverage = coverage

    def source(self):
        return os.path.join(self.folder, self._filename)

    def bands(self):
        return self.coverage.bands

    def name(self):
        return self.time()

    def time(self):
        return self._time

    def datasetName(self):
        return os.path.dirname(self.folder)

    def coverageName(self):
        return os.path.basename(self.folder)

    def layer(self):
        return QgsRasterLayer(self.source(), self.name(), "gdal")


connectors = [WCSConnector, FileConnector]