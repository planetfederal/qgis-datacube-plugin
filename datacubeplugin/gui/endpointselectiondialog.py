import os
from qgis.PyQt import uic

pluginPath = os.path.dirname(os.path.dirname(__file__))
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'endpointselectiondialog.ui'))


class EndpointSelectionDialog(BASE, WIDGET):

    def __init__(self):
        self.url = None
        super(EndpointSelectionDialog, self).__init__(None)
        self.setupUi(self)

        self.buttonBox.accepted.connect(self.okPressed)
        self.buttonBox.rejected.connect(self.cancelPressed)

    def okPressed(self):
        self.url = self.comboBox.currentText()
        self.close()

    def cancelPressed(self):
        self.close()
