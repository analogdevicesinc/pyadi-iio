ad7799
======

Supported Drivers
-----------------

The class **adi.ad7799** supports the following IIO drivers:

.. autoattribute:: adi.ad7799.ad7799.compatible_parts

Class API
---------

.. autoclass:: adi.ad7799.ad7799
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: compatible_parts

Dynamic Attributes
------------------

The ad7799 class supports a variable number of channels depending on the hardware configuration. Therefore, the channel property interfaces are dynamically generated. They are available on an initiated object as attributes with names voltage0, voltage1, etc. They will be instances of the ad7799_channel class.

.. autoclass:: adi.ad7799.ad7799_channel
   :members:
   :undoc-members:
   :show-inheritance:
