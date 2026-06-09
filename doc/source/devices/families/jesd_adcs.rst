High-Speed / JESD ADCs
======================

High-speed ADCs that move samples to an FPGA — most use JESD204B/C serial
lanes; a few use parallel CMOS or LVDS. Use these for wideband radar,
instrumentation, communications test, or any application where high
sample rates are required. A part in this family is always paired with
an HDL design on an FPGA that provides the link partner (JESD or
parallel) and DMA.

Parts in this family
--------------------

.. list-table::
   :header-rows: 1
   :widths: 20 55 25

   * - Part
     - Highlights
     - Typical platform
   * - :doc:`AD6676 <../adi.ad6676>`
     - IF-sampling ADC, 200 MHz IF
     - AD6676 EVM
   * - :doc:`AD9081 <../adi.ad9081>` / :doc:`AD9081-MC <../adi.ad9081_mc>`
     - 4-channel, 4 GSPS RX (multi-chip variant for QuadMxFE)
     - QuadMxFE
   * - :doc:`AD9083 <../adi.ad9083>`
     - 16-channel, 125 MSPS, JESD204B
     - AD9083 EVM
   * - :doc:`AD9084 <../adi.ad9084>` / :doc:`AD9084-MC <../adi.ad9084_mc>`
     - 4 GSPS, JESD204C, multi-chip Triton platform
     - Triton
   * - :doc:`AD9094 <../adi.ad9094>`
     - 4-channel, 1 GSPS, JESD204B
     - AD9094 EVM
   * - :doc:`AD9213 <../adi.ad9213>`
     - 12-bit, 10 GSPS
     - AD9213 EVM
   * - :doc:`AD9250 <../adi.ad9250>`
     - Dual 14-bit, 250 MSPS
     - AD9250 / DAQ-class
   * - :doc:`AD9265 <../adi.ad9265>`
     - 16-bit, 125 MSPS (parallel CMOS, sometimes JESD-paired)
     - AD9265 EVM
   * - :doc:`AD9434 <../adi.ad9434>`
     - 12-bit, 500 MSPS
     - AD9434 EVM
   * - :doc:`AD9467 <../adi.ad9467>`
     - 16-bit, 250 MSPS
     - AD9467 EVM
   * - :doc:`AD9625 <../adi.ad9625>`
     - 12-bit, 2.5 GSPS
     - AD9625 EVM
   * - :doc:`AD9680 <../adi.ad9680>`
     - Dual 14-bit, 1.25 GSPS
     - FMCDAQ2

Mental model
------------

These parts always live behind an FPGA. The pyadi-iio class talks to the
IIO driver running on the FPGA's processor (Zynq, ZynqMP, MicroBlaze),
which talks to the part over SPI for control and over JESD204 for data.

``rx()`` returns either real ndarrays or ``complex128`` ndarrays depending
on whether the HDL profile includes a digital downconverter (DDC).
``rx_buffer_size`` is samples per channel; the DMA fills it.

Sample rate is **fixed by the HDL profile**, not settable at runtime in
most cases. Decimation and NCO frequency (when a DDC is present) are
runtime-settable. See :doc:`../../concepts` for the buffer / data-shape
contract.

Minimal example
---------------

.. code-block:: python

   import adi

   adc = adi.ad9680(uri="ip:analog.local")
   adc.rx_enabled_channels = [0, 1]
   adc.rx_buffer_size = 1024

   data = adc.rx()       # list of 2 ndarrays

Common properties
-----------------

* ``rx_enabled_channels`` — indices of enabled channels (real-valued
  for parts without a DDC, complex pairs for parts with a DDC).
* ``rx_buffer_size`` — samples per channel.
* ``sampling_frequency`` — fixed by the HDL profile; read-only on most
  parts.
* DDC properties (where present): ``rx_main_nco_frequencies``,
  ``rx_channel_nco_frequencies``, ``rx_main_nco_phases``,
  ``rx_test_mode``.
* AD9081/AD9084: per-channel and per-main NCO frequency/phase arrays;
  fine/coarse decimation.

Common gotchas
--------------

* ``sampling_frequency`` is read-only or HDL-driven on most parts. The
  way to change it is to flash an HDL design with the desired rate, not
  to set the property at runtime.
* Multi-chip variants (``_mc``) bind to multiple IIO devices in one
  context. If discovery fails, run ``iio_info -u <uri>`` to confirm all
  expected device names are present.
* AD9081 / AD9084 DDC channel indexing is non-obvious: complex pairs
  correspond to (main NCO, channel NCO) tuples. See the per-part page.
* JESD link bring-up issues surface as zero / garbage samples. Use
  ``adi.jesd`` (with the ``[jesd]`` extra) to inspect link status.
* DMA underflows (``rx()`` returns less data than ``rx_buffer_size``)
  usually mean upstream JESD isn't producing samples — check link state
  before debugging the Python side.

See also
--------

* :doc:`Concepts <../../concepts>`
* :doc:`Examples: multi-channel capture <../../guides/examples>`
* :doc:`Utility / Infrastructure (JESD debug) <utility>`
* :doc:`Multi-Chip / Eval Systems <eval_systems>` for board-level
  platforms like QuadMxFE and Triton.

Reference (per-part API)
------------------------

.. toctree::
   :maxdepth: 1

   ../adi.ad6676
   ../adi.ad9081
   ../adi.ad9081_mc
   ../adi.ad9083
   ../adi.ad9084
   ../adi.ad9084_mc
   ../adi.ad9094
   ../adi.ad9213
   ../adi.ad9250
   ../adi.ad9265
   ../adi.ad9434
   ../adi.ad9467
   ../adi.ad9625
   ../adi.ad9680
