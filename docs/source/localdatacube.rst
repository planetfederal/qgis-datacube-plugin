Datacubes can be created from local files, as long are they are stored with a particular structure.

To create a datacube, create a folder with its name in your filesystem. Under it, create as many subfolders as coverages you have in your datacube.

Each subfolder should contain all the available timepositions for that coverage. Each timeposition is stored as a geotiff file. The name of the file must be a valid data in ISO 8601 format. Since dates in that format contain colons (which are not allowed as part of a filename in certain operating systems), all colons should be replaced with underscores.

An example of a valid filename for a layer file representing a timeposition is ``2001-09-04T14_48_59``

All timeposition files are supposed to have the same extent and pixel size.

Along with the files containing the timepositions, and additional file names ``bands.json`` is needed. It contains a an array in JSON format, with the names of the bands that layers in that coverage contain. Here is an example of the content of this file.

``["blue", "green", "red", "nir", "swir1", "swir2", "atmos_opacity", "pixel_qa", "radsat_qa", "cloud_qa", "solar_azimuth", "solar_zenith", "sensor_azimuth", "sensor_zenith"]``

Here is an example of a full structure of a local datacube, according to the ideas described above

/My_datacube
    /Landsat7
        - 2001-09-04T14_00_00
        - 2002-09-04T14_00_00
        - 2003-09-04T14_00_00
        - .
        - .
        - .
        - bands.json
    /Landsat8
        - 2017-01-01T00_00_00
        - 2017-02-01T00_00_00
        - 2017-03-01T00_00_00
        - .
        - .
        - .
        - bands.json
