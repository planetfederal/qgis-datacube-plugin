from qgis.core import QgsRasterLayer, QgsRasterFileWriter, QgsRasterPipe
from datacubeplugin.layers import uriFromComponents
from qgiscommons2.files import tempFilename
import owslib.wcs as wcs
import os
from dateutil import parser

class Layer():

    def __init__(self):
        self._files = {}

    def layerFile(self, extent=None):
        if extent in self._files:
            return self._files[extent]
        else:
            filename = tempFilename("tif")
            filewriter = QgsRasterFileWriter(filename)
            pipe = QgsRasterPipe()
            layer = self.layer()
            provider = layer.dataProvider()
            xSize = extent.width() / layer.rasterUnitsPerPixelX()
            ySize = extent.width() / layer.rasterUnitsPerPixelY()
            pipe.set(provider.clone())
            filewriter.writeRaster(pipe, xSize, ySize, extent, provider.crs())
            self._files[extent] = filename
            return filename

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
        self.crs = coverage.supportedCRS[0]

    def timePositions(self):
        return self._timepositions

    def layerForTimePosition(self, time):
        return WCSLayer(self, time)

class WCSLayer(Layer):

    def __init__(self, coverage, time):
        Layer.__init__(self)
        self.coverage = coverage
        self._time = time

    def source(self):
        uri = uriFromComponents(self.coverage.url, self.coverage.coverageName, self.time())
        return str(uri.encodedUri())

    def bands(self):
        return self.coverage.bands

    def name(self):
        return self.time()

    def time(self):
        return self._time

    def datasetName(self):
        return self.coverage.url

    def coverageName(self):
        return self.coverage.coverageName

    def layer(self):
        return QgsRasterLayer(self.source(), self.name(), "wcs")


class FileConnector():

    def __init__(self, folder):
        self.folder = folder
        self._coverages = {}
        for f in os.listdir(folder):
            path = os.path.join(folder, f)
            if os.path.isdir(path):
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

    def timePositions(self):
        return self._timepositions

    def layerForTimePosition(self, time):
        return FileLayer(self.folder, time  + self._exts[time])

class FileLayer(Layer):

    def __init__(self, folder, filename):
        Layer.__init__(self)
        self.folder = folder
        self._time = os.path.splitext(filename)[0].replace("_", ":").replace("Z", "")
        self._filename = filename
        self._bands = ["Band 1"]

    def source(self):
        return os.path.join(self.folder, self._filename)

    def bands(self):
        return self._bands

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