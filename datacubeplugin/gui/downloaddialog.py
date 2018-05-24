import os
import numpy as np
from qgis.core import *
from qgis.gui import QgsMessageBar
from qgis.utils import iface
from qgis.PyQt import uic, QtCore
from qgis.PyQt.QtGui import QListWidgetItem
from datacubeplugin import layers
from qgiscommons2.layers import layerFromSource, WrongLayerSourceException
from qgiscommons2.files import tempFilename, tempFolderInTempFolder
from dateutil import parser
from osgeo import gdal
from osgeo.gdalconst import GA_ReadOnly
from datacubeplugin.gui.selectdownloadextentmaptool import SelectDownloadExtentMapTool
from datacubeplugin.mosaicfunctions import mosaicFunctions, NO_DATA
from datacubeplugin.utils import addLayerIntoGroup, dateFromDays, daysFromDate
from datacubeplugin.layers import getArray
from qgiscommons2.gui import execute, startProgressBar, closeProgressBar, setProgressValue, askForFolder
import processing

pluginPath = os.path.dirname(os.path.dirname(__file__))
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'downloaddialog.ui'))

class DownloadDialog(BASE, WIDGET):

    def __init__(self, timepositions, parent=None):
        super(DownloadDialog, self).__init__(parent)
        self.timepositions = []
        self.roi = None
        self.openInDatacubePanel = False
        self.setupUi(self)
        self.buttonSelectExtentOnCanvas.clicked.connect(self.selectExtentOnCanvas)
        self.buttonSelectFolder.clicked.connect(self.selectFolder)
        self.checkROI.stateChanged.connect(self.roiStateChanged)
        self.mapTool = SelectDownloadExtentMapTool(iface.mapCanvas(), self)
        self.checkROI.setChecked(False)
        self.enableROIWidgets(False)
        
        self.buttonBox.accepted.connect(self.okPressed)
        self.buttonBox.rejected.connect(self.cancelPressed)

        self.prevMapTool = iface.mapCanvas().mapTool()
        iface.mapCanvas().mapToolSet.connect(self.unsetTool)
        
        for time in timepositions:
            item = QListWidgetItem(time, self.listTimePositions)
            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
            item.setCheckState(QtCore.Qt.Unchecked)

    def selectFolder(self):
        folder = askForFolder(self, "Folder for local storage")
        if folder:
            self.textFolder.setText(folder)
            
    def roiStateChanged(self):
        state = self.checkROI.isChecked()
        self.enableROIWidgets(state)
        
    def enableROIWidgets(self, state):
        self.buttonSelectExtentOnCanvas.setEnabled(state)
        self.textXMin.setEnabled(state)
        self.textXMax.setEnabled(state)
        self.textYMin.setEnabled(state)
        self.textYMax.setEnabled(state)
        
    def unsetTool(self, tool):
        from datacubeplugin.gui.selectdownloadextentmaptool import SelectDownloadExtentMapTool
        if not isinstance(tool, SelectDownloadExtentMapTool):
            self.buttonSelectExtentOnCanvas.setChecked(False)
            self.showNormal()
            self.raise_()
            self.activateWindow()
            

    def selectExtentOnCanvas(self):
        self.buttonSelectExtentOnCanvas.setChecked(True)
        iface.mapCanvas().setMapTool(self.mapTool)
        self.showMinimized()

    def setExtent(self, extent):
        self.textXMin.setText(str(extent.xMinimum()))
        self.textYMin.setText(str(extent.yMinimum()))
        self.textXMax.setText(str(extent.xMaximum()))
        self.textYMax.setText(str(extent.yMaximum()))
        iface.mapCanvas().setMapTool(self.prevMapTool)

    def okPressed(self):
        self.timepositions = []
        for i in range(self.listTimePositions.count()):
            item = self.listTimePositions.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                self.timepositions.append(item.text())
        if self.checkROI.isChecked():
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
                self.timepositions = []
                return
            self.roi = QgsRectangle(QgsPoint(xmin, ymin), QgsPoint(xmax, ymax))
        else:
            self.roi = None
        self.openInDatacubePanel = self.checkOpenDownloaded.isChecked()
        self.folder = self.textFolder.text()
        iface.mapCanvas().mapToolSet.disconnect(self.unsetTool)
        self.close()
        
    def cancelPressed(self):
        self.timepositions = []
        iface.mapCanvas().mapToolSet.disconnect(self.unsetTool)
        self.close()