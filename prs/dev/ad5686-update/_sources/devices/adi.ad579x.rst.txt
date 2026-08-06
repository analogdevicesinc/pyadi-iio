ad579x
=================

Supported Drivers
-----------------

The class **adi.ad579x** supports the following IIO drivers:

.. autoattribute:: adi.ad579x.compatible_parts


Class API
-----------------

.. autoclass:: adi.ad579x
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: compatible_parts


Dynamic Attributes
------------------

The ad579x class supports a variable number of channels depending on the hardware configuration. Therefore, the channel property interfaces are dynamically generated. They are available on an initiated object as attributes with names voltage0, voltage1, etc. They will be instances of the ad579x_channel class.

.. autoclass:: adi.ad579x.ad579x_channel
   :members:
   :undoc-members:
   :show-inheritance:
