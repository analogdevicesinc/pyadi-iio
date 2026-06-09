High-Speed / JESD DACs
======================

GSPS-class DACs that receive samples from an FPGA — most use JESD204B or
204C serial lanes; the AD9739A uses parallel LVDS. The mirror image of
the JESD ADC family: complex baseband in, RF or wideband real out,
fixed sample rate set by the HDL profile.

Parts in this family
--------------------

.. list-table::
   :header-rows: 1
   :widths: 20 55 25

   * - Part
     - Highlights
     - Typical platform
   * - :doc:`AD9136 <../adi.ad9136>`
     - Dual 16-bit, 2.8 GSPS, JESD204B
     - AD9136 EVM
   * - :doc:`AD9144 <../adi.ad9144>`
     - Quad 16-bit, 2.8 GSPS, JESD204B
     - FMCDAQ2
   * - :doc:`AD9152 <../adi.ad9152>`
     - Dual 16-bit, 2.25 GSPS, JESD204B
     - FMCDAQ3
   * - :doc:`AD9162 <../adi.ad9162>`
     - 16-bit, 12 GSPS interpolating
     - AD9162 EVM
   * - :doc:`AD9166 <../adi.ad9166>`
     - 16-bit, 12 GSPS with on-chip NCO
     - AD9166 EVM
   * - :doc:`AD9172 <../adi.ad9172>`
     - Dual 16-bit, 12.6 GSPS, JESD204B
     - AD9172 EVM
   * - :doc:`AD9739A <../adi.ad9739a>`
     - 14-bit, 2.5 GSPS, LVDS
     - AD9739A EVM

Mental model
------------

``tx()`` accepts an ndarray (or list of ndarrays, one per enabled
channel) and pushes it to the DAC via DMA. For parts that include a
digital upconverter (DUC), the input is complex baseband and the part
mixes to the configured NCO frequency. For parts without a DUC, the
input is real, at the DAC sample rate.

Like the JESD ADC family, sample rate is HDL-fixed. Interpolation
factors, NCO frequencies, and per-channel scaling are runtime-settable.

For continuous waveforms at GSPS rates, use cyclic mode
(``tx_cyclic_buffer = True``) — Python can't keep refilling the buffer
fast enough otherwise.

Minimal example
---------------

.. code-block:: python

   import adi
   import numpy as np

   dac = adi.ad9172(uri="ip:analog.local")
   dac.tx_enabled_channels = [0]

   N = 1024
   fc = 1e6
   t = np.arange(N) / dac.sample_rate
   iq = (np.cos(2 * np.pi * fc * t) + 1j * np.sin(2 * np.pi * fc * t)) * 2**14

   dac.tx_cyclic_buffer = True
   dac.tx(iq)

Common properties
-----------------

* ``tx_enabled_channels`` — indices of enabled channels.
* ``tx_cyclic_buffer`` — enable cyclic playback.
* ``sample_rate`` / ``sampling_frequency`` — HDL-driven; usually read-only.
* DUC properties: NCO frequencies, interpolation factors, channel
  scaling.
* DDS properties on FPGA-side helpers (``dds_single_tone``,
  ``dds_frequencies``) — see :doc:`../../fpga/index`.

Common gotchas
--------------

* Cyclic mode requires ``tx_destroy_buffer()`` before re-arming. See
  :doc:`../../guides/troubleshooting`.
* For parts with a DUC, the input dtype must be complex. Passing a
  real ndarray either errors or silently does the wrong thing.
* NCO frequencies must be within the supported range for the configured
  interpolation; out-of-range values get clamped.
* The FPGA-side DDS (``dds_*`` properties) and the chip-side DUC NCO are
  different things — pyadi-iio exposes both. The DDS replaces the DMA
  source; the DUC NCO mixes the DMA output.

See also
--------

* :doc:`Concepts <../../concepts>`
* :doc:`Examples: cyclic TX <../../guides/examples>`
* :doc:`FPGA features (DDS, DMA sync) <../../fpga/index>`
* :doc:`Multi-Chip / Eval Systems <eval_systems>` for board-level
  TX platforms (FMCDAQ2, FMCDAQ3).

Reference (per-part API)
------------------------

.. toctree::
   :maxdepth: 1

   ../adi.ad9136
   ../adi.ad9144
   ../adi.ad9152
   ../adi.ad9162
   ../adi.ad9166
   ../adi.ad9172
   ../adi.ad9739a
