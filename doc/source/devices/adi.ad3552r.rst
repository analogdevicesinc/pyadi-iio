ad3552r
=======

Supported Drivers
-----------------

The class **adi.ad3552r** supports the following IIO drivers:

.. autoattribute:: adi.ad3552r.ad3552r.compatible_parts

Class API
---------

.. autoclass:: adi.ad3552r.ad3552r
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: compatible_parts

Dynamic Attributes
------------------

The ad3552r class supports a variable number of channels depending on the hardware configuration. Therefore, the channel property interfaces are dynamically generated. They are available on an initiated object as attributes with names voltage0, voltage1, etc. They will be instances of the ad3552r_channel class.

.. autoclass:: adi.ad3552r.ad3552r_channel
   :members:
   :undoc-members:
   :show-inheritance:
