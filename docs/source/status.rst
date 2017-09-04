Current Status
**************

This page describes the current development sttus of the plugin in this repository


Data cube panel
----------------

It contains 3 tabs:

- Layers Tab: Used to add new endpoints and manage layers. 

.. image:: img/mainpanel.png

The endpoint dialog allow to enter the location of the endpoint. Remote WCS endpoints can be added, and local filesystem folders as well. Endpoints added previously are remembered between sessions and available in the dropdown list.

.. image:: img/endpoint.png

When an endpoint is added, all available layers from it are added to this tab. With the corresponding checkbox, the layer can be added or removed to the QGIS canvas

.. image:: img/layerslist.png


- RGB rendering tab: Allows to configure the R, G and B bands to use for all the layers from a given coverage, so they dont have to be changed one by one in  the QGIS layers panel.

.. image:: img/rgb.png

- Plot tab: It contains elements to create and configure plots based on layer values.

.. image:: img/plottab.png

The coverage to use and the parameter to plot must be defined in the corresponding dropdown list.

TODO: We need the mathematical definition of compound parameters

Tools for selecting pixels to plot can be activated in this tab:

The *Select Point Tool* allows the user to click in a single point. 

.. image:: img/selectpoint.png

When the user clicks, the Plot panel is opened, and it shows a scatterplot with the values of the layers that are currently in the QGIS canvas for the selected coverage.

.. image:: img/plotpoint.png

The *Select Region Tool* allows the user to draw a rectangle. 

.. image:: img/selectregion.png


When the user clicks, the Plot panel is opened, and it shows a box and whiskers plot with the values of the layers that are currently in the QGIS canvas for the selected coverage.

.. image:: img/plotregion.png

The range of values and dates used for the plot can be controled with the sliders in the plot tab.


In the plot panel, the Save button allows the user to save the plot data as a CSV file



Mosaic Tool
***********

To be developed