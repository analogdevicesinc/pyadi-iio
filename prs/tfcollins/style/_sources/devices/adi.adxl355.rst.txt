adxl355
=======

Supported Drivers
-----------------

The class **adi.adxl355** supports the following IIO drivers:

.. autoattribute:: adi.adxl355.adxl355.compatible_parts

Class API
---------

.. autoclass:: adi.adxl355.adxl355
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: compatible_parts

.. autoclass:: adi.adxl355.adxl355_tempchannel
   :members:
   :undoc-members:
   :show-inheritance:

Dynamic Attributes
------------------

The adxl355 class supports a variable number of channels depending on the hardware configuration. Therefore, the channel property interfaces are dynamically generated. They are available on an initiated object as attributes with names voltage0, voltage1, etc. They will be instances of the adxl355_channel class.

.. autoclass:: adi.adxl355.adxl355_channel
   :members:
   :undoc-members:
   :show-inheritance:
