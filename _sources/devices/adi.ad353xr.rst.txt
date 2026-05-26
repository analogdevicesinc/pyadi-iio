ad353xr
=================

Supported Drivers
-----------------

The class **adi.ad353xr** supports the following IIO drivers:

.. autoattribute:: adi.ad353xr.compatible_parts


Class API
-----------------

.. autoclass:: adi.ad353xr
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: compatible_parts


Dynamic Attributes
------------------

The ad353xr class supports a variable number of channels depending on the hardware configuration. Therefore, the channel property interfaces are dynamically generated. They are available on an initiated object as attributes with names voltage0, voltage1, etc. They will be instances of the ad353xr_channel class.

.. autoclass:: adi.ad353xr.ad353xr_channel
   :members:
   :undoc-members:
   :show-inheritance:
