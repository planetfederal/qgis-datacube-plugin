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

        self.pt = None
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        layout = QHBoxLayout()
        layout.addWidget(self.canvas)
        self.canvasWidget.setLayout(layout)

        self.comboLayer.currentIndexChanged.connect(self.plot)

        self.comboParameter.addItems([str(p) for p in plotparams.parameters])

    def setPoint(self, pt):
        self.pt = pt
        self.plot()

    def plot(self):
        if self.pt is None:
            return
        txt = self.comboLayer.currentText()
        if txt:
            param = plotparams.parameters[self.comboParameter.currentIndex()]
            name, coverageName = txt.split(" : ")
            x = []
            y = []
            for layerdef in layers._layers[name][coverageName]:
                source = layerdef.source()
                time = layerdef.time()
                try:
                    layer = layerFromSource(source)
                    v = param.value(layer, self.pt)
                    if v is not None:
                        time = parser.parse(time)
                        x.append(time)
                        y.append(v)
                except WrongLayerSourceException:
                    pass

            x = matplotlib.dates.date2num(x)
            plt.gcf().clear()
            plt.plot_date(x,y)
            plt.gcf().autofmt_xdate()

        self.canvas.draw()

plotWidget = PlotWidget(iface.mainWindow())