ad7490
======

Supported Drivers
-----------------

The class **adi.ad7490** supports the following IIO drivers:

.. autoattribute:: adi.ad7490.ad7490.compatible_parts

Class API
---------

.. autoclass:: adi.ad7490.ad7490
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: compatible_parts

Dynamic Attributes
------------------

The ad7490 class supports a variable number of channels depending on the hardware configuration. Therefore, the channel property interfaces are dynamically generated. They are available on an initiated object as attributes with names voltage0, voltage1, etc. They will be instances of the ad7490_channel class.

.. autoclass:: adi.ad7490.ad7490_channel
   :members:
   :undoc-members:
   :show-inheritance:
