Beamformers & Phased Array
==========================

Beamforming front-ends and phased-array reference designs. Small
family but high-touch — these parts have richer per-channel control
than the rest of the RF front-end family because they manage phase /
attenuation per element.

Parts in this family
--------------------

.. list-table::
   :header-rows: 1
   :widths: 25 60 15

   * - Part
     - Highlights
     - Platform
   * - :doc:`ADAR1000 <../adi.adar1000>`
     - 4-channel 8 – 16 GHz beamformer; ``adar1000_array`` for stacking
     - ADAR1000 EVM
   * - :doc:`CN0566 <../adi.cn0566>`
     - Phaser: 8-element X-band phased array kit with Pluto + ADAR1000s
     - CN0566 kit

Mental model
------------

Per-element phase and gain set the beam steering / shaping. Each
ADAR1000 controls 4 channels, exposed via ``bf.channels[i]``. The
``adar1000_array`` class manages multiple ADAR1000 chips as a single
logical array and exposes array-level helpers such as ``frequency``
and ``element_spacing`` for steering math.

CN0566 is a complete kit — it integrates a Pluto SDR, two ADAR1000s,
and an 8-element antenna into one beamforming system. The pyadi-iio
class exposes both the SDR (via the Pluto subclass) and the
beamforming controls.

Minimal example
---------------

.. code-block:: python

   import adi

   # Single ADAR1000 wired as a 1x4 array. chip_id must match the
   # ADAR1000 label in the device tree; array_element_map and
   # channel_element_map are required.
   bf = adi.adar1000(
       uri="ip:analog.local",
       chip_id="csb1_chip1",
       array_element_map=[[1, 2, 3, 4]],
       channel_element_map=[1, 2, 3, 4],
   )

   bf.mode = "tx"
   for ch in bf.channels:
       ch.tx_enable = True

   # Progressive 45° phase ramp across the 4 elements
   for i, ch in enumerate(bf.channels):
       ch.tx_phase = i * 45
       ch.tx_gain = 0x67

   bf.latch_tx_settings()   # push staged phase/gain to the chip

For multi-chip arrays, use ``adi.adar1000_array(...)``; it exposes
``frequency``, ``element_spacing``, and azimuth/elevation steering
helpers in addition to per-element control.

Common properties
-----------------

* ``bf.channels[i].rx_phase`` / ``tx_phase`` — per-element phase in
  degrees.
* ``bf.channels[i].rx_gain`` / ``tx_gain`` — per-element gain code.
* ``bf.mode`` — ``"rx"`` or ``"tx"`` path select.
* ``bf.latch_rx_settings()`` / ``bf.latch_tx_settings()`` — push
  staged values to the chip.
* On ``adar1000_array``: ``frequency``, ``element_spacing``,
  ``rx_azimuth`` / ``rx_elevation`` (and ``tx_`` equivalents) for
  steering math.

Common gotchas
--------------

* Phase and gain are staged; nothing takes effect until
  ``latch_*_settings()`` is called.
* ``array_element_map`` and ``channel_element_map`` are **required**
  constructor arguments — instantiating ``adi.adar1000(...)`` without
  them raises an exception.
* ``chip_id`` must match the ADAR1000's label in the device tree
  (default ``"csb1_chip1"``); a mismatch raises *Device not found*.
* Multi-chip arrays require all chips to be configured before any
  ``latch`` is meaningful — otherwise beam shape is undefined.
* CN0566 / Phaser kit needs a specific HDL build on the Pluto to
  expose the beamformer SPI — using a stock Pluto won't work.

See also
--------

* :doc:`Concepts <../../concepts>`
* :doc:`RF Transceivers <rf_transceivers>` — the SDR side of CN0566.

Reference (per-part API)
------------------------

.. toctree::
   :maxdepth: 1

   ../adi.adar1000
   ../adi.cn0566
