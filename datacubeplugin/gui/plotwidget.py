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


pluginPath = os.path.dirname(os.path.dirname(__file__))
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'plotwidget.ui'))


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
                        pt = v[1]
                        writer.writerow([time, pt.x(), pt.y(), v[0]])

    def setRectangle(self, rect):
        self.rectangle = rect
        self.pt = None
        self.plot()

    def setPoint(self, pt):
        self.pt = pt
        self.rectangle = None
        self.plot()

    def plot(self, filter=None, parameter=None, coverage=None, dataset=None):
        self.parameter = parameter or self.parameter
        self.coverage = coverage or self.coverage
        self.dataset = dataset or self.dataset
        execute(lambda: self._plot(filter))

    def _plot(self, filter=None):
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
            time = layerdef.time()
            try:
                layer = layerFromSource(source)
                canvasLayers.append((layerdef, time))
            except WrongLayerSourceException:
                pass

        if not canvasLayers:
            print 3
            return

        try:
            if filter is None:
                bands = allCoverageLayers[0].bands()

                if self.rectangle is None:
                    self.data = {}
                    startProgressBar("Retrieving plot data", len(canvasLayers))
                    for (i, (layerdef, time)) in enumerate(canvasLayers):
                        layer = layerdef.layer()
                        v = self.parameter.value(layer, self.pt, bands)
                        setProgressValue(i + 1)
                        if v is not None:
                            time = parser.parse(time)
                            self.data[time] = [(v, self.pt)]
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
                        layer = layerdef.layer()
                        xsteps = int(self.rectangle.width() / layer.rasterUnitsPerPixelX())
                        ysteps = int(self.rectangle.height() / layer.rasterUnitsPerPixelY())
                        filename = layerdef.layerFile(self.rectangle)
                        roi = layers.getBandArrays(filename)
                        setProgressValue(i + 1)
                        time = parser.parse(time)
                        self.data[time] = []
                        for col in range(xsteps):
                            x = self.rectangle.xMinimum() + col * layer.rasterUnitsPerPixelX()
                            for row in range(ysteps):
                                y = self.rectangle.yMinimum() + row * layer.rasterUnitsPerPixelY()
                                pt = QgsPoint(x, y)
                                pixel = QgsPoint(col, row)
                                value = self.parameter.value(roi, pixel, bands)
                                if value:
                                    self.data[time].append((value, pt))
                    closeProgressBar()
                    if not self.data:
                        return
                    y = [[v[0] for v in lis] for lis in self.data.values()]
                    ymin = min([min(v) for v in y])
                    ymax = max([max(v) for v in y])

                xmin = min(self.data.keys())
                xmax = max(self.data.keys())
                self.plotDataChanged.emit(xmin, xmax, ymin, ymax)
                self.dataToPlot = copy.deepcopy(self.data)
            else:
                self.dataToPlot = copy.deepcopy(self.data)
                datesToRemove = []
                for d in self.data.keys():
                    if d < filter[0] or d > filter[1]:
                        datesToRemove.append(d)
                for d in datesToRemove:
                    del self.dataToPlot[d]
                for key, values in self.data.iteritems():
                    for v in values[::-1]:
                        if v[0] < filter[2] or v[0] > filter[3]:
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
                axes.plot_date(x,y)
            else:
                y = [[v[0] for v in lis] for lis in self.dataToPlot.values()]
                axes.boxplot(y, positions = x)
                axes.set_xticklabels([str(d).split(" ")[0] for d in self.dataToPlot.keys()], rotation=45)

            self.figure.autofmt_xdate()
        except:
            raise
            return

        self.buttonSave.setEnabled(True)
        self.canvas.draw()

plotWidget = PlotWidget(iface.mainWindow())