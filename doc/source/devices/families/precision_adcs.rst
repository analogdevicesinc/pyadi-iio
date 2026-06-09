Precision ADCs
==============

Lower-speed, high-resolution ADCs. Covers SAR (e.g., AD7689, AD4020),
sigma-delta (e.g., AD7124, AD4130), and integrated signal-chain parts
(e.g., AD4630, AD4858, ADAQ8092). Most parts connect over SPI or I²C
through an IIO driver in the kernel and don't require FPGA-side HDL,
though the higher-throughput parts can be paired with an FMC card and
FPGA DMA.

Parts in this family
--------------------

This family is large (~30 parts). High-level groups:

* **SAR ADCs (single / multi-channel):** AD4000-series (AD4020,
  AD4080), AD4858, AD7091RX, AD738x, AD7490, AD7606, AD7689, AD777x,
  LTC2378, LTC2387, LTC2314_14.
* **Sigma-delta ADCs:** AD4110, AD4130, AD4170, AD7124, AD7134,
  AD717x, AD719x, AD7768, AD7799, LTC2499.
* **Integrated signal-chain / DAQ-class:** AD4630 / ADAQ42xx,
  AD469x, AD514x, ADA4355, ADAQ8092, AD405x.
* **High-resolution measurement-class:** AD7799, MAX11205.

Mental model
------------

Most parts in this family expose one or more channels, each with a
``raw`` and ``scale`` attribute. Calling ``rx()`` returns the raw
integer codes; setting ``rx_output_type = "SI"`` returns floats in the
appropriate engineering unit (volts, ohms, °C — depends on the driver).

Sample rate is configurable on most parts (``sampling_frequency`` or
``sample_rate``, depending on the driver). For SPI-attached parts, the
practical limit is the kernel SPI clock, not the part itself. For
FPGA-DMA-attached parts (AD4858, AD4630), the rate is HDL-driven like
the JESD family.

Multi-channel parts return a list of ndarrays from ``rx()`` when
multiple channels are enabled. Some parts also expose per-channel
sub-objects (``adc.channel["voltage0"].scale``).

Minimal example
---------------

.. code-block:: python

   import adi

   adc = adi.ad7124(uri="ip:analog.local")
   adc.sample_rate = 100
   adc.rx_enabled_channels = [0]
   adc.rx_buffer_size = 16
   adc.rx_output_type = "SI"

   data = adc.rx()      # float array in volts (after scaling)

Common properties
-----------------

* ``rx_enabled_channels`` — channel indices to capture.
* ``rx_buffer_size`` — samples per channel.
* ``sampling_frequency`` / ``sample_rate`` — device- or per-channel
  attribute, depending on the part.
* ``rx_output_type`` — "raw" or "SI".
* Per-channel sub-objects (``adc.channel["voltageN"].scale``, etc.)
  for parts that expose channel-level control.

Common gotchas
--------------

* Not every part supports ``rx_output_type = "SI"``. Check the per-part
  autodoc; for parts that don't, multiply ``raw * scale`` yourself.
* Sigma-delta ADCs have ODR / settling-time interactions. Changing the
  sample rate and immediately calling ``rx()`` may return values from
  before the rate took effect.
* Some integrated signal-chain parts (AD4630, ADAQ8092) need an FPGA
  with a matching HDL profile — they behave more like JESD parts than
  like SPI parts despite the lower converter rate.
* Multi-channel parts that share a single converter (e.g., AD7689 with
  a mux) cannot truly sample channels simultaneously; the data is a
  time-sliced interleave.
* The LTC2499 and similar sigma-delta parts default to slow conversion
  rates — calling ``rx()`` blocks until the conversion completes.

See also
--------

* :doc:`Concepts <../../concepts>` — raw vs. SI units, annotated output.
* :doc:`Examples: multi-channel capture <../../guides/examples>`

Reference (per-part API)
------------------------

.. toctree::
   :maxdepth: 1

   ../adi.ad4020
   ../adi.ad405x
   ../adi.ad4080
   ../adi.ad4110
   ../adi.ad4130
   ../adi.ad4170
   ../adi.ad4630
   ../adi.ad469x
   ../adi.ad4858
   ../adi.ad514x
   ../adi.ad7091rx
   ../adi.ad7124
   ../adi.ad7134
   ../adi.ad717x
   ../adi.ad719x
   ../adi.ad738x
   ../adi.ad7490
   ../adi.ad7606
   ../adi.ad7689
   ../adi.ad7768
   ../adi.ad777x
   ../adi.ad7799
   ../adi.ada4355
   ../adi.adaq8092
   ../adi.ltc2314_14
   ../adi.ltc2378
   ../adi.ltc2387
   ../adi.ltc2499
   ../adi.max11205
