ad2s1210
========

Supported Drivers
-----------------

The class **adi.ad2s1210** supports the following IIO drivers:

.. autoattribute:: adi.ad2s1210.ad2s1210.compatible_parts

Class API
---------

.. autoclass:: adi.ad2s1210.ad2s1210
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: compatible_parts

Dynamic Attributes
------------------

The ad2s1210_position class supports a variable number of channels depending on the hardware configuration. Therefore, the channel property interfaces are dynamically generated. They are available on an initiated object as attributes with names voltage0, voltage1, etc. They will be instances of the ad2s1210_position_channel class.

.. autoclass:: adi.ad2s1210.ad2s1210_position_channel
   :members:
   :undoc-members:
   :show-inheritance:

The ad2s1210_velocity class supports a variable number of channels depending on the hardware configuration. Therefore, the channel property interfaces are dynamically generated. They are available on an initiated object as attributes with names voltage0, voltage1, etc. They will be instances of the ad2s1210_velocity_channel class.

.. autoclass:: adi.ad2s1210.ad2s1210_velocity_channel
   :members:
   :undoc-members:
   :show-inheritance:
