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
voltage1, etc.

The channel class is selected automatically based on the device name:

- **ad4695.c family** (ad4695/96/97/98): channels are instances of
  ``ad4695_channel``, which adds ``offset``, ``calibscale``, and
  ``calibbias`` on top of the base attributes.

- **ad4691.c family** (ad4691/92/93/94): channels are instances of
  ``ad4691_channel``, which adds ``oversampling_ratio``,
  ``oversampling_ratio_available``, and ``sampling_frequency`` on top
  of the base attributes.

.. autoclass:: adi.ad469x.ad469x_channel
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: adi.ad469x.ad4695_channel
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: adi.ad469x.ad4691_channel
   :members:
   :undoc-members:
   :show-inheritance:
