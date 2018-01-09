import os

import itertools
import json

from qgis.core import *
from qgis.gui import QgsMessageBar

from qgis.utils import iface
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QTreeWidgetItem, QLabel, QHBoxLayout, QWidget
from qgis.PyQt.QtGui import QSizePolicy, QPixmap, QImage, QPainter, QIcon, QDoubleValidator
from qgis.PyQt.QtCore import Qt, QSize
from qgis.PyQt.QtSvg import QSvgRenderer
from qgiscommons2.layers import layerFromSource, WrongLayerSourceException
from qgiscommons2.gui import execute, askForFolder, startProgressBar, closeProgressBar, setProgressValue

from endpointselectiondialog import EndpointSelectionDialog

from datacubeplugin.selectionmaptools import PointSelectionMapTool, RegionSelectionMapTool
from datacubeplugin import layers
from datacubeplugin.connectors import connectors
from datacubeplugin.gui.plotwidget import plotWidget
from datacubeplugin.gui.mosaicwidget import mosaicWidget
from datacubeplugin.gui.downloaddialog import DownloadDialog
from datacubeplugin import plotparams
from datacubeplugin.utils import addLayerIntoGroup, dateFromDays, daysFromDate, setLayerRGB
import datetime

pluginPath = os.path.dirname(os.path.dirname(__file__))
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'datacubewidget.ui'))


class DataCubeWidget(BASE, WIDGET):

    def __init__(self, parent=None):
        super(DataCubeWidget, self).__init__(parent)
        self.setupUi(self)

        logoPath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons", "datacube.png")
        self.labelLogo.setText('<img src="%s" width="150">' % logoPath)

        self.plotParameters = []

        self.rectangle = None
        self.pt = None

        self.yAbsoluteMin = 0
        self.yAbsoluteMax = 1

        AddEndpointTreeItem(self.treeWidget.invisibleRootItem(),
                                self.treeWidget, self)

        self.treeWidget.itemClicked.connect(self.treeItemClicked)

        self.comboCoverageForRGB.currentIndexChanged.connect(self.coverageForRGBHasChanged)

        self.applyButton.clicked.connect(self.updateRGB)
        self.selectPointButton.clicked.connect(self.togglePointMapTool)
        self.selectRegionButton.clicked.connect(self.toggleRegionMapTool)

        iface.mapCanvas().mapToolSet.connect(self.unsetTool)

        self.pointSelectionTool = PointSelectionMapTool(iface.mapCanvas())
        self.regionSelectionTool = RegionSelectionMapTool(iface.mapCanvas())
        plotWidget.plotDataChanged.connect(self.plotDataChanged)
        self.pointSelectionTool.pointSelected.connect(self.setPoint)
        self.regionSelectionTool.regionSelected.connect(self.setRectangle)

        self.comboCoverageToPlot.currentIndexChanged.connect(self.coverageToPlotHasChanged)

        self.plotButton.clicked.connect(self.drawPlot)
        self.chkFilter.stateChanged.connect(self.filterCheckChanged)

        self.txtMinY.setValidator(QDoubleValidator(self))
        self.txtMaxY.setValidator(QDoubleValidator(self))


    def filterCheckChanged(self, state):
        enabled = self.chkFilter.isChecked()
        self.txtStartDate.setEnabled(enabled)
        self.txtEndDate.setEnabled(enabled)
        self.txtMinY.setEnabled(enabled)
        self.txtMaxY.setEnabled(enabled)

    def coverageToPlotHasChanged(self):
        txt = self.comboCoverageToPlot.currentText()
        name, coverageName = txt.split(" : ")
        bands = layers._coverages[name][coverageName].bands
        self.plotParameters = plotparams.getParameters(bands)
        self.comboParameterToPlot.blockSignals(True)
        self.comboParameterToPlot.clear()
        self.comboParameterToPlot.addItems([str(p) for p in self.plotParameters])
        self.comboParameterToPlot.blockSignals(False)

    def plotDataChanged(self, xmin, xmax, ymin, ymax):
        self.txtStartDate.setDate(xmin)
        self.txtEndDate.setDate(xmax)
        self.txtMinY.setText(str(ymin))
        self.txtMaxY.setText(str(ymax))

    def treeItemClicked(self, item, col):
        if isinstance(item, LayerTreeItem):
            item.addOrRemoveLayer()

    def unsetTool(self, tool):
        if not isinstance(tool, PointSelectionMapTool):
            self.selectPointButton.setChecked(False)
        if not isinstance(tool, RegionSelectionMapTool):
            self.selectRegionButton.setChecked(False)

    def togglePointMapTool(self):
        self.selectPointButton.setChecked(True)
        iface.mapCanvas().setMapTool(self.pointSelectionTool)

    def toggleRegionMapTool(self):
        self.selectRegionButton.setChecked(True)
        iface.mapCanvas().setMapTool(self.regionSelectionTool)

    def updateRGB(self):
        name, coverageName = self.comboCoverageForRGB.currentText().split(" : ")
        r = self.comboR.currentIndex()
        g = self.comboG.currentIndex()
        b = self.comboB.currentIndex()
        layers._rendering[name][coverageName] = (r, g, b)
        try:
            mosaics = layers._mosaicLayers[name][coverageName]
        except KeyError:
            mosaics = []
        for layer in itertools.chain(layers._layers[name][coverageName], mosaics):
            source = layer if isinstance(layer, basestring) else layer.source()
            try:
                layer = layerFromSource(source)
                setLayerRGB(layer, r, g, b)
            except WrongLayerSourceException:
                pass


    def coverageForRGBHasChanged(self):
        self.updateRGBFields()

    def updateRGBFields(self, nameToUpdate = None, coverageNameToUpdate = None):
        name, coverageName = self.comboCoverageForRGB.currentText().split(" : ")
        if nameToUpdate is not None and (name != nameToUpdate or coverageName != coverageNameToUpdate):
            return

        blacklisted = ["coastal_aerosol", "aerosol_qa", "radsat_qa", "solar_azimuth",
                   "solar_zenith", "sensor_azimuth", "sensor_zenith"]
        bands = layers._layers[name][coverageName][0].bands()
        bands = [b for b in bands if b not in blacklisted]
        try:
            r, g, b = layers._rendering[name][coverageName]
        except KeyError:
            if len(bands) > 2:
                try:
                    r = bands.index("red")
                    g = bands.index("green")
                    b = bands.index("blue")
                except ValueError:
                    r, g, b = 0, 1, 2
            else:
                r = g = b = 0

        self.comboR.clear()
        self.comboR.addItems(bands)
        self.comboR.setCurrentIndex(r)
        self.comboG.clear()
        self.comboG.addItems(bands)
        self.comboG.setCurrentIndex(g)
        self.comboB.clear()
        self.comboB.addItems(bands)
        self.comboB.setCurrentIndex(b)

    def setRectangle(self, rect):
        self.rectangle = rect
        self.pt = None
        self.txtSelectedArea.setText("Region selected")

    def setPoint(self, pt):
        self.pt = pt
        self.rectangle = None
        self.txtSelectedArea.setText("Point selected: %d, %d" % (pt.x(), pt.y()))

    def drawPlot(self):
        plotWidget.show()
        txt = self.comboCoverageToPlot.currentText()
        if txt:
            name, coverageName = txt.split(" : ")
            param = self.plotParameters[self.comboParameterToPlot.currentIndex()]
            _filter = None
            if self.chkFilter.isChecked():
                xmin = self.txtStartDate.date().toPyDate()
                xmax = self.txtEndDate.date().toPyDate()
                xmin = datetime.datetime(xmin.year, xmin.month, xmin.day)
                xmax = datetime.datetime(xmax.year, xmax.month, xmax.day)
                try:
                    ymin = float(self.txtMinY.text())
                except:
                    ymin = None
                try:
                    ymax = float(self.txtMaxY.text())
                except:
                    ymin = None
                _filter = [xmin, xmax, ymin, ymax]
            plotWidget.plot(dataset=name, coverage=coverageName, parameter=param,
                            _filter=_filter, pt=self.pt, rectangle=self.rectangle)
            
    def addEndpoint(self, endpoint):
        iface.mainWindow().statusBar().showMessage("Retrieving coverages info from endpoint...")
        connector = None
        for c in connectors:
            if c.isCompatible(endpoint):
                connector = c(endpoint)
                break
        if connector is None:
            iface.messageBar().pushMessage("", "Could not add coverages from the provided endpoint.",
                                               level=QgsMessageBar.WARNING)
            iface.mainWindow().statusBar().showMessage("")
            return
        layers._layers[connector.name()] = {}
        layers._coverages[connector.name()] = {}
        coverages = connector.coverages()
        if coverages:
            endpointItem = QTreeWidgetItem()
            endpointItem.setText(0, connector.name())
        emptyCoverages = 0
        for coverageName in coverages:
            coverage = connector.coverage(coverageName)
            timepositions = coverage.timePositions()
            if timepositions:
                item = CoverageItem(endpointItem, self.treeWidget, coverage, self)
                timeLayers = []
                for time in timepositions:
                    layer = coverage.layerForTimePosition(time)
                    timeLayers.append(layer)
                    subitem = LayerTreeItem(layer, self)
                    item.addChild(subitem)
                layers._layers[connector.name()][coverageName] = timeLayers
                layers._coverages[connector.name()][coverageName] = coverage
                self.comboCoverageToPlot.addItem(connector.name() + " : " + coverageName)
                self.comboCoverageForRGB.addItem(connector.name() + " : " + coverageName)
                mosaicWidget.comboCoverage.addItem(connector.name() + " : " + coverageName)
            else:
                emptyCoverages += 1
        iface.mainWindow().statusBar().showMessage("")
        if emptyCoverages == len(coverages):
            iface.messageBar().pushMessage("", "No coverages with timepositions were found in server.", level=QgsMessageBar.WARNING)
        else:
            self.treeWidget.addTopLevelItem(endpointItem)
            if emptyCoverages:
                iface.messageBar().pushMessage("",
                        "%i out of %i coverages do not declare any time position and could not be added." % (emptyCoverages, len(coverages)),
                        level=QgsMessageBar.WARNING)


class TreeItemWithLink(QTreeWidgetItem):

    def __init__(self, parent, tree, text, linkText, linkColor="blue", icon=None):
        QTreeWidgetItem.__init__(self, parent)
        self.parent = parent
        self.tree = tree
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel()
        if icon and os.path.exists(icon):
            svg_renderer = QSvgRenderer(icon)
            image = QImage(32, 32, QImage.Format_ARGB32)
            # Set the ARGB to 0 to prevent rendering artifacts
            image.fill(0x00000000)
            svg_renderer.render(QPainter(image))
            pixmap = QPixmap.fromImage(image)
            icon = QIcon(pixmap)
            self.setIcon(0, icon)
            self.setSizeHint(0, QSize(32, 32))
        self.label.setText(text)
        layout.addWidget(self.label)
        if linkText:
            self.linkLabel = QLabel()
            self.linkLabel.setText("<a href='#' style='color: %s;'> %s</a>" % (linkColor, linkText))
            self.linkLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            layout.addWidget(self.linkLabel)
            self.linkLabel.linkActivated.connect(self.linkClicked)
        w = QWidget()
        w.setLayout(layout)
        self.tree.setItemWidget(self, 0, w)

class AddEndpointTreeItem(TreeItemWithLink):

    def __init__(self, parent, tree, widget):
        iconPath = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons", "plus.svg")
        TreeItemWithLink.__init__(self, parent, tree, "", "Add new data source", "DodgerBlue", iconPath)
        self.widget = widget

    def linkClicked(self):
        from endpointselectiondialog import EndpointSelectionDialog
        dialog = EndpointSelectionDialog()
        dialog.exec_()
        if dialog.url is not None:
            self.addEndpoint(dialog.url)

    def addEndpoint(self, endpoint):
        execute(lambda: self.widget.addEndpoint(endpoint))


class CoverageItem(TreeItemWithLink):

    def __init__(self, parent, tree, coverage, widget):
        TreeItemWithLink.__init__(self, parent, tree, coverage.name(), "Download")
        self.coverage = coverage
        self.widget = widget

    def linkClicked(self):
        timepositions = self.coverage.timePositions()
        dlg = DownloadDialog(timepositions, self.tree)
        dlg.show()
        dlg.exec_()
        if dlg.timepositions:
            folder = os.path.join(dlg.folder, self.coverage.name())
            if not os.path.exists(folder):
                try:
                    os.makedirs(folder)
                except:
                    iface.messageBar().pushMessage("",
                        "Wrong output directory or error creating it",
                        level=QgsMessageBar.WARNING)
                    return
                    
            bandsFile = os.path.join(folder, "bands.json")
            with open(bandsFile, "w") as f:
                json.dump(self.coverage.bands, f) 
            startProgressBar("Downloading datacube subset", len(timepositions))
            for i, time in enumerate(timepositions):
                setProgressValue(i)
                layer = self.coverage.layerForTimePosition(time)
                execute(lambda: layer.saveTo(folder, dlg.roi))
            closeProgressBar()
            if dlg.openInDatacubePanel:
                execute(lambda: self.widget.addEndpoint(dlg.folder))
                


class LayerTreeItem(QTreeWidgetItem):

    def __init__(self, layer, widget):
        QTreeWidgetItem.__init__(self)
        self.layer = layer
        self.widget = widget
        self.setCheckState(0, Qt.Unchecked);
        self.setText(0, layer.time())

    def addOrRemoveLayer(self):
        source = self.layer.source()
        if self.checkState(0) == Qt.Checked:
            try:
                layer = layerFromSource(source)
            except WrongLayerSourceException:
                layer = execute(self.layer.layer)
                if layer.isValid():
                    coverageName = self.layer.coverageName()
                    name = self.layer.datasetName()
                    addLayerIntoGroup(layer, name, coverageName, self.layer.bands())
                    mosaicWidget.updateDates()
                else:
                    iface.messageBar().pushMessage("", "Invalid layer.",
                                               level=QgsMessageBar.WARNING)
        else:
            try:
                layer = layerFromSource(source)
                QgsMapLayerRegistry.instance().removeMapLayers([layer.id()])
            except WrongLayerSourceException:
                pass


