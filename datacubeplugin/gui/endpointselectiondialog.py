import os
from qgis.PyQt import uic
from qgiscommons2.settings import pluginSetting, setPluginSetting

pluginPath = os.path.dirname(os.path.dirname(__file__))
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'endpointselectiondialog.ui'))


class EndpointSelectionDialog(BASE, WIDGET):

    ENDPOINTS = "Endpoints"

    def __init__(self):
        self.url = None
        super(EndpointSelectionDialog, self).__init__(None)
        self.setupUi(self)

        self.buttonBox.accepted.connect(self.okPressed)
        self.buttonBox.rejected.connect(self.cancelPressed)

        endpoints = pluginSetting(self.ENDPOINTS)
        if endpoints:
            items = endpoints.split(";")
            self.comboBox.addItems(items)

    def okPressed(self):
        self.url = self.comboBox.currentText()
        endpoints = pluginSetting(self.ENDPOINTS)
        if endpoints:
            endpoints = set(endpoints.split(";"))
            endpoints.add(self.url)
            setPluginSetting(self.ENDPOINTS, ";".join(endpoints))
        else:
            setPluginSetting(self.ENDPOINTS, self.url)
        self.close()

    def cancelPressed(self):
        self.close()
