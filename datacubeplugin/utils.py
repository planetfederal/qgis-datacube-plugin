from qgis.core import QgsProject, QgsMapLayerRegistry, QgsLayerTreeGroup, QgsMultiBandColorRenderer
from qgis.utils import iface
from datetime import timedelta
from dateutil import parser
from datacubeplugin import layers
from qgiscommons2.gui import execute

def addLayerIntoGroup(layer, name, coverageName, bands=None):
    root = QgsProject.instance().layerTreeRoot()
    group = None
    for child in root.children():
        if isinstance(child, QgsLayerTreeGroup) and child.name() == coverageName:
            group = child
            break
    if group is None:
        group = root.addGroup(coverageName)
    QgsMapLayerRegistry.instance().addMapLayer(layer, False)
    group.addLayer(layer)

    try:
        r, g, b = layers._rendering[name][coverageName]
        setLayerRGB(layer, r, g, b)
    except KeyError, e:
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
            setLayerRGB(layer, 0, 0, 0)

MINDATE = parser.parse("1800-01-01T00:00:00")

def daysFromDate(d):
    delta = d - MINDATE
    return delta.days

def dateFromDays(days):
    delta = timedelta(days)
    return MINDATE + delta

def setLayerRGB(layer, r, g, b):
    renderer = QgsMultiBandColorRenderer(layer.dataProvider(), r + 1, g + 1, b + 1)
    layer.setRenderer(renderer)
    layer.triggerRepaint()
    iface.legendInterface().refreshLayerSymbology(layer)