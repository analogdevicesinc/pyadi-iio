Clocks, PLLs & Synthesizers
===========================

Frequency synthesizers (ADF series) and clock-tree distribution parts
(HMC). No data buffer — these are control-plane devices. You configure
output frequencies and read back lock status.

Parts in this family
--------------------

.. list-table::
   :header-rows: 1
   :widths: 25 60 15

   * - Part
     - Highlights
     - Interface
   * - :doc:`ADF4030 <../adi.adf4030>`
     - 10-channel BAW-based PLL clock generator
     - SPI
   * - :doc:`ADF4159 <../adi.adf4159>`
     - Direct-modulation fractional-N PLL (FMCW radar)
     - SPI
   * - :doc:`ADF4355 / 4371 / 4377 / 4382 <../adi.adf4355>`
     - Wideband fractional-N PLLs, 4–13 GHz range
     - SPI
   * - :doc:`ADF5610 / 5611 <../adi.adf5610>`
     - Microwave PLL+VCO, up to 15 GHz
     - SPI
   * - :doc:`HMC7044 <../adi.hmc7044>`
     - 14-output clock distribution / JESD-friendly clocking
     - SPI

Mental model
------------

These are pure control parts: no ``rx()``, no ``tx()``. Properties set
the output frequency, reference frequency, charge-pump current, etc.,
and readbacks tell you whether the PLL is locked.

Most parts in this family are used **as supporting infrastructure** for
JESD ADCs/DACs and transceivers — HMC7044 in particular shows up as the
clock source for nearly every JESD-class system. They're rarely the
center of an application by themselves; the ADF4159 (FMCW radar) is
the main exception.

Minimal example
---------------

Property names are part-specific. ADF4371 exposes one frequency knob
per RF output (``rf8_frequency``, ``rf16_frequency``, ``rf32_frequency``,
``rfaux8_frequency``):

.. code-block:: python

   import adi

   pll = adi.adf4371(uri="ip:analog.local")
   pll.rf8_frequency = 5_000_000_000   # 5 GHz on the 8 GHz output

ADF4159 uses a single ``frequency`` property; HMC7044 exposes one
``<channel>_frequency`` per output (14 outputs). Always check the
per-part API page linked below.

Common properties
-----------------

* ``frequency`` / ``rf<n>_frequency`` / ``<channel>_frequency`` —
  target output frequency in Hz. Naming is part-specific.
* ``reference_frequency`` — input reference frequency (for parts that
  expose it, e.g. ADF4377, HMC7044).
* ``charge_pump_current`` — loop filter charge-pump setting.
* For multi-output parts (HMC7044, ADF4030): per-output configuration
  via per-channel properties.

Common gotchas
--------------

* "Locked" status depends on the loop filter being correctly designed
  for the target frequency. A frequency that lies outside the lock
  range will silently fail to acquire — check whatever lock-detect
  property the part exposes.
* HMC7044 in JESD systems is usually pre-configured by an HDL-level
  init script; touching its properties from pyadi-iio can break the
  JESD link clocking.
* Reference frequencies are part-specific; setting a target output
  outside the achievable range gets clamped on some parts and rejected
  on others.
* ADF4371 has no single ``frequency`` property — each of the four RF
  outputs (8 GHz, aux 8 GHz, 16 GHz, 32 GHz) has its own
  ``rf<n>_frequency`` setter.

See also
--------

* :doc:`Concepts <../../concepts>`
* :doc:`JESD ADCs <jesd_adcs>` / :doc:`JESD DACs <jesd_dacs>` for the
  systems these clocks support.

Reference (per-part API)
------------------------

.. toctree::
   :maxdepth: 1

   ../adi.adf4030
   ../adi.adf4159
   ../adi.adf4355
   ../adi.adf4371
   ../adi.adf4377
   ../adi.adf4382
   ../adi.adf5610
   ../adi.adf5611
   ../adi.hmc7044
