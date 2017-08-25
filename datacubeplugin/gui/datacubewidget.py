
import os
import owslib.wcs as wcs
from qgis.core import *

from qgis.utils import iface
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QTreeWidgetItem, QLabel, QHBoxLayout, QWidget
from qgis.PyQt.QtGui import QSizePolicy
from qgis.PyQt.QtCore import Qt
from qgiscommons2.layers import layerFromSource, WrongLayerSourceException
from qgiscommons2.gui import execute

from collections import defaultdict

from endpointselectiondialog import EndpointSelectionDialog

from datacubeplugin.pointselectionmaptool import PointSelectionMapTool

pluginPath = os.path.dirname(os.path.dirname(__file__))
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'datacubewidget.ui'))

_layers = {}
_addedLayers = defaultdict(list)


class DataCubeWidget(BASE, WIDGET):

    def __init__(self, parent=None):
        super(DataCubeWidget, self).__init__(parent)
        self.setupUi(self)

        item = AddEndpointTreeItem(self.treeWidget.invisibleRootItem(),
                                self.treeWidget)

        self.treeWidget.itemClicked.connect(self.treeItemClicked)

        self.applyButton.clicked.connect(self.updateRGB)
        self.selectOnCanvasButton.clicked.connect(self.toggleMapTool)

        iface.mapCanvas().mapToolSet.connect(self.unsetTool)

    def treeItemClicked(self, item, col):
        if isinstance(item, LayerTreeItem):
            item.addOrRemoveLayer()

    def unsetTool(self, tool):
        if not isinstance(tool, PointSelectionMapTool):
            self.selectOnCanvasButton.setChecked(False)
    
    def toggleMapTool(self):
        self.selectOnCanvasButton.setChecked(True)
        mapTool = PointSelectionMapTool(iface.mapCanvas())
        iface.mapCanvas().setMapTool(mapTool)

    def updateRGB(self):
        url = self.comboLayersSet.currentText()
        r = self.comboR.currentIndex()
        g = self.comboG.currentIndex()
        b = self.comboB.currentIndex()
        for source in _addedLayers[url]:
            try:
                layer = layerFromSource(source)
                setLayerRGB(layer, r, g, b)
            except WrongLayerSourceException:
                pass

def updateComboLayersSet(self):
    self.comboLayersSet.setItems(_addedLayers.keys())
    
def setLayerRGB(layer, r, g, b):
    renderer = QgsMultiBandColorRenderer()
    renderer.setRedBand(r)
    renderer.setGreenBand(g)
    renderer.setBlueBand(b)
    layer.setRenderer(renderer)
    layer.triggerRepaint()
    qgis.utils.iface.legendInterface().refreshLayerSymbology(rlayer)

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

    def __init__(self, parent, tree):
        TreeItemWithLink.__init__(self, parent, tree, "", "Add new data source")
   
    def linkClicked(self):
        dialog = EndpointSelectionDialog()
        dialog.exec_()
        if dialog.url is not None:
            self.addEndpoint(dialog.url)

    def addEndpoint(self, url):
        execute(self.addEndpoint(url))

    def _addEndpoint(self, url):
        endpointLayers = []
        iface.mainWindow().statusBar().showMessage("Retrieving coverages info from endpoint...")
        w = wcs.WebCoverageService(url, version='1.0.0')
        coverages = w.contents.keys()[:1]
        for i, coverageName in enumerate(coverages):
            item = QTreeWidgetItem()
            item.setText(0, coverageName)
            self.tree.addTopLevelItem(item)
            coverage = w[coverageName]
            timepositions = coverage.timepositions[:10]
            for j, time in enumerate(timepositions):                
                uri = QgsDataSourceURI()
                uri.setParam("url", url)
                uri.setParam("identifier", coverageName)
                uri.setParam("time", time)
                endpointLayers.append(uri)
                subitem = LayerTreeItem(uri)
                item.addChild(subitem)
        _layers[url] = endpointLayers


class LayerTreeItem(QTreeWidgetItem):

    def __init__(self, layer):
        QTreeWidgetItem.__init__(self)
        self.layer = layer
        self.setCheckState(0, Qt.Unchecked);
        self.setText(0, layer.param("time"))

    def addOrRemoveLayer(self):
        source = str(self.layer.encodedUri())
        if self.checkState(0) == Qt.Checked:
            try:
                layer = layerFromSource(source)
            except WrongLayerSourceException:
                layer = QgsRasterLayer(source, self.layer.param("identifier"), "wcs")
                QgsMapLayerRegistry.instance().addMapLayer(layer)
                _addedLayers[self.layer.param("url")].append(source)
        else:
            try:
                layer = layerFromSource(source)
                QgsMapLayerRegistry.instance().removeMapLayers([layer.id()])
            except WrongLayerSourceException:
                pass
        

