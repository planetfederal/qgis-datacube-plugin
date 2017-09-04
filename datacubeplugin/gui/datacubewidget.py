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
from datacubeplugin.connectors import WCSConnector, FileConnector
from datacubeplugin.gui.plotwidget import plotWidget
from datacubeplugin import plotparams

pluginPath = os.path.dirname(os.path.dirname(__file__))
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'datacubewidget.ui'))


class DataCubeWidget(BASE, WIDGET):

    def __init__(self, parent=None):
        super(DataCubeWidget, self).__init__(parent)
        self.setupUi(self)

        AddEndpointTreeItem(self.treeWidget.invisibleRootItem(),
                                self.treeWidget, self)

        self.treeWidget.itemClicked.connect(self.treeItemClicked)

        self.comboLayersSet.currentIndexChanged.connect(self.comboLayersChanged)

        self.applyButton.clicked.connect(self.updateRGB)
        self.selectPointButton.clicked.connect(self.togglePointMapTool)
        self.selectRegionButton.clicked.connect(self.toggleRegionMapTool)

        self.comboLayerToPlot.currentIndexChanged.connect(self.layerToPlotHasChanged)
        self.comboParameterToPlot.currentIndexChanged.connect(self.parameterToPlotHasChanged)

        self.comboParameterToPlot.addItems([str(p) for p in plotparams.parameters])

        iface.mapCanvas().mapToolSet.connect(self.unsetTool)

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
        mapTool = PointSelectionMapTool(iface.mapCanvas())
        iface.mapCanvas().setMapTool(mapTool)

    def toggleRegionMapTool(self):
        self.selectRegionButton.setChecked(True)
        mapTool = RegionSelectionMapTool(iface.mapCanvas())
        iface.mapCanvas().setMapTool(mapTool)

    def updateRGB(self):
        name, coverageName = self.comboLayersSet.currentText().split(" : ")
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

    def comboLayersChanged(self):
        self.updateRGBFields()

    def updateRGBFields(self, nameToUpdate = None, coverageNameToUpdate = None):
        name, coverageName = self.comboLayersSet.currentText().split(" : ")
        if nameToUpdate is not None and (name != nameToUpdate or coverageName != coverageNameToUpdate):
            return
        try:
            bandCount = layers._bandCount[name][coverageName]
            r, g, b = layers._rendering[name][coverageName]
        except KeyError:
            #TODO improve this
            bandCount = 3
            r, g, b = (0, 1, 2)

        items = [str(i + 1) for i in range(bandCount)]
        self.comboR.clear()
        self.comboR.addItems(items)
        self.comboR.setCurrentIndex(r)
        self.comboG.clear()
        self.comboG.addItems(items)
        self.comboG.setCurrentIndex(g)
        self.comboB.clear()
        self.comboB.addItems(items)
        self.comboB.setCurrentIndex(b)


    def updateComboLayersSet(self):
        allItems = []
        for name in layers._layers.keys():
            for coverageName in layers._layers[name].keys():
                allItems.append(name + " : " + coverageName)

        self.comboLayersSet.clear()
        self.comboLayersSet.addItems(allItems)

    def parameterToPlotHasChanged(self):
        param = plotparams.parameters[self.comboParameterToPlot.currentIndex()]
        plotWidget.setParameter(param)

    def layerToPlotHasChanged(self):
        txt = self.comboLayerToPlot.currentText()
        name, coverageName = txt.split(" : ")
        plotWidget.setLayer(name, coverageName)


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
        endpointLayers = {}
        iface.mainWindow().statusBar().showMessage("Retrieving coverages info from endpoint...")
        if os.path.exists(endpoint):
            connector = FileConnector(endpoint)
        else:
            connector = WCSConnector(endpoint)
        coverages = connector.coverages()
        if coverages:
            endpointItem = QTreeWidgetItem()
            endpointItem.setText(0, connector.name())
            self.tree.addTopLevelItem(endpointItem)
        for coverageName in coverages:
            item = QTreeWidgetItem()
            item.setText(0, coverageName)
            endpointItem.addChild(item)
            self.widget.comboLayerToPlot.addItem(connector.name() + " : " + coverageName)
            coverage = connector.coverage(coverageName)
            timepositions = coverage.timePositions()[:10]
            timeLayers = []
            for time in timepositions:
                layer = coverage.layerForTimePosition(time)
                timeLayers.append(layer)
                subitem = LayerTreeItem(layer, self.widget)
                item.addChild(subitem)
            endpointLayers[coverageName] = timeLayers
        layers._layers[connector.name()] = endpointLayers
        self.widget.updateComboLayersSet()
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
                layer = self.layer.layer()
                if layer.isValid():
                    coverageName = self.layer.coverageName()
                    root = QgsProject.instance().layerTreeRoot()
                    group = None
                    for child in root.children():
                        if isinstance(child, QgsLayerTreeGroup) and child.name() == coverageName:
                            group = child
                    if group is None:
                        group = root.addGroup(coverageName)
                    QgsMapLayerRegistry.instance().addMapLayer(layer, False)
                    group.addLayer(layer)
                    name = self.layer.datasetName()
                    try:
                        count = layers._bandCount[name][coverageName]
                        r, g, b = layers._rendering[name][coverageName]
                        setLayerRGB(layer, r, g, b)
                    except KeyError, e:
                        layers._bandCount[name][coverageName] = layer.bandCount()
                        if layer.bandCount() > 2:
                            layers._rendering[name][coverageName] = (0,1,2)
                        else:
                            layers._rendering[name][coverageName] = (0,0,0)
                        self.widget.updateRGBFields(name, coverageName)
                else:
                    iface.mainWindow().statusBar().showMessage("Invalid layer")
        else:
            try:
                layer = layerFromSource(source)
                QgsMapLayerRegistry.instance().removeMapLayers([layer.id()])
            except WrongLayerSourceException:
                pass


