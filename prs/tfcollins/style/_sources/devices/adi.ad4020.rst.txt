ad4020
======

Supported Drivers
-----------------

The class **adi.ad4020** supports the following IIO drivers:

.. autoattribute:: adi.ad4020.ad4020.compatible_parts

The class **adi.ad4000** supports the following IIO drivers:

.. autoattribute:: adi.ad4020.ad4000.compatible_parts

The class **adi.ad4001** supports the following IIO drivers:

.. autoattribute:: adi.ad4020.ad4001.compatible_parts

The class **adi.ad4002** supports the following IIO drivers:

.. autoattribute:: adi.ad4020.ad4002.compatible_parts

The class **adi.ad4003** supports the following IIO drivers:

.. autoattribute:: adi.ad4020.ad4003.compatible_parts

Class API
---------

.. autoclass:: adi.ad4020.ad4020
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: compatible_parts

.. autoclass:: adi.ad4020.__ad40xx_sr
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: adi.ad4020.ad4000
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: compatible_parts

.. autoclass:: adi.ad4020.ad4001
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: compatible_parts

.. autoclass:: adi.ad4020.ad4002
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: compatible_parts

.. autoclass:: adi.ad4020.ad4003
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: compatible_parts

Dynamic Attributes
------------------

The ad4000 class supports a variable number of channels depending on the hardware configuration. Therefore, the channel property interfaces are dynamically generated. They are available on an initiated object as attributes with names voltage0, voltage1, etc. They will be instances of the ad4000_channel class.

.. autoclass:: adi.ad4020.ad4000_channel
   :members:
   :undoc-members:
   :show-inheritance:

The ad4020 class supports a variable number of channels depending on the hardware configuration. Therefore, the channel property interfaces are dynamically generated. They are available on an initiated object as attributes with names voltage0, voltage1, etc. They will be instances of the ad4020_channel class.

.. autoclass:: adi.ad4020.ad4020_channel
   :members:
   :undoc-members:
   :show-inheritance:
