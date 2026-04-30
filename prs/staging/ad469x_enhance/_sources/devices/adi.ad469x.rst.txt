ad469x
=================

Supported Drivers
-----------------

The class **adi.ad469x** supports the following IIO drivers:

.. autoattribute:: adi.ad469x.compatible_parts


Class API
-----------------

.. autoclass:: adi.ad469x
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: compatible_parts


Dynamic Attributes
------------------

The ad469x class supports a variable number of channels depending on the
hardware configuration. Channel attributes are dynamically generated and
available on an initiated object as attributes with names voltage0,
voltage1, etc. They will be instances of the ad469x_channel class.

Attributes that are not exposed by the underlying Linux driver are handled
gracefully: reads return a safe default (``'0'`` for offset, ``None`` for
oversampling_ratio, sampling_frequency, calibscale, and calibbias) and
writes are silently ignored.

.. autoclass:: adi.ad469x.ad469x_channel
   :members:
   :undoc-members:
   :show-inheritance:
