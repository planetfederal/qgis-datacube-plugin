import os
from qgis.core import *
from qgis.utils import iface
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QHBoxLayout

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
import matplotlib.pyplot as plt

pluginPath = os.path.dirname(os.path.dirname(__file__))
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'plotwidget.ui'))


class PlotWidget(BASE, WIDGET):

    def __init__(self, parent=None):
        super(PlotWidget, self).__init__(parent)
        self.setupUi(self)

        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        layout = QHBoxLayout()
        layout.addWidget(self.canvas)
        self.canvasWidget.setLayout(layout)

    def plot(self):

        self.canvas.draw()

plotWidget = PlotWidget(iface.mainWindow())