ad7091rx
========

Supported Drivers
-----------------

The class **adi.ad7091rx** supports the following IIO drivers:

.. autoattribute:: adi.ad7091rx.ad7091rx.compatible_parts

Class API
---------

.. autoclass:: adi.ad7091rx.ad7091rx
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: compatible_parts

Dynamic Attributes
------------------

The ad7091rx class supports a variable number of channels depending on the hardware configuration. Therefore, the channel property interfaces are dynamically generated. They are available on an initiated object as attributes with names voltage0, voltage1, etc. They will be instances of the ad7091rx_channel class.

.. autoclass:: adi.ad7091rx.ad7091rx_channel
   :members:
   :undoc-members:
   :show-inheritance:
