ad4858
======

Supported Drivers
-----------------

The class **adi.ad4858** supports the following IIO drivers:

.. autoattribute:: adi.ad4858.ad4858.compatible_parts

Class API
---------

.. autoclass:: adi.ad4858.ad4858
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: compatible_parts

Dynamic Attributes
------------------

The ad4858 class supports a variable number of channels depending on the hardware configuration. Therefore, the channel property interfaces are dynamically generated. They are available on an initiated object as attributes with names voltage0, voltage1, etc. They will be instances of the ad4858_channel class.

.. autoclass:: adi.ad4858.ad4858_channel
   :members:
   :undoc-members:
   :show-inheritance:
