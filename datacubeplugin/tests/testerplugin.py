# Tests for the QGIS Tester plugin. To know more see
# https://github.com/boundlessgeo/qgis-tester-plugin

import os
import unittest
from qgis.PyQt.QtGui import QApplication
try:
    from qgistester.test import Test
    from qgistester.utils import layerFromName
except:
    pass

def copyDatacubeFolder():
    path = os.path.join(os.path.dirname(__file__), "data", "datacube")
    cb = QApplication.clipboard()
    cb.clear(mode=cb.Clipboard )
    cb.setText(path, mode=cb.Clipboard)
    
def functionalTests():
    try:
        from qgistester.test import Test
        from qgistester.utils import layerFromName
    except:
        return []

    def sampleMethod(self):
        pass

    plotTest = Test("Plot workflow")
    plotTest.addStep("Copy folder path", copyDatacubeFolder)
    plotTest.addStep("Add data source to plugin main panel. Datacube URL has been copied to the clipboard")
    plotTest.addStep("Add all layers from the ls7 coverage")
    plotTest.addStep("Move to the 'Plot' tab and click the 'Select point tool' button." 
                     "Click on a point in the canvas. You should see a plot in the plot panel.", isVerifyStep=True)
    plotTest.addStep("Click on the 'Select region tool'. Click and drag a small rectangle in the canvas."
                     " You should see a box and whiskers plot in the plot panel", isVerifyStep=True)
    plotTest.addStep("Move the sliders in the 'Plot' tab and verify that the plot panel reacts correctly", isVerifyStep=True)
    plotTest.addStep("Change the parameter to plot and verify that the plot panel reacts correctly", isVerifyStep=True)
    plotTest.addStep("Change the coverage to plot and verify that the plot panel is cleared", isVerifyStep=True)
    plotTest.addStep("Change back the coverage to plot and verify that the plot panel shows a plot again", isVerifyStep=True)

    renderingTest = Test("Rendering test")
    renderingTest.addStep("Copy folder path", copyDatacubeFolder)
    renderingTest.addStep("Add data source to plugin main panel. Datacube URL has been copied to the clipboard")
    renderingTest.addStep("Add one layers from the ls7 coverage")
    renderingTest.addStep("Modify the rendering of the ls7 coverage so r=green, g=blue, b=nir. Click on apply and verify the rendering changes",
                     isVerifyStep = True) 
    renderingTest.addStep("Add the remaining layer from the ls7 coverage and verify in its properties that it uses bands 2, 3 and 4 for the rendering",
                     isVerifyStep = True) 

    wrongEndpointTest = Test("Rendering test")
    wrongEndpointTest.addStep("Add wrong source to plugin main panel, entering 'wrong' in the endpoint dialog. Verify that a warning message is shown")


    return [plotTest, renderingTest, wrongEndpointTest]


class DataCubePluginTest(unittest.TestCase):

    def testSampleTest(self):
        pass


def pluginSuite():
    suite = unittest.TestSuite()
    suite.addTests(unittest.makeSuite(DataCubePluginTest, 'test'))
    return suite

def unitTests():
    _tests = []
    _tests.extend(pluginSuite())
    return _tests

# run all tests, this function is automatically called by the travis CI
# from the qgis-testing-environment-docker system
def run_all():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(pluginSuite())
