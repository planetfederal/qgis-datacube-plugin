import os
from qgis.core import *
from qgis.utils import iface
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QHBoxLayout
from qgis.PyQt.QtCore import pyqtSignal

import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
#import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib import axes
from datacubeplugin import plotparams
from datacubeplugin import layers
from qgiscommons2.layers import layerFromSource, WrongLayerSourceException
from qgiscommons2.gui import askForFiles, execute, startProgressBar, closeProgressBar, setProgressValue
from dateutil import parser
import csv
from datetime import datetime
import copy
import time as timelib
import logging
import traceback

pluginPath = os.path.dirname(os.path.dirname(__file__))
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'plotwidget.ui'))

logger = logging.getLogger('datacube')

class PlotWidget(BASE, WIDGET):

    plotDataChanged = pyqtSignal(datetime, datetime, float ,float)

    def __init__(self, parent=None):
        super(PlotWidget, self).__init__(parent)
        self.setupUi(self)
        self.data = {}
        self.rectangle = None
        self.pt = None
        self.dataset = None
        self.coverage = None
        self.parameter = None
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        layout = QHBoxLayout()
        layout.addWidget(self.canvas)
        self.canvasWidget.setLayout(layout)
        self.buttonSave.setIcon(QgsApplication.getThemeIcon('/mActionFileSave.svg'))
        self.buttonSave.clicked.connect(self.savePlotData)
        self.buttonSave.setEnabled(False)

    def savePlotData(self):
        filename = askForFiles(self, msg="Save plot data", isSave=True, allowMultiple=False, exts = "csv")
        if filename:
            with open(filename, 'wb') as csvfile:
                writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
                for time, values in self.data.iteritems():
                    for v in values:
                        x,y = v[1]
                        writer.writerow([time, x, y, v[0]])

    def plot(self, _filter=None, parameter=None, coverage=None, dataset=None, pt=None, rectangle=None):
        self.parameter = parameter or self.parameter
        self.coverage = coverage or self.coverage
        self.dataset = dataset or self.dataset
        self.pt = pt
        self.rectangle = rectangle
        self.filter = _filter
        execute(self._plot)

    def _plot(self):
        self.figure.clear()
        self.canvas.draw()
        self.buttonSave.setEnabled(False)

        if self.pt is None and self.rectangle is None:
            return

        if self.parameter is None or self.coverage is None or self.dataset is None:
            return

        canvasLayers = []
        try:
            allCoverageLayers = layers._layers[self.dataset][self.coverage]
        except KeyError:
            return
        for layerdef in allCoverageLayers:
            source = layerdef.source()
            time = parser.parse(layerdef.time())
            try:
                layer = layerFromSource(source)
                canvasLayers.append((layerdef, time))
            except WrongLayerSourceException:
                pass

        if not canvasLayers:
            return

        minDate = None
        maxDate = None
        minY = None
        maxY = None
        if self.filter:
            if self.filter[0] is not None:
                minDate = self.filter[0]
            if self.filter[1] is not None:
                maxDate = self.filter[1]
            minY = self.filter[2] or None
            maxY = self.filter[3] or None

        try:
            bands = allCoverageLayers[0].bands()

            if self.rectangle is None:
                self.data = {}
                startProgressBar("Retrieving plot data", len(canvasLayers))
                for (i, (layerdef, time)) in enumerate(canvasLayers):
                    if ((minDate is not None and time < minDate) or
                        (maxDate is not None and time > maxDate)):
                        continue
                    start = timelib.time()
                    layer = layerdef.layer()
                    v = self.parameter.value(layer, self.pt, bands)
                    end = timelib.time()
                    logger.info("Plot data for layer %i retrieved in %s seconds" % (i, str(end-start)))
                    setProgressValue(i + 1)
                    if v is not None:
                        self.data[time] = [(v, (self.pt.x(), self.pt.y()))]
                closeProgressBar()
                if not self.data:
                    return
                y = [v[0][0] for v in self.data.values()]
                ymin = min(y)
                ymax = max(y)
            else:
                self.data = {}
                startProgressBar("Retrieving plot data", len(canvasLayers))
                for (i, (layerdef, time)) in enumerate(canvasLayers):
                    if ((minDate is not None and time < minDate) or
                        (maxDate is not None and time > maxDate)):
                        continue
                    start = timelib.time()
                    layer = layerdef.layer()
                    if not self.rectangle.intersects(layer.extent()):
                        continue
                    rectangle = self.rectangle.intersect(layer.extent())
                    xsteps = int(rectangle.width() / layer.rasterUnitsPerPixelX())
                    ysteps = int(rectangle.height() / layer.rasterUnitsPerPixelY())
                    filename = layerdef.layerFile(rectangle)
                    roi = layers.getBandArrays(filename)
                    end = timelib.time()
                    logger.info("ROI data for layer %i retrieved in %s seconds" % (i, str(end-start)))
                    start = timelib.time()
                    setProgressValue(i + 1)
                    self.data[time] = []
                    for col in range(xsteps):
                        x = rectangle.xMinimum() + col * layer.rasterUnitsPerPixelX()
                        for row in range(ysteps):
                            y = rectangle.yMinimum() + row * layer.rasterUnitsPerPixelY()
                            pixel = QgsPoint(col, row)
                            value = self.parameter.value(roi, pixel, bands)
                            if value:
                                self.data[time].append((value, (x, y)))
                    end = timelib.time()
                    logger.info("Plot data computed from ROI data in %s seconds" % (str(end-start)))
                closeProgressBar()
                if not self.data:
                    return
                y = [[v[0] for v in lis] for lis in self.data.values()]
                ymin = min([min(v) for v in y])
                ymax = max([max(v) for v in y])

            xmin = min(self.data.keys())
            xmax = max(self.data.keys())

            if self.filter is None:
                self.plotDataChanged.emit(xmin, xmax, ymin, ymax)
            self.dataToPlot = copy.deepcopy(self.data)

            if self.filter:
                for key, values in self.data.iteritems():
                    for v in values[::-1]:
                        if ((minY is not None and  v[0] < minY)
                            or (maxY is not None and v[0] > maxY)):
                            try:
                                self.dataToPlot[key].remove(v)
                            except:
                                pass

            datesToRemove = []
            for key, values in self.dataToPlot.iteritems():
                if not values:
                    datesToRemove.append(key)
            for d in datesToRemove:
                del self.dataToPlot[d]

            axes = self.figure.add_subplot(1, 1, 1)
            x = matplotlib.dates.date2num(self.dataToPlot.keys())
            if self.rectangle is None:
                y = [v[0][0] for v in self.dataToPlot.values() if v]
                axes.scatter(self.dataToPlot.keys(), y)
            else:
                sortedKeys = sorted(self.dataToPlot.keys())
                y = [[v[0] for v in self.dataToPlot[k]] for k in sortedKeys]
                axes.boxplot(y)
                axes.set_xticklabels([str(d).split(" ")[0] for d in sortedKeys], rotation=70)
            self.figure.autofmt_xdate()
        except Exception, e:
            traceback.print_exc()
            closeProgressBar()
            return

        self.buttonSave.setEnabled(True)
        self.canvas.draw()

plotWidget = PlotWidget(iface.mainWindow())