Concepts
========

This page is the bridge between the quick start and the per-device API
reference. After reading it, the rest of the documentation should stop
feeling magical.

How a pyadi-iio device class is built
-------------------------------------

Every device class is a composition of small mixins:

* ``context_manager`` — owns the libiio context (``iio.Context``). This is
  what the ``uri=`` argument feeds into.
* ``attribute`` — reads and writes IIO channel-attributes and device-attributes.
  Every Python property on a device class goes through this layer.
* ``rx`` and/or ``tx`` — for parts that have a sample-capture or
  sample-output buffer. These mixins provide the ``rx()`` and ``tx()``
  methods.

A class like ``adi.ad9361`` looks like ``class ad9361(rx_tx, ...)`` and
inherits properties from each mixin. When you do ``sdr.rx_lo = 2_400_000_000``,
the ``rx_lo`` setter is defined on the AD9361 class and uses the ``attribute``
layer to write the corresponding IIO attribute through ``context_manager``'s
context.

This is why ``dir(sdr)`` shows a large attribute list: every mixin contributes,
plus the part-specific properties on top.

URIs and connecting to a device
-------------------------------

A URI tells libiio which backend to use to reach the device:

* ``ip:192.168.2.1`` — network backend over TCP.
* ``ip:pluto.local`` — same, resolved via mDNS.
* ``usb:1.24.5`` — USB backend at bus 1, device 24, interface 5.
* ``serial:/dev/ttyUSB0,115200`` — serial backend.
* ``local:`` — local backend (process running on the target board itself).

When you construct a device class without ``uri=``, pyadi-iio falls through
to auto-discovery: it scans available contexts and picks the first one that
exposes a matching device name. This works well for a single USB device on
a developer machine; it's ambiguous if you have two Plutos plugged in.

Device classes are context managers. Either pattern works:

.. code-block:: python

   sdr = adi.ad9361(uri="ip:192.168.2.1")
   try:
       data = sdr.rx()
   finally:
       sdr.close()

.. code-block:: python

   with adi.ad9361(uri="ip:192.168.2.1") as sdr:
       data = sdr.rx()

The ``rx()`` and ``tx()`` methods
---------------------------------

For parts with a capture buffer, ``rx()`` returns a NumPy array:

* **Single enabled channel:** a single ndarray.
* **Multiple enabled channels:** a list of ndarrays, one per channel.
* **Complex parts** (transceivers, AD9081, etc.): the dtype is
  ``complex64``; I and Q are already combined.
* **Real parts** (precision ADCs, IMUs): the native dtype — typically
  ``int16`` or ``int32``.

``rx_buffer_size`` is the number of **samples per channel**, not the total
sample count across all enabled channels. With two channels enabled and
``rx_buffer_size = 1024``, you get two arrays of 1024 samples each.

``tx()`` accepts the same shape it would return: an ndarray for one
channel, a list of ndarrays for many. For complex TX devices, pass a
complex-dtype array; pyadi-iio splits it into the I and Q DMA streams.

Indexing into channels:

* For real parts, channel indices map directly to IIO channel order
  (channel 0 is the first channel).
* For complex parts, channel indices count complex pairs. ``rx_enabled_channels = [0]``
  on a transceiver means "enable I/Q pair 0," which is two underlying IIO channels.

See :doc:`buffers/index` for buffer mechanics in depth.

Properties and attributes
-------------------------

Properties on device classes map to libiio attributes:

* **Device attributes** — apply to the whole device (e.g., sample rate).
* **Channel attributes** — apply to a single channel (e.g., per-channel gain).

Reads and writes hit libiio every time. Most properties don't cache, so
setting one and reading it back is a real round-trip. Some drivers clamp
or snap the value to a supported grid — if ``sdr.rx_lo = 2_400_000_001``
reads back as ``2_399_999_968``, the driver picked the closest legal
value.

Writes can raise on:

* out-of-range values,
* read-only attributes on this driver variant,
* a channel index that isn't present on this part.

See :doc:`attr/index` for the property model in depth.

Cyclic vs. one-shot buffers
---------------------------

By default, ``tx()`` pushes a one-shot buffer: the data plays once.

With ``tx_cyclic_buffer = True`` set before the first ``tx()``, the
buffer plays in a loop until you tear it down. Cyclic mode is the only
sensible way to keep transmitting at multi-GSPS rates from a Python
process — you can't realistically refill the buffer in time otherwise.

The catch: once a cyclic buffer is loaded, you must call
``tx_destroy_buffer()`` before pushing a new one. Forgetting this is
the most common cause of "my second tx() call hangs or errors."

Raw vs. SI units
----------------

Some drivers expose data in scientific units. Setting
``rx_output_type = "SI"`` makes ``rx()`` return floats with the
appropriate scale applied (e.g., m/s² for an accelerometer, volts for
a voltage ADC). The default is ``raw`` — the integer codes coming out
of the converter. Not every part supports SI; check the family page or
the per-part autodoc.

libiio underneath
-----------------

Everything ultimately goes through libiio's Python bindings (``iio``).
The ``iio.Context`` is accessible as ``sdr.ctx`` on every device, and
you can drop down to libiio directly when you need an attribute pyadi-iio
hasn't surfaced. See :doc:`libiio` for the direct-access patterns.

Where to go next
----------------

* :doc:`Quick Start <guides/quick>` — install and run your first capture.
* :doc:`Supported devices <devices/index>` — find your part by family.
* :doc:`Buffers in depth <buffers/index>` — rx/tx buffer mechanics.
* :doc:`libiio direct access <libiio>` — when to bypass pyadi-iio.
* :doc:`Troubleshooting <guides/troubleshooting>` — common errors and fixes.
