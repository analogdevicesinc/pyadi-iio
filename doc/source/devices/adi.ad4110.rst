ad4110
=================

Supported Drivers
-----------------

The class **adi.ad4110** supports the following IIO drivers:

.. autoattribute:: adi.ad4110.compatible_parts


Class API
-----------------

.. autoclass:: adi.ad4110
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: compatible_parts


Dynamic Attributes
------------------

The ad4110 class supports a variable number of channels depending on the hardware configuration. Therefore, the channel property interfaces are dynamically generated. They are available on an initiated object as attributes with names voltage0, voltage1, etc. They will be instances of the ad4110_channel class.

.. autoclass:: adi.ad4110.ad4110_channel
   :members:
   :undoc-members:
   :show-inheritance:
