ad469x
======

Supported Drivers
-----------------

The class **adi.ad469x** supports the following IIO drivers:

.. autoattribute:: adi.ad469x.ad469x.compatible_parts

Class API
---------

.. autoclass:: adi.ad469x.ad469x
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: compatible_parts

Dynamic Attributes
------------------

The ad4691 class supports a variable number of channels depending on the hardware configuration. Therefore, the channel property interfaces are dynamically generated. They are available on an initiated object as attributes with names voltage0, voltage1, etc. They will be instances of the ad4691_channel class.

.. autoclass:: adi.ad469x.ad4691_channel
   :members:
   :undoc-members:
   :show-inheritance:

The ad4695 class supports a variable number of channels depending on the hardware configuration. Therefore, the channel property interfaces are dynamically generated. They are available on an initiated object as attributes with names voltage0, voltage1, etc. They will be instances of the ad4695_channel class.

.. autoclass:: adi.ad469x.ad4695_channel
   :members:
   :undoc-members:
   :show-inheritance:

The ad469x class supports a variable number of channels depending on the hardware configuration. Therefore, the channel property interfaces are dynamically generated. They are available on an initiated object as attributes with names voltage0, voltage1, etc. They will be instances of the ad469x_channel class.

.. autoclass:: adi.ad469x.ad469x_channel
   :members:
   :undoc-members:
   :show-inheritance:
