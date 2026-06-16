ad7291
======

Supported Drivers
-----------------

The class **adi.ad7291** supports the following IIO drivers:

.. autoattribute:: adi.ad7291.ad7291.compatible_parts

Class API
---------

.. autoclass:: adi.ad7291.ad7291
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: compatible_parts

Dynamic Attributes
------------------

The ad7291 class supports a variable number of channels depending on the hardware configuration. Therefore, the channel property interfaces are dynamically generated. They are available on an initiated object as attributes with names voltage0, voltage1, etc. They will be instances of the ad7291_channel class.

.. autoclass:: adi.ad7291.ad7291_channel
   :members:
   :undoc-members:
   :show-inheritance:

The ad7291_temp class supports a variable number of channels depending on the hardware configuration. Therefore, the channel property interfaces are dynamically generated. They are available on an initiated object as attributes with names voltage0, voltage1, etc. They will be instances of the ad7291_temp_channel class.

.. autoclass:: adi.ad7291.ad7291_temp_channel
   :members:
   :undoc-members:
   :show-inheritance:
