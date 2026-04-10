ad7124
=================

Supported Drivers
-----------------

The class **adi.ad7124** supports the following IIO drivers:

.. autoattribute:: adi.ad7124.compatible_parts


Class API
-----------------

.. autoclass:: adi.ad7124
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: compatible_parts


Dynamic Attributes
------------------

The ad7124 class supports a variable number of channels depending on the hardware configuration. Channel property interfaces are dynamically generated using their IIO channel IDs and are available in ``channel`` and as named attributes (e.g. ``temp`` or ``getattr(dev, "voltage0-voltage1")``). Voltage channels are instances of ``_ad7124_channel`` and temperature channels are instances of ``_temp_channel``.

.. autoclass:: adi.ad7124._ad7124_channel
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: adi.ad7124._temp_channel
   :members:
   :undoc-members:
   :show-inheritance:
