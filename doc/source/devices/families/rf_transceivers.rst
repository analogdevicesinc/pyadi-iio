RF Transceivers
===============

Integrated RF transceivers combine the entire signal chain — ADC, DAC,
mixer, LO, and digital filtering — into one device. You give them an LO
frequency, a sample rate, and a buffer size; you get complex baseband
samples in and out. Use a part in this family when you need a wide
tuning range (typically 70 MHz to 6 GHz) and don't want to design a
discrete RF front-end.

Parts in this family
--------------------

.. list-table::
   :header-rows: 1
   :widths: 25 50 25

   * - Part
     - Highlights
     - Typical platform
   * - :doc:`Pluto / AD9361 / AD9363 / AD9364 <../adi.ad936x>`
     - 70 MHz – 6 GHz, up to 2×2 MIMO, ~56 MHz BW
     - PlutoSDR, FMComms2/3/4
   * - :doc:`AD9371 / AD9375 <../adi.ad937x>`
     - 300 MHz – 6 GHz, 2×2, ~100 MHz BW
     - ADRV9371 SOM
   * - :doc:`ADRV9002 <../adi.adrv9002>`
     - 30 MHz – 6 GHz, 2×2, narrowband + wideband modes
     - ADRV9002 SOM
   * - :doc:`ADRV9009 (and ADRV9008-1/-2) <../adi.adrv9009>`
     - 75 MHz – 6 GHz, 2×2, ~200 MHz BW
     - ADRV9009 SOM
   * - :doc:`ADRV9009-ZU11EG (single / FMComms8 / multi) <../adi.adrv9009_zu11eg>`
     - Quad ADRV9009 on Zynq UltraScale+ MPSoC
     - ADRV9009-ZU11EG eval

Mental model
------------

Every part in this family is a complex transceiver. ``rx()`` returns a
``complex128`` ndarray (or list of them, one per enabled MIMO channel),
and ``tx()`` takes the same shape. ``rx_enabled_channels = [0]`` means
"enable channel 0," which is the full I/Q pair — never just I or just Q.

LO, gain, and sample rate are usually device-wide properties; gain mode
("slow_attack", "manual", "fast_attack") controls how the AGC behaves.
See :doc:`../../concepts` for the underlying property model.

Minimal example
---------------

.. code-block:: python

   import adi

   sdr = adi.Pluto(uri="ip:192.168.2.1")
   sdr.sample_rate = 2_000_000
   sdr.rx_lo = 2_400_000_000
   sdr.tx_lo = 2_400_000_000
   sdr.rx_rf_bandwidth = 2_000_000
   sdr.gain_control_mode_chan0 = "slow_attack"
   sdr.rx_buffer_size = 4096

   data = sdr.rx()      # complex128, length 4096

Common properties
-----------------

These appear on most parts in the family (exact names may vary
between AD9361 and ADRV9009-class parts):

* ``sample_rate`` — device-wide sample rate in Hz.
* ``rx_lo`` / ``tx_lo`` — receive and transmit LO frequencies in Hz.
* ``rx_rf_bandwidth`` / ``tx_rf_bandwidth`` — analog filter bandwidths.
* ``rx_hardwaregain_chan0`` (and ``_chan1`` for MIMO) — RX gain in dB.
* ``tx_hardwaregain_chan0`` (and ``_chan1``) — TX attenuation in dB
  (negative number; closer to 0 is louder).
* ``gain_control_mode_chan0`` (and ``_chan1`` for MIMO) — AGC mode
  ("slow_attack", "fast_attack", "manual").

For the full property list see the per-part autodoc below.

Common gotchas
--------------

* ``rx_enabled_channels = [0]`` enables the full I/Q pair, not a single
  scalar channel. Indexing into the returned data with ``data[0]`` on
  a single-channel capture gives you the first complex sample, not the
  I channel.
* ``tx_cyclic_buffer = True`` plus a second ``tx()`` without
  ``tx_destroy_buffer()`` in between will fail. See
  :doc:`../../guides/troubleshooting`.
* ``sample_rate`` snaps to legal values. Read it back after setting to
  confirm what hardware actually programmed.
* On ADRV9009-class parts, the FPGA HDL profile sets fixed sample-rate
  and bandwidth options — those rates aren't fully arbitrary.
* For MIMO parts, RX and TX channels can be enabled independently
  (``rx_enabled_channels`` and ``tx_enabled_channels`` are distinct).
* ADRV9009-ZU11EG variants use the ``[jesd]`` extra
  (``pip install pyadi-iio[jesd]``) for JESD204 debug helpers.

See also
--------

* :doc:`Concepts <../../concepts>` — rx/tx data shape, properties.
* :doc:`Examples <../../guides/examples>` — capture+plot, cyclic TX.
* :doc:`Buffers <../../buffers/index>` — buffer mechanics.
* :doc:`Troubleshooting <../../guides/troubleshooting>` — common errors.

Reference (per-part API)
------------------------

.. toctree::
   :maxdepth: 1

   ../adi.ad936x
   ../adi.ad937x
   ../adi.adrv9002
   ../adi.adrv9009
   ../adi.adrv9009_zu11eg
   ../adi.adrv9009_zu11eg_fmcomms8
   ../adi.adrv9009_zu11eg_multi
