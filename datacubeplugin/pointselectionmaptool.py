from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QApplication
from qgis.PyQt.QtGui import QCursor

from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform
from qgis.gui import QgsMapTool, QgsMessageBar
from qgis.utils import iface

from datacubeplugin.gui.plotwidget import plotWidget

class PointSelectionMapTool(QgsMapTool):

    def __init__(self, canvas):
        QgsMapTool.__init__(self, canvas)
        self.setCursor(Qt.CrossCursor)

    def canvasReleaseEvent(self, e):

        pt = self.toMapCoordinates(e.pos())

        plotWidget.show()

