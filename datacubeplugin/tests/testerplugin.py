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
    renderingTest.addStep("Add one layer from the ls7 coverage")
    renderingTest.addStep("Modify the rendering of the ls7 coverage so r=green, g=blue, b=nir. Click on apply and verify the rendering changes",
                     isVerifyStep = True) 
    renderingTest.addStep("Add the remaining layer from the ls7 coverage and verify in its properties that it uses bands 2, 3 and 4 for the rendering",
                     isVerifyStep = True) 

    wrongEndpointTest = Test("Rendering test")
    wrongEndpointTest.addStep("Add wrong source to plugin main panel, entering 'wrong' in the endpoint dialog. Verify that a warning message is shown")

    mosaicParametersTest = Test("Mosaic parameters test")
    mosaicParametersTest.addStep("Copy folder path", copyDatacubeFolder)
    mosaicParametersTest.addStep("Add data source to plugin main panel. Datacube URL has been copied to the clipboard")
    mosaicParametersTest.addStep("Open the mosaic panel and try to create a mosaic. Verify it complains that extent is not configured",
                          isVerifyStep = True) 
    mosaicParametersTest.addStep("Fill the extent values clicking on 'Canvas extent'. Try to create a mosaic. Verify it complains that there are no coverages.",
                          isVerifyStep = True) 
    mosaicParametersTest.addStep("Add one layer from the ls7 coverage and then remove it from the QGIS project. Try to create the mosaic and verify a warning is shown",
                          isVerifyStep = True) 
    

    mosaicTest = Test("Mosaic parameters test")
    mosaicTest.addStep("Copy folder path", copyDatacubeFolder)
    mosaicTest.addStep("Add data source to plugin main panel. Datacube URL has been copied to the clipboard")
    mosaicTest.addStep("Add one layer from the ls7 coverage")
    mosaicTest.addStep("Open the mosaic panel. Click on 'Select on canvas'. Click and drag on the canvas to define a extent. Click on 'Create mosaic'. Verify the mosaic is created and added")

    return [plotTest, renderingTest, wrongEndpointTest, mosaicTest, mosaicParametersTest]


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
