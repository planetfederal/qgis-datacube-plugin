from qgis.core import QgsRasterLayer, QgsRasterFileWriter, QgsRasterPipe
from datacubeplugin.layers import uriFromComponents
from qgiscommons2.files import tempFilename
import owslib.wcs as wcs
import os
from dateutil import parser

class WCSConnector():

    def __init__(self, url):
        self.url = url
        self._coverages = {}
        w = wcs.WebCoverageService(url, version='1.0.0')
        coverages = w.contents.keys()
        for name in coverages:
            coverage = w[name]
            self._coverages[name] = WCSCoverage(url, name, coverage)


    def coverages(self):
        return self._coverages.keys()

    def coverage(self, name):
        return self._coverages[name]

    def name(self):
        return self.url

    @staticmethod
    def isCompatible(endpoint):
        #TODO
        return False



class WCSCoverage():

    def __init__(self, url, coverageName, coverage):
        self.url = url
        self.coverageName = coverageName
        self._timepositions = coverage.timepositions

    def timePositions(self):
        return self._timepositions

    def layerForTimePosition(self, time):
        return WCSLayer(self.url, self.coverageName, time)

class WCSLayer():

    def __init__(self, url, coverageName, time):
        self.url = url
        self._coverageName = coverageName
        self._time = time

    def source(self):
        uri = uriFromComponents(self.url, self.coverageName(), self.time())
        return str(uri.encodedUri())

    def name(self):
        return self.time()

    def time(self):
        return self._time

    def datasetName(self):
        return self.url

    def coverageName(self):
        return self._coverageName

    def layer(self):
        return QgsRasterLayer(self.source(), self.name(), "wcs")

    _files = {}
    def layerFile(self, extent=None):
        if extent in self._files:
            return self._files[extent]
        else:
            filename = tempFilename("tif")
            bbox = [extent.xMinimum(), extent.yMinimum(), extent.xMaximum(), extent.yMaximum()]
            output=wcs.getCoverage(identifier=self.coverageName(),time=[self.time()],bbox=bbox,format='GeoTIFF')
            with open(filename,'wb') as f:
                f.write(output.read())
            self._files[extent] = filename
            return filename

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

class FileLayer():

    def __init__(self, folder, filename):
        self.folder = folder
        self._time = os.path.splitext(filename)[0].replace("_", ":")
        self._filename = filename

    def source(self):
        return os.path.join(self.folder, self._filename)

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

    _files = {}
    def layerFile(self, extent=None):
        if extent is None:
            return self.source()
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

connectors = [WCSConnector, FileConnector]