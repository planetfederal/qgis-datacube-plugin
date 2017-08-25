
import os
import webbrowser

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsApplication

from qgiscommons2.settings import readSettings
from qgiscommons2.gui.settings import addSettingsMenu, removeSettingsMenu
from qgiscommons2.gui import addAboutMenu, removeAboutMenu, addHelpMenu, removeHelpMenu

from datacubeplugin.gui.datacubewidget import DataCubeWidget
from datacubeplugin.gui.plotwidget import plotWidget

class DataCubePlugin:
    def __init__(self, iface):
        self.iface = iface
        try:
            from .tests import testerplugin
            from qgistester.tests import addTestModule
            addTestModule(testerplugin, "Data Cube Plugin")
        except:
            pass

        readSettings()

    def initGui(self):
        try:
            from lessons import addLessonsFolder
            folder = os.path.join(os.path.dirname(__file__), "_lessons")
            addLessonsFolder(folder, "datacubeplugin")
        except:
            pass

        self.dataCubeWidget = DataCubeWidget(self.iface.mainWindow())
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dataCubeWidget)
        self.dataCubeWidget.hide()

        self.iface.addDockWidget(Qt.BottomDockWidgetArea, plotWidget)
        plotWidget.hide()

        self.action = self.dataCubeWidget.toggleViewAction()
        icon = QIcon(os.path.dirname(__file__) + "/icons/desktop.svg")
        self.action.setIcon(icon)
        self.action.setText("Data Cube panel")
        self.iface.addPluginToMenu("Data Cube Plugin", self.action)

        addSettingsMenu("Data Cube Plugin")
        addHelpMenu("Data Cube Plugin")
        addAboutMenu("Data Cube Plugin")
        
    def unload(self):
        try:
            from .tests import testerplugin
            from qgistester.tests import removeTestModule
            removeTestModule(testerplugin, "Data Cube Plugin")
        except:
            pass

        try:
            from lessons import removeLessonsFolder
            folder = os.path.join(os.path.dirname(__file__), "_lessons")
            removeLessonsFolder(folder)
        except:
            pass

        self.iface.removePluginWebMenu("Data Cube Plugin", self.action)
        removeSettingsMenu("Data Cube Plugin")
        removeAboutMenu("Data Cube Plugin")
        removeHelpMenu("Data Cube Plugin")
