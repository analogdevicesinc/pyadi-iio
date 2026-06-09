Precision DACs
==============

Lower-speed, high-resolution DACs. SPI/I²C parts with on-chip references
that map well to test, instrumentation, and bias/setpoint applications.
Includes multi-function parts like the AD5592R (combo DAC + ADC + GPIO).

Parts in this family
--------------------

.. list-table::
   :header-rows: 1
   :widths: 25 50 25

   * - Part
     - Highlights
     - Typical platform
   * - :doc:`AD353xR <../adi.ad353xr>`
     - 16-bit, multi-channel, internal reference
     - AD353xR EVM
   * - :doc:`AD3552R / AD3552R-HS <../adi.ad3552r>`
     - 16-bit, dual-channel, low-noise; HS variant: high-speed mode
     - AD3552R EVM
   * - :doc:`AD5592R <../adi.ad5592r>`
     - Combo: 8-channel ADC + DAC + GPIO
     - AD5592R EVM
   * - :doc:`AD5627 <../adi.ad5627>`
     - Dual 12-bit, I²C
     - AD5627 EVM
   * - :doc:`AD5686 <../adi.ad5686>`
     - Quad 16-bit, SPI
     - AD5686 EVM
   * - :doc:`AD5706R / AD5710R / AD5754R <../adi.ad5706r>`
     - Single / dual / quad 16-bit, integrated reference
     - AD57xxR EVM
   * - :doc:`AD579x <../adi.ad579x>`
     - 16-bit, high-precision
     - AD579x EVM
   * - :doc:`LTC2664 / LTC2672 / LTC2688 <../adi.ltc2664>`
     - 12 / 16-bit, multi-channel, with toggling and softspan
     - LTC EVM

Mental model
------------

Most parts in this family operate on a per-channel "set this output
voltage" pattern rather than a streaming buffer. The pyadi-iio class
exposes a ``channel`` collection; each channel has a ``raw`` setter
(integer code) and often a ``scale`` for converting to volts.

Some parts (AD3552R-HS, AD5754R) support streaming TX through a DMA;
those expose ``tx()`` like the JESD DAC family.

Minimal example
---------------

.. code-block:: python

   import adi

   dac = adi.ad5686(uri="ip:analog.local")
   # Set channel 0 to mid-scale
   dac.channel[0].raw = 32768

For streaming-capable parts:

.. code-block:: python

   dac = adi.ad3552r_hs(uri="ip:analog.local")
   dac.tx_enabled_channels = [0]
   dac.tx_cyclic_buffer = True
   dac.tx(waveform.astype("int16"))

Common properties
-----------------

* ``channel[i].raw`` — integer code for channel ``i``.
* ``channel[i].scale`` — scale factor to volts (where supported).
* ``channel[i].powerdown`` / ``powerdown_mode`` — per-channel power state.
* For streaming parts: ``tx_enabled_channels``, ``tx_cyclic_buffer``,
  ``sampling_frequency``.

Common gotchas
--------------

* Most parts in this family do **not** have a ``tx()`` buffer. They
  output a static voltage. Look for ``channel[i].raw`` instead.
* The internal reference must be enabled before the scale value is
  valid on some parts.
* Combo parts (AD5592R) require channel-direction configuration
  (input vs. output) before reads/writes make sense.
* LTC2688 and similar parts have "toggle" and "dither" modes that
  pyadi-iio exposes as separate properties; default state may differ
  from what you expect.

See also
--------

* :doc:`Concepts <../../concepts>`

Reference (per-part API)
------------------------

.. toctree::
   :maxdepth: 1

   ../adi.ad353xr
   ../adi.ad3552r
   ../adi.ad3552r_hs
   ../adi.ad5592r
   ../adi.ad5627
   ../adi.ad5686
   ../adi.ad5706r
   ../adi.ad5710r
   ../adi.ad5754r
   ../adi.ad579x
   ../adi.ltc2664
   ../adi.ltc2672
   ../adi.ltc2688
