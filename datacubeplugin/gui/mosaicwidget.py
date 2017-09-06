import os
from qgis.core import *
from qgis.utils import iface
from qgis.PyQt import uic
from datacubeplugin import layers
from qgiscommons2.layers import layerFromSource, WrongLayerSourceException
from dateutil import parser
import struct
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly
from datacubeplugin.gui.selectextentmaptool import SelectExtentMapTool

pluginPath = os.path.dirname(os.path.dirname(__file__))
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'mosaicwidget.ui'))

def mostRecent(values, times):
    return values[-1]

def leastRecent(values, times):
    return values[0]

mosaicFunctions = [mostRecent, leastRecent]
mosaicFunctionNames = ["Most recent", "Least recent"]


class MosaicWidget(BASE, WIDGET):

    def __init__(self, parent=None):
        super(MosaicWidget, self).__init__(parent)
        self.setupUi(self)
        self.buttonCreateMosaic.clicked.connect(self.createMosaic)
        self.comboCoverage.currentIndexChanged.connect(self.updateDates)
        self.comboMosaicType.addItems(mosaicFunctionNames)
        self.buttonLayerExtent.clicked.connect(self.useLayerExtent)
        self.buttonCanvasExtent.clicked.connect(self.useCanvasExtent)
        self.buttonSelectExtentOnCanvas.clicked.connect(self.selectExtentOnCanvas)
        self.mapTool = SelectExtentMapTool(iface.mapCanvas(), self)

        iface.mapCanvas().mapToolSet.connect(self.unsetTool)

    def useCanvasExtent(self):
        self.setExent(iface.mapCanvas().extent())

    def useLayerExtent(self):
        layer = iface.activeLayer()
        if layer:
            self.setExtent(layer.extent())

    def unsetTool(self, tool):
        if not isinstance(tool, SelectExtentMapTool):
            self.buttonSelectExtentOnCanvas.setChecked(False)

    def selectExtentOnCanvas(self):
        self.buttonSelectExtentOnCanvas.setChecked(True)
        iface.mapCanvas().setMapTool(self.mapTool)

    def setExtent(self, extent):
        self.textXMin.setText(str(extent.xMinimum()))
        self.textYMin.setText(str(extent.yMinimum()))
        self.textXMax.setText(str(extent.xMaximum()))
        self.textYMax.setText(str(extent.yMaximum()))

    def _loadedLayersForCoverage(self, name, coverageName):
        loadedLayers = []
        for layer in layers._layers[name][coverageName]:
            source = layer.source()
            try:
                layer = layerFromSource(source)
                loadedLayers.append(layer)
            except WrongLayerSourceException:
                pass
        loadedLayers.sort(key=lambda lay: lay[1])
        return loadedLayers

    def updateDates(self):
        txt = self.comboCoverage.currentText()
        name, coverageName = txt.split(" : ")
        layers = self._loadedLayersForCoverage(name, coverageName)
        if layers:
            years = [parser.parse(lay.time()).year for lay in layers]
            minYear = min(years)
            maxYear = max(years)
            self.sliderStartDate.setMinimum(minYear)
            self.sliderStartDate.setMaximum(maxYear)
            self.sliderStartDate.setValue(minYear)
            self.sliderEndDate.setMinimum(minYear)
            self.sliderEndDate.setMaximum(maxYear)
            self.sliderEndDate.setValue(maxYear)

    def createMosaic(self):
        extent = self.extentBox.currentExtent()
        txt = self.comboCoverage.currentText()
        name, coverageName = txt.split(" : ")
        layers = self._loadedLayersForCoverage(name, coverageName)
        minYear = self.sliderStartDate.value()
        maxYear = self.sliderEndDate.value()
        layerFiles = []
        for layer in layers:
            time = parser.parse(layer.time())
            if (time.year >= minYear and time.year <= maxYear):
                layerFiles.append(layer.layerFile(extent))
        mosaicFunction = mosaicFunctions[self.comboMosaicType.currentIndex()]

def scanraster(filename, bandidx):
    dataset = gdal.Open(filename, GA_ReadOnly)
    band = dataset.GetRasterBand(bandidx)
    nodata = band.GetNoDataValue()
    bandtype = gdal.GetDataTypeName(band.DataType)
    for y in xrange(band.YSize):
        scanline = band.ReadRaster(0, y, band.XSize, 1, band.XSize, 1, band.DataType)
        if bandtype == 'Byte':
            values = struct.unpack('B' * band.XSize, scanline)
        elif bandtype == 'Int16':
            values = struct.unpack('h' * band.XSize, scanline)
        elif bandtype == 'UInt16':
            values = struct.unpack('H' * band.XSize, scanline)
        elif bandtype == 'Int32':
            values = struct.unpack('i' * band.XSize, scanline)
        elif bandtype == 'UInt32':
            values = struct.unpack('I' * band.XSize, scanline)
        elif bandtype == 'Float32':
            values = struct.unpack('f' * band.XSize, scanline)
        elif bandtype == 'Float64':
            values = struct.unpack('d' * band.XSize, scanline)
        if values[0] == nodata:
            value = None
        else:
            value = value[0]
        yield value

mosaicWidget = MosaicWidget(iface.mainWindow())

