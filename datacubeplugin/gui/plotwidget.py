import os
from qgis.core import *
from qgis.utils import iface
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QHBoxLayout

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import matplotlib
from datacubeplugin import plotparams
from datacubeplugin import layers
from qgiscommons2.layers import layerFromSource, WrongLayerSourceException
from dateutil import parser

pluginPath = os.path.dirname(os.path.dirname(__file__))
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'plotwidget.ui'))


class PlotWidget(BASE, WIDGET):

    def __init__(self, parent=None):
        super(PlotWidget, self).__init__(parent)
        self.setupUi(self)
        self.rectangle = None
        self.pt = None
        self.dataset = None
        self.coverage = None
        self.parameterX = None
        self.parameterY = None
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        layout = QHBoxLayout()
        layout.addWidget(self.canvas)
        self.canvasWidget.setLayout(layout)

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

    def setParameterX(self, parameter):
        self.parameterX = parameter
        self.plot()

    def setParameterY(self, parameter):
        self.parameterY = parameter
        self.plot()

    def plot(self):
        if self.coverage is None or self.dataset is None:
            return

        plt.gcf().clear()

        canvasLayers = []
        try:
            allCoverageLayers = layers._layers[self.dataset][self.coverage]
        except KeyError:
            return
        for layerdef in allCoverageLayers:
            source = layerdef.source()
            time = layerdef.time()
            time = parser.parse(time)
            try:
                layer = layerFromSource(source)
                canvasLayers.append((layer, time))
            except WrongLayerSourceException:
                pass

        if not canvasLayers:
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
            return

        if len(pts) == 1:
            x = []
            y = []
            for layer, time in canvasLayers:
                vx = self.parameterX.value(layer, pts[0], time)
                vy = self.parameterY.value(layer, pts[0], time)
                if vx is not None and vy is not None:
                    x.append(vx)
                    y.append(vy)
            if isinstance(self.parameterX, plotparams.TimeValue):
                x = matplotlib.dates.date2num(x)
                plt.plot_date(x,y)
                plt.gcf().autofmt_xdate()
            else:
                plt.plot(x,y)
        else:
            data = {}
            for layer, time in canvasLayers:
                vy = self.parameterY.value(layer, pts[0], time)
                if vy is not None:
                    data[vy] = []
                    for pt in pts:
                        vx = self.parameter.value(layer, pt)
                        if vx is not None:
                            vx = self.parameterX.value(layer, pts[0], time)
                        data[vy].append(vx)
                y = data.values()
            if isinstance(self.parameterX, plotparams.TimeValue):
                x = matplotlib.dates.date2num(data.keys())
                plt.gca().set_xticklabels([str(d).split(" ")[0] for d in data.keys()], rotation=45)
            plt.boxplot(y, positions = x)



        self.canvas.draw()

plotWidget = PlotWidget(iface.mainWindow())