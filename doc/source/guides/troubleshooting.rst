Troubleshooting
===============

Symptom → cause → fix. Entries are short and pragmatic; if your problem
isn't here, see :doc:`Support <../support>` or the
`EngineerZone forum <https://ez.analog.com/sw-interface-tools/f/q-a>`_.

import iio / libiio not found
-----------------------------

**Symptom:** ``ImportError: No module named iio`` or ``cannot find -liio``.

**Cause:** The libiio Python bindings (``pylibiio``) or the C library
itself isn't on the path. Common when libiio was built from source and
installed to ``/usr/local/lib/pythonX.Y/site-packages``, which a virtualenv
won't see by default.

**Fix:** Either set ``PYTHONPATH`` to include the site-packages dir
where ``iio.py`` lives, or recreate the venv with
``--system-site-packages``, or ``pip install pylibiio`` to get the
PyPI build.

No device found on instantiation
--------------------------------

**Symptom:** ``Exception: No device found`` when calling
``adi.<part>(uri=...)``.

**Cause:** The URI doesn't reach a libiio context, or the context
doesn't contain a device the class is looking for. Common cases:
firewall blocking the Ethernet backend, USB enumeration delay,
typo in the IP/hostname, hardware not powered.

**Fix:** Verify with ``iio_info`` directly: ``iio_info -u ip:192.168.2.1``
should list devices. If that fails, the problem is below pyadi-iio.
If it succeeds but pyadi-iio still fails, the class is looking for a
device name that isn't in this context (e.g., wrong HDL profile).

rx() returns an empty array
---------------------------

**Symptom:** ``sdr.rx()`` returns an array of length 0 or a list of
empty arrays.

**Cause:** ``rx_buffer_size`` was set to 0, no channels are enabled,
or the DMA underflowed before the buffer filled.

**Fix:** Confirm ``sdr.rx_buffer_size`` is the sample count you expect.
Confirm ``sdr.rx_enabled_channels`` is non-empty. If both look right,
the DMA is underflowing — usually because the upstream HDL isn't
producing samples (LO not locked, sample rate misconfigured, no clock).

tx() raises after the first call
--------------------------------

**Symptom:** First ``tx()`` works; second ``tx()`` raises or hangs.

**Cause:** ``tx_cyclic_buffer = True`` was set, and the cyclic buffer
must be torn down before re-arming.

**Fix:** Call ``sdr.tx_destroy_buffer()`` before the second ``tx()``.

Property read returns a stale value
-----------------------------------

**Symptom:** ``sdr.foo = X`` followed by ``print(sdr.foo)`` shows the
old value or a snapped-to-grid value.

**Cause:** Some drivers clamp setpoints to a supported grid; some
expose the raw last-write rather than the active value. This is
device-specific.

**Fix:** Check the per-part datasheet for the supported grid. For
sample rates and LO frequencies, the readback usually reflects what
the hardware actually programmed, not what you tried to set.

attr not defined in <class>
---------------------------

**Symptom:** ``AttributeError: <attr> not defined in <class>``.

**Cause:** Either the wrong subclass (e.g., using ``adi.ad9361`` against
an AD9364, which doesn't have channel-1 properties), or a driver variant
mismatch (the IIO ``compatible`` string in the kernel is different from
what pyadi-iio expects).

**Fix:** Confirm the device name reported by ``iio_info -u <uri>`` matches
what the class binds to. If you're using a multi-class module (e.g.,
``adi.ad936x``), try the specific subclass (``adi.ad9364``).

Multi-chip / _mc class doesn't find all devices
-----------------------------------------------

**Symptom:** ``adi.ad9081_mc(uri=..., phy_dev_name="ad9081-phy")`` fails
to discover all the chips, or only sees a subset.

**Cause:** The context doesn't expose every expected device, usually
because the FPGA design is misconfigured or only one chip is up.

**Fix:** ``iio_info -u <uri> | head -50`` to enumerate what the context
actually contains. The ``_mc`` class names map 1:1 to IIO device names.

libiio v0 vs. v1 behavior differences
-------------------------------------

**Symptom:** Code that worked on one machine fails on another with
buffer-mask or channel-find errors.

**Cause:** pyadi-iio supports both libiio v0.x and v1.x via
``adi/compat.py``, but a few buffer-management behaviors differ —
v1 uses ``iio.Stream`` and ``iio.ChannelsMask``; v0 uses ``iio.Buffer``.

**Fix:** Check the libiio version both ends are running:
``python -c "import iio; print(iio.version)"``. For now, prefer libiio
v0.x for stable behavior; v1.x support is current but its Python
bindings are not yet on PyPI. See :doc:`../libiio`.

pyadi-iio[jesd] extras vs. base install
---------------------------------------

**Symptom:** ``ModuleNotFoundError: No module named 'paramiko'`` when
constructing the JESD debug class.

**Cause:** ``adi.jesd`` requires ``paramiko``, which is optional and
only installed with the ``[jesd]`` extra.

**Fix:** ``pip install pyadi-iio[jesd]``. The JESD debug class is
typically only needed for ADRV9009-ZU11EG multi-SOM configurations;
if you don't use those, you don't need the extra.

Reporting new issues
--------------------

If your problem isn't covered above, please open an issue at the
`pyadi-iio GitHub <https://github.com/analogdevicesinc/pyadi-iio/issues>`_
or post on the
`EngineerZone <https://ez.analog.com/sw-interface-tools/f/q-a>`_.
Include the libiio version, pyadi-iio version, OS, and the output of
``iio_info -u <your-uri>``.
