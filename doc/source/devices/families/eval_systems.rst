Multi-Chip / Eval Systems
=========================

Board-level evaluation systems — FMC and DAQ daughter cards, CN0xxx
reference designs, and multi-SOM stacks. Each class in this family
binds to a *board*, not a *chip* — the class wires up the multiple
underlying drivers (ADC + DAC + clock + amp) into a single Python
object so a user doesn't have to configure them individually.

Parts in this family
--------------------

.. list-table::
   :header-rows: 1
   :widths: 30 55 15

   * - Board / system
     - Highlights
     - Pairs with
   * - :doc:`DAQ2 <../adi.daq2>`
     - AD9680 + AD9144 FMC card, 1 GSPS TX/RX
     - FMC FPGA
   * - :doc:`DAQ3 <../adi.daq3>`
     - AD9680 + AD9152, 2.25 GSPS DAC
     - FMC FPGA
   * - :doc:`FMCADC3 <../adi.fmcadc3>`
     - Quad 1 GSPS ADC FMC card
     - FMC FPGA
   * - :doc:`FMCJESDADC1 <../adi.fmcjesdadc1>`
     - Dual AD9250 250 MSPS card
     - FMC FPGA
   * - :doc:`FMComms5 <../adi.fmcomms5>`
     - Dual AD9361 MIMO 4×4
     - ZC706 / ZCU102
   * - :doc:`FMComms11 <../adi.fmcomms11>`
     - AD9162 + AD9625, 12 GSPS DAC + 2.5 GSPS ADC
     - FMC FPGA
   * - :doc:`FMC VNA <../adi.fmc_vna>`
     - Vector network analyzer FMC
     - FMC FPGA
   * - :doc:`QuadMxFE_multi <../adi.QuadMxFE_multi>`
     - Quad AD9081 multi-chip stack
     - VCU118 / custom
   * - :doc:`CN0511 <../adi.cn0511>`
     - DDS reference design (Raspberry Pi)
     - RPi
   * - :doc:`CN0532 <../adi.cn0532>`
     - Multi-channel data acquisition reference
     - ZC706
   * - :doc:`CN0540 <../adi.cn0540>`
     - 24-bit DAQ reference
     - SDP-K1
   * - :doc:`CN0554 <../adi.cn0554>`
     - 12-channel ADC + 8-channel DAC RPi HAT
     - RPi
   * - :doc:`CN0556 <../adi.cn0556>`
     - Programmable power supply reference
     - SDP-K1
   * - :doc:`CN0565 <../adi.cn0565>`
     - Bioimpedance / EIT reference
     - ADuCM355
   * - :doc:`CN0575 <../adi.cn0575>`
     - RPi temperature / fan controller reference
     - RPi
   * - :doc:`CN0579 <../adi.cn0579>`
     - High-precision DAQ reference
     - SDP-K1

Mental model
------------

Each class typically wraps multiple underlying device classes. For
example, ``DAQ2`` exposes ``rx()`` (from the AD9680 ADC) and ``tx()``
(from the AD9144 DAC) on a single object, plus the FPGA-side DDS
controls. The class handles the dance of finding all the right IIO
devices in the context and connecting them.

``_mc`` (multi-chip) classes are similar but for parts that span
multiple identical chips — see ``QuadMxFE_multi`` for four
synchronized AD9081s. The chip-level multi-chip classes (``ad9081_mc``,
``ad9084_mc``) live in the JESD ADCs family; this family is for
board-level stacks.

Minimal example
---------------

.. code-block:: python

   import adi

   daq = adi.DAQ2(uri="ip:analog.local")
   daq.rx_enabled_channels = [0, 1]
   daq.rx_buffer_size = 1024
   rx_data = daq.rx()
   daq.dds_single_tone(10_000_000, 0.9)   # generate a 10 MHz tone on TX

Common properties
-----------------

* All standard ``rx()`` / ``tx()`` properties from the underlying
  ADC / DAC classes.
* DDS properties (``dds_single_tone``, ``dds_frequencies``,
  ``dds_scales``) for transmit-capable boards — see
  :doc:`../../fpga/index`.
* Multi-chip variants: per-chip indexing into the underlying device
  collections.

Common gotchas
--------------

* Eval systems pair a specific HDL design with the board. Using
  pyadi-iio against a Vivado-built design that differs from ADI's
  reference HDL will partially or fully fail, often silently.
* Multi-chip stacks need clock alignment (synchronization). Use
  ``sync_start`` (see :doc:`../../fpga/index`) for deterministic
  TX→RX capture.
* CN0xxx classes are often very narrowly tailored to their reference
  design — they aren't general-purpose wrappers around the underlying
  chips.

See also
--------

* :doc:`Concepts <../../concepts>`
* :doc:`FPGA features (DDS, DMA sync) <../../fpga/index>`
* :doc:`JESD ADCs <jesd_adcs>` / :doc:`JESD DACs <jesd_dacs>` for the
  underlying converters.

Reference (per-part API)
------------------------

.. toctree::
   :maxdepth: 1

   ../adi.QuadMxFE_multi
   ../adi.cn0511
   ../adi.cn0532
   ../adi.cn0540
   ../adi.cn0554
   ../adi.cn0556
   ../adi.cn0565
   ../adi.cn0575
   ../adi.cn0579
   ../adi.daq2
   ../adi.daq3
   ../adi.fmc_vna
   ../adi.fmcadc3
   ../adi.fmcjesdadc1
   ../adi.fmcomms5
   ../adi.fmcomms11
