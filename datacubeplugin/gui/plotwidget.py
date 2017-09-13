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
from qgiscommons2.gui import askForFiles
from dateutil import parser
import csv
from datetime import datetime

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

    def setLayer(self, dataset, coverage):
        self.dataset = dataset
        self.coverage = coverage
        self.plot()

    def setParameter(self, parameter):
        self.parameter = parameter
        self.plot()

    def plot(self, filter=None):

        if self.parameter is None or self.coverage is None or self.dataset is None:
            self.buttonSave.setEnabled(False)
            return

        self.figure.clear()

        canvasLayers = []
        try:
            allCoverageLayers = layers._layers[self.dataset][self.coverage]
        except KeyError:
            self.buttonSave.setEnabled(False)
            return
        for layerdef in allCoverageLayers:
            source = layerdef.source()
            time = layerdef.time()
            try:
                layer = layerFromSource(source)
                canvasLayers.append((layer, time))
            except WrongLayerSourceException:
                pass

        if not canvasLayers:
            self.buttonSave.setEnabled(False)
            return

        pts = []
        if self.rectangle is not None:
            lay = canvasLayers[0][0]
            xsteps = int(self.rectangle.width() / lay.rasterUnitsPerPixelX())
            xs = [self.rectangle.xMinimum() + i * lay.rasterUnitsPerPixelX() for i in range(xsteps)]
            ysteps = int(self.rectangle.height() / lay.rasterUnitsPerPixelY())
            ys = [self.rectangle.yMinimum() + i * lay.rasterUnitsPerPixelY() for i in range(ysteps)]
            for x in xs:
                for y in ys:
                    pts.append(QgsPoint(x, y))
        elif self.pt is not None:
            pts = [self.pt]

        if not pts:
            self.buttonSave.setEnabled(False)
            return

        if len(pts) == 1:
            self.data = {}
            for layer, time in canvasLayers:
                v = self.parameter.value(layer, pts[0])
                if v is not None:
                    time = parser.parse(time)
                    self.data[time] = [(v, pts[0])]
            y = [v[0][0] for v in self.data.values()]
            ymin = min(y)
            ymax = max(y)
        else:
            self.data = {}
            for layer, time in canvasLayers:
                time = parser.parse(time)
                self.data[time] = []
                for pt in pts:
                    vx = self.parameter.value(layer, pt)
                    if vx is not None:
                        self.data[time].append((vx, pt))
            y = [[v[0] for v in lis] for lis in self.data.values()]
            ymin = min([min(v) for v in y])
            ymax = max([max(v) for v in y])

        if filter is None:
            print self.data.keys()
            xmin = min(self.data.keys())
            xmax = max(self.data.keys())
            self.plotDataChanged.emit(xmin, xmax, ymin, ymax)
        else:
            datesToRemove = []
            for d in self.data.keys():
                if d < filter[0] or d > filter[1]:
                    datesToRemove.append(d)
            for d in datesToRemove:
                del self.data[d]
            for key, values in self.data.iteritems():
                for v in values[::-1]:
                    if v[0] < filter[2] or v[0] > filter[3]:
                        try:
                            self.data[key].remove(v)
                        except:
                            pass

        datesToRemove = []
        for key, values in self.data.iteritems():
            if not values:
                datesToRemove.append(key)
        for d in datesToRemove:
            del self.data[d]

        axes = self.figure.add_subplot(1, 1, 1)
        x = matplotlib.dates.date2num(self.data.keys())
        if len(pts) == 1:
            y = [v[0][0] for v in self.data.values() if v]
            axes.plot_date(x,y)
        else:
            y = [[v[0] for v in lis] for lis in self.data.values()]
            axes.boxplot(y, positions = x)
            axes.set_xticklabels([str(d).split(" ")[0] for d in self.data.keys()], rotation=45)

        self.figure.autofmt_xdate()

        self.buttonSave.setEnabled(True)
        self.canvas.draw()

plotWidget = PlotWidget(iface.mainWindow())