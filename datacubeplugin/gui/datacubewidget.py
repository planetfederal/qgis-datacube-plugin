import os

from qgis.core import *

from qgis.utils import iface
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QTreeWidgetItem, QLabel, QHBoxLayout, QWidget
from qgis.PyQt.QtGui import QSizePolicy
from qgis.PyQt.QtCore import Qt
from qgiscommons2.layers import layerFromSource, WrongLayerSourceException
from qgiscommons2.gui import execute

from endpointselectiondialog import EndpointSelectionDialog

from datacubeplugin.selectionmaptools import PointSelectionMapTool, RegionSelectionMapTool
from datacubeplugin import layers
from datacubeplugin.connectors import connectors
from datacubeplugin.gui.plotwidget import plotWidget
from datacubeplugin.gui.mosaicwidget import mosaicWidget
from datacubeplugin import plotparams
from datacubeplugin.utils import addLayerIntoGroup, dateFromDays, daysFromDate

pluginPath = os.path.dirname(os.path.dirname(__file__))
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'datacubewidget.ui'))


class DataCubeWidget(BASE, WIDGET):

    def __init__(self, parent=None):
        super(DataCubeWidget, self).__init__(parent)
        self.setupUi(self)

        self.plotParameters = []

        AddEndpointTreeItem(self.treeWidget.invisibleRootItem(),
                                self.treeWidget, self)

        self.treeWidget.itemClicked.connect(self.treeItemClicked)

        self.comboCoverageForRGB.currentIndexChanged.connect(self.coverageForRGBHasChanged)

        self.applyButton.clicked.connect(self.updateRGB)
        self.selectPointButton.clicked.connect(self.togglePointMapTool)
        self.selectRegionButton.clicked.connect(self.toggleRegionMapTool)

        self.comboCoverageToPlot.currentIndexChanged.connect(self.coverageToPlotHasChanged)
        self.comboParameterToPlot.currentIndexChanged.connect(self.parameterToPlotHasChanged)

        iface.mapCanvas().mapToolSet.connect(self.unsetTool)

        self.pointSelectionTool = PointSelectionMapTool(iface.mapCanvas())
        self.regionSelectionTool = RegionSelectionMapTool(iface.mapCanvas())
        self.sliderStartDate.valueChanged.connect(self.plotDataFilterChanged)
        self.sliderEndDate.valueChanged.connect(self.plotDataFilterChanged)
        self.sliderMinY.valueChanged.connect(self.plotDataFilterChanged)
        self.sliderMaxY.valueChanged.connect(self.plotDataFilterChanged)

        plotWidget.plotDataChanged.connect(self.plotDataChanged)

    def plotDataFilterChanged(self):
        xmin = dateFromDays(self.sliderStartDate.value())
        xmax = dateFromDays(self.sliderEndDate.value())
        ymin = self.sliderMinY.value()
        ymax = self.sliderMaxY.value()
        self.txtStartDate.setText(str(xmin).split(" ")[0])
        self.txtEndDate.setText(str(xmax).split(" ")[0])
        self.txtMinY.setText(str(ymin))
        self.txtMaxY.setText(str(ymax))
        _filter = [xmin, xmax, ymin, ymax]
        plotWidget.plot(_filter)

    def plotDataChanged(self, xmin, xmax, ymin, ymax):
        widgets = [self.sliderMinY, self.sliderMaxY, self.sliderStartDate, self.sliderEndDate]

        for w in widgets:
            w.blockSignals(True)

        self.sliderMinY.setMinimum(ymin)
        self.sliderMaxY.setMinimum(ymin)
        self.sliderMinY.setMaximum(ymax)
        self.sliderMaxY.setMaximum(ymax)
        self.sliderMaxY.setValue(ymax)
        self.sliderMinY.setValue(ymin)

        self.sliderStartDate.setMinimum(daysFromDate(xmin) - 1)
        self.sliderEndDate.setMinimum(daysFromDate(xmin) - 1)
        self.sliderStartDate.setMaximum(daysFromDate(xmax) + 1)
        self.sliderEndDate.setMaximum(daysFromDate(xmax) + 1)
        self.sliderStartDate.setValue(daysFromDate(xmin) - 1)
        self.sliderEndDate.setValue(daysFromDate(xmax) + 1)

        self.txtStartDate.setText(str(xmin).split(" ")[0])
        self.txtEndDate.setText(str(xmax).split(" ")[0])
        self.txtMinY.setText(str(ymin))
        self.txtMaxY.setText(str(ymax))

        for w in widgets:
            w.blockSignals(False)

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
        for layer in layers._layers[name][coverageName]:
            source = layer.source()
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

        bands = layers._layers[name][coverageName][0].bands()
        try:
            r, g, b = layers._rendering[name][coverageName]
        except KeyError:
            r, g, b = (0, 1, 2)

        self.comboR.clear()
        self.comboR.addItems(bands)
        self.comboR.setCurrentIndex(r)
        self.comboG.clear()
        self.comboG.addItems(bands)
        self.comboG.setCurrentIndex(g)
        self.comboB.clear()
        self.comboB.addItems(bands)
        self.comboB.setCurrentIndex(b)

    def parameterToPlotHasChanged(self):
        param = self.plotParameters[self.comboParameterToPlot.currentIndex()]
        plotWidget.plot(parameter=param)

    def coverageToPlotHasChanged(self):
        txt = self.comboCoverageToPlot.currentText()
        name, coverageName = txt.split(" : ")
        bands = layers._coverages[name][coverageName].bands
        self.plotParameters = plotparams.getParameters(bands)
        self.comboParameterToPlot.blockSignals(True)
        self.comboParameterToPlot.clear()
        self.comboParameterToPlot.addItems([str(p) for p in self.plotParameters])
        self.comboParameterToPlot.blockSignals(False)
        plotWidget.plot(dataset=name, coverage=coverageName, parameter=self.plotParameters[0])


def setLayerRGB(layer, r, g, b):
    return
    renderer = QgsMultiBandColorRenderer(layer.dataProvider, r, g, b)
    layer.setRenderer(renderer)
    layer.triggerRepaint()
    iface.legendInterface().refreshLayerSymbology(layer)

class TreeItemWithLink(QTreeWidgetItem):

    def __init__(self, parent, tree, text, linkText):
        QTreeWidgetItem.__init__(self, parent)
        self.parent = parent
        self.tree = tree
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel()
        self.label.setText(text)
        layout.addWidget(self.label)
        if linkText:
            self.linkLabel = QLabel()
            self.linkLabel.setText("<a href='#'> %s</a>" % linkText)
            self.linkLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            layout.addWidget(self.linkLabel)
            self.linkLabel.linkActivated.connect(self.linkClicked)
        w = QWidget()
        w.setLayout(layout)
        self.tree.setItemWidget(self, 0, w)

class AddEndpointTreeItem(TreeItemWithLink):

    def __init__(self, parent, tree, widget):
        TreeItemWithLink.__init__(self, parent, tree, "", "Add new data source")
        self.widget = widget

    def linkClicked(self):
        dialog = EndpointSelectionDialog()
        dialog.exec_()
        if dialog.url is not None:
            self.addEndpoint(dialog.url)

    def addEndpoint(self, endpoint):
        execute(lambda: self._addEndpoint(endpoint))

    def _addEndpoint(self, endpoint):
        iface.mainWindow().statusBar().showMessage("Retrieving coverages info from endpoint...")
        connector = None
        for c in connectors:
            if c.isCompatible(endpoint):
                connector = c(endpoint)
                break
        if connector is None:
            return
        layers._layers[connector.name()] = {}
        layers._coverages[connector.name()] = {}
        coverages = connector.coverages()
        if coverages:
            endpointItem = QTreeWidgetItem()
            endpointItem.setText(0, connector.name())
            self.tree.addTopLevelItem(endpointItem)
        for coverageName in coverages:
            item = QTreeWidgetItem()
            item.setText(0, coverageName)
            endpointItem.addChild(item)
            coverage = connector.coverage(coverageName)
            timepositions = coverage.timePositions()
            timeLayers = []
            for time in timepositions:
                layer = coverage.layerForTimePosition(time)
                timeLayers.append(layer)
                subitem = LayerTreeItem(layer, self.widget)
                item.addChild(subitem)
            layers._layers[connector.name()][coverageName] = timeLayers
            layers._coverages[connector.name()][coverageName] = coverage
            self.widget.comboCoverageToPlot.addItem(connector.name() + " : " + coverageName)
            self.widget.comboCoverageForRGB.addItem(connector.name() + " : " + coverageName)
            mosaicWidget.comboCoverage.addItem(connector.name() + " : " + coverageName)
        iface.mainWindow().statusBar().showMessage("")


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
                    addLayerIntoGroup(layer, coverageName)
                    name = self.layer.datasetName()
                    try:
                        r, g, b = layers._rendering[name][coverageName]
                        setLayerRGB(layer, r, g, b)
                    except KeyError, e:
                        bands = self.layer.bands()
                        if len(bands) > 2:
                            try:
                                r = bands.index("red")
                                g = bands.index("green")
                                b = bands.index("blue")
                            except ValueError:
                                r, g, b = 0, 1, 2
                            layers._rendering[name][coverageName] = (r,g,b)
                            setLayerRGB(layer, r, g, b)
                        else:
                            layers._rendering[name][coverageName] = (0,0,0)
                    mosaicWidget.updateDates()
                else:
                    iface.mainWindow().statusBar().showMessage("Invalid layer")
        else:
            try:
                layer = layerFromSource(source)
                QgsMapLayerRegistry.instance().removeMapLayers([layer.id()])
            except WrongLayerSourceException:
                pass


