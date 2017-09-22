import os
import numpy as np
from qgis.core import *
from qgis.gui import QgsMessageBar
from qgis.utils import iface
from qgis.PyQt import uic
from datacubeplugin import layers
from qgiscommons2.layers import layerFromSource, WrongLayerSourceException
from qgiscommons2.files import tempFilename
from dateutil import parser
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly
from datacubeplugin.gui.selectextentmaptool import SelectExtentMapTool
from datacubeplugin.mosaicfunctions import mosaicFunctions
from datacubeplugin.utils import addLayerIntoGroup, dateFromDays, daysFromDate
from datacubeplugin.layers import getRowArray
from qgiscommons2.gui import execute
from collections import defaultdict

pluginPath = os.path.dirname(os.path.dirname(__file__))
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'mosaicwidget.ui'))

class MosaicWidget(BASE, WIDGET):

    def __init__(self, parent=None):
        super(MosaicWidget, self).__init__(parent)
        self.setupUi(self)
        self.buttonCreateMosaic.clicked.connect(self.createMosaic)
        self.comboCoverage.currentIndexChanged.connect(self.updateDates)
        self.comboMosaicType.addItems([f.name for f in mosaicFunctions])
        self.buttonLayerExtent.clicked.connect(self.useLayerExtent)
        self.buttonCanvasExtent.clicked.connect(self.useCanvasExtent)
        self.buttonSelectExtentOnCanvas.clicked.connect(self.selectExtentOnCanvas)
        self.mapTool = SelectExtentMapTool(iface.mapCanvas(), self)
        self.sliderStartDate.valueChanged.connect(self.startDateChanged)
        self.sliderEndDate.valueChanged.connect(self.endDateChanged)

        iface.mapCanvas().mapToolSet.connect(self.unsetTool)

    def startDateChanged(self):
        self.txtStartDate.setText(str(dateFromDays(self.sliderStartDate.value())).split(" ")[0])

    def endDateChanged(self):
        self.txtEndDate.setText(str(dateFromDays(self.sliderEndDate.value())).split(" ")[0])

    def useCanvasExtent(self):
        self.setExtent(iface.mapCanvas().extent())

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
        for layerdef in layers._layers[name][coverageName]:
            source = layerdef.source()
            try:
                layer = layerFromSource(source)
                loadedLayers.append(layerdef)
            except WrongLayerSourceException:
                pass
        loadedLayers.sort(key=lambda lay: lay.time())
        return loadedLayers

    def updateDates(self):
        txt = self.comboCoverage.currentText()
        name, coverageName = txt.split(" : ")
        layers = self._loadedLayersForCoverage(name, coverageName)
        if layers:
            dates = [parser.parse(lay.time()) for lay in layers]
            minDays = daysFromDate(min(dates))
            maxDays = daysFromDate(max(dates))
            self.sliderStartDate.setMinimum(minDays)
            self.sliderStartDate.setMaximum(maxDays)
            self.sliderStartDate.setValue(minDays)
            self.sliderEndDate.setMinimum(minDays)
            self.sliderEndDate.setMaximum(maxDays)
            self.sliderEndDate.setValue(maxDays)

    def createMosaic(self):
        execute(self._createMosaic)
        iface.messageBar().pushMessage("", "Mosaic has been correctly created and added to project.",
                                               level=QgsMessageBar.INFO)

    def _createMosaic(self):
        mosaicFunction = mosaicFunctions[self.comboMosaicType.currentIndex()]
        def getValue(textbox, paramName):
            try:
                v = float(textbox.text())
                return v
            except:
                iface.messageBar().pushMessage("", "Wrong value for parameter %s: %s" % (paramName, textbox.text()),
                                               level=QgsMessageBar.WARNING)
                raise
        try:
            widgets = [self.textXMin, self.textXMax, self.textYMin, self.textYMax]
            names = ["X min", "X max", "Y min", "Y max"]
            xmin, xmax, ymin, ymax = [getValue(w, n) for w, n in zip(widgets, names)]
        except:
            return
        extent = QgsRectangle(QgsPoint(xmin, ymin), QgsPoint(xmax, ymax))
        txt = self.comboCoverage.currentText()
        name, coverageName = txt.split(" : ")
        loadedLayers = self._loadedLayersForCoverage(name, coverageName)
        minDays = self.sliderStartDate.value()
        maxDays = self.sliderEndDate.value()
        validLayers = []
        for layer in loadedLayers:
            time = daysFromDate(parser.parse(layer.time()))
            if (time >= minDays and time <= maxDays):
                validLayers.append(layer)

        if validLayers:
            ds = gdal.Open(validLayers[0].layerFile(extent), GA_ReadOnly)
            datatype = ds.GetRasterBand(1).DataType
            bandCount = ds.RasterCount
            width = ds.RasterXSize
            height = ds.RasterYSize
            geotransform = ds.GetGeoTransform()
            projection = ds.GetProjection()
            newBands = []
            bandNames = layers._coverages[name][coverageName].bands
            newBands = defaultdict(list)
            try:
                qaBand = bandNames.index("pixel_qa")
            except:
                qaBand = None
            for row in range(height):
                if qaBand is not None:
                    qaData = [getRowArray(lay.layerFile(extent), qaBand, row, width) for lay in validLayers]
                else:
                    qaData = None
                for band, bandName in enumerate(bandNames):
                    bandData = [getRowArray(lay.layerFile(extent), band + 1, row, width) for lay in validLayers]
                    newBands[bandName].append(mosaicFunction.compute(bandData, qaData))
                    bandData = None
            driver = gdal.GetDriverByName("GTiff")
            dstFilename = tempFilename("tif")
            dstDs= driver.Create(dstFilename, width, height, bandCount, datatype)

            for i, band in enumerate(bandNames):
                gdalBand = dstDs.GetRasterBand(i+1)
                newBand = np.vstack(newBands[band])
                gdalBand.WriteArray(newBand)
                gdalBand.FlushCache()
                del newBand

            dstDs.SetGeoTransform(geotransform)
            dstDs.SetProjection(projection)
            del dstDs

            layer = QgsRasterLayer(dstFilename, "Mosaic [%s]" % mosaicFunction.name, "gdal")
            addLayerIntoGroup(layer, validLayers[0].coverageName())



mosaicWidget = MosaicWidget(iface.mainWindow())

