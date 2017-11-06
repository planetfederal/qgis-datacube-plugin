Data Cube Plugin
==================

A plugin to access a Data Cube and handle its layers in a simple way. Allows to create plots and mosaics from Data Cube layers.

Installation
************

To install the latest version of the plugin:

- Clone this repository or download and unzip the latest code of the plugin

- If you do not have paver (https://github.com/paver/paver) installed, install it by typing the following in a console:

::

	pip install paver
	
- Open a console in the folder created in the first step, and type

::

	paver setup

This will get all the dependencies needed by the plugin.

- Install into QGIS by running

::

	paver install

That will copy the code into your QGIS user plugin folder, or create a symlink in it, depending on your OS

To package the plugin, run

::

	paver package

Documentation will be built in the `docs` folder and added to the resulting zip file. It includes dependencies as well, but it will not download them, so the `setup` task has to be run before packaging.

Usage
*****

Usage is documented `here <./docs/source/usage.rst>`_

A note on plugin dependencies
******************************

The plugin requires the hdmedians library to compute the geomedian for creating mosaics. The correspoding paver task will download and compile it. This library contains Cython code, so the resulting binaries can only be used in the same platform as it was compiled. Running the paver package task will generate a package that can run on that platform, but not in other platforms.

To create a package than can run on any QGIS, regardless of the Operating System, binaries must be added for all OSs in the corresponding folder in the ``ext-libs`` folder where dependencies are located.

