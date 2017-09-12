from qgis.core import QgsProject, QgsMapLayerRegistry, QgsLayerTreeGroup
from datetime import timedelta
from dateutil import parser

def addLayerIntoGroup(layer, groupName):
    root = QgsProject.instance().layerTreeRoot()
    group = None
    for child in root.children():
        if isinstance(child, QgsLayerTreeGroup) and child.name() == groupName:
            group = child
            break
    if group is None:
        group = root.addGroup(groupName)
    QgsMapLayerRegistry.instance().addMapLayer(layer, False)
    group.addLayer(layer)

MINDATE = parser.parse("1800-01-01T00:00:00Z")

def daysFromDate(d):
    delta = d - MINDATE
    return delta.days

def dateFromDays(days):
    delta = timedelta(days)
    return MINDATE + delta