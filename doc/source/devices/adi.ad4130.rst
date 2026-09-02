ad4130
=================

Supported Drivers
-----------------

The class **adi.ad4130** supports the following IIO drivers:

.. autoattribute:: adi.ad4130.compatible_parts


Class API
-----------------

.. autoclass:: adi.ad4130
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: compatible_parts


Dynamic Attributes
------------------

The ad4130 class supports a variable number of channels depending on the hardware configuration. Therefore, the channel property interfaces are dynamically generated. They are available on an initiated object as attributes with names voltage0, voltage1, etc. They will be instances of the ad4130_channel class.

.. autoclass:: adi.ad4130.ad4130_channel
   :members:
   :undoc-members:
   :show-inheritance:
