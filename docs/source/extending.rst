Extending the datacube plugin
******************************

There are several ways of extending the functionality of the plugin:


Adding a new connector
-------------------------

Connectors are used to feed data coverages to the plugin. A connector provides a set of coverages, and for each of them there is a set of time positions.

To add a new Connector, you should implement the corresponding classes for the connector itself, a coverage object and a layer object. The ``connectors.py`` has two connectors already implemented (WCS and file-based), that you can use as an example. Add new connectors in that module and extend the ``connectors`` array so it becomes available.


Adding new functions to plot in the Y axis
-------------------------------------------

Available functions for use to compute Y-axis values in plots are implemented in the ``plotparams.py`` module. Extend the PlotParameter class in that module to create a new parameter, and add an object of that new class to the ``parameters`` array so it becomes available.

Adding new algorithms to compute mosaic pixel values
-----------------------------------------------------

