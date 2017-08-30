from collections import defaultdict
from qgis.core import  QgsDataSourceURI
_layers = {}
_rendering = defaultdict(defaultdict)
_bandCount = defaultdict(defaultdict)

def uriFromComponents(url, coverageName, time):
    uri = QgsDataSourceURI()
    uri.setParam("url", url)
    uri.setParam("identifier", coverageName)
    uri.setParam("time", time)
    return uri