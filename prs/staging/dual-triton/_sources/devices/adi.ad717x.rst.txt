ad717x
=================

Supported Drivers
-----------------

The class **adi.ad717x** supports the following IIO drivers:

.. autoattribute:: adi.ad717x.compatible_parts


Class API
-----------------

.. autoclass:: adi.ad717x
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: compatible_parts


Dynamic Attributes
------------------

The ad717x class supports a variable number of channels depending on the hardware configuration. Therefore, the channel property interfaces are dynamically generated. They are available on an initiated object as attributes with names voltage0, voltage1, etc. They will be instances of the ad717x_channel class.

.. autoclass:: adi.ad717x.ad717x_channel
   :members:
   :undoc-members:
   :show-inheritance:
