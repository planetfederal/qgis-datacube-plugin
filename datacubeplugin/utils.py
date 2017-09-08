from qgis.core import QgsProject, QgsMapLayerRegistry, QgsLayerTreeGroup

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