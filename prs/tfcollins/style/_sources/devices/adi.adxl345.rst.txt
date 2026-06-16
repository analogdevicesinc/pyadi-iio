adxl345
=======

Supported Drivers
-----------------

The class **adi.adxl345** supports the following IIO drivers:

.. autoattribute:: adi.adxl345.adxl345.compatible_parts

Class API
---------

.. autoclass:: adi.adxl345.adxl345
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: compatible_parts

Dynamic Attributes
------------------

The adxl345 class supports a variable number of channels depending on the hardware configuration. Therefore, the channel property interfaces are dynamically generated. They are available on an initiated object as attributes with names voltage0, voltage1, etc. They will be instances of the adxl345_channel class.

.. autoclass:: adi.adxl345.adxl345_channel
   :members:
   :undoc-members:
   :show-inheritance:
