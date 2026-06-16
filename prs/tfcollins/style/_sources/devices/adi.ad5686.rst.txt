ad5686
======

Supported Drivers
-----------------

The class **adi.ad5686** supports the following IIO drivers:

.. autoattribute:: adi.ad5686.ad5686.compatible_parts

Class API
---------

.. autoclass:: adi.ad5686.ad5686
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: compatible_parts

Dynamic Attributes
------------------

The ad5686 class supports a variable number of channels depending on the hardware configuration. Therefore, the channel property interfaces are dynamically generated. They are available on an initiated object as attributes with names voltage0, voltage1, etc. They will be instances of the ad5686_channel class.

.. autoclass:: adi.ad5686.ad5686_channel
   :members:
   :undoc-members:
   :show-inheritance:
