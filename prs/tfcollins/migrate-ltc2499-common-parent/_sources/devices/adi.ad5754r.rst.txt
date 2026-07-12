ad5754r
=================

Supported Drivers
-----------------

The class **adi.ad5754r** supports the following IIO drivers:

.. autoattribute:: adi.ad5754r.compatible_parts


Class API
-----------------

.. autoclass:: adi.ad5754r
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: compatible_parts


Dynamic Attributes
------------------

The ad5754r class supports a variable number of channels depending on the hardware configuration. Therefore, the channel property interfaces are dynamically generated. They are available on an initiated object as attributes with names voltage0, voltage1, voltage2, voltage3. They will be instances of the ad5754r_channel class.

.. autoclass:: adi.ad5754r.ad5754r_channel
   :members:
   :undoc-members:
   :show-inheritance:
