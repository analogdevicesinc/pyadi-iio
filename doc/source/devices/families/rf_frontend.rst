RF Front-End
============

Discrete RF signal-conditioning parts: amplifiers, attenuators, mixers,
switches, and tunable filters. These sit between an antenna and a
transceiver/converter and are typically controlled per-set-point, not
streamed.

Parts in this family
--------------------

.. list-table::
   :header-rows: 1
   :widths: 25 60 15

   * - Part
     - Highlights
     - Type
   * - :doc:`ADA4961 <../adi.ada4961>`
     - DC – 4 GHz digitally controlled VGA
     - VGA
   * - :doc:`ADL5240 <../adi.adl5240>`
     - 0.1 – 4 GHz analog VGA
     - VGA
   * - :doc:`ADL5960 <../adi.adl5960>`
     - 100 MHz – 20 GHz vector network analyzer front-end
     - Mixer / RX
   * - :doc:`ADL8113 <../adi.adl8113>`
     - 4-port SP4T RF switch
     - Switch
   * - :doc:`ADMV8818 <../adi.admv8818>`
     - 2 – 18 GHz digitally tunable filter
     - Filter
   * - :doc:`ADRF5720 <../adi.adrf5720>`
     - 9 kHz – 60 GHz digital attenuator
     - Attenuator

Mental model
------------

All control-plane: no buffers. Configure a gain or attenuation, switch
state, or filter passband, and the device sits in that state until
reconfigured.

Minimal example
---------------

.. code-block:: python

   import adi

   atten = adi.adrf5720(uri="ip:analog.local")
   atten.attenuation = 15.5   # dB

Common properties
-----------------

* ``gain`` / ``attenuation`` — signed value in dB.
* ``frequency`` — for tunable filters and mixers, the center / LO
  frequency.
* ``switch_state`` / channel-state for switches.

Common gotchas
--------------

* These parts are often controlled by GPIO or a simple SPI register
  write. The pyadi-iio class abstracts that, but firmware on the host
  system has to provide the IIO driver — make sure the driver is in
  the device tree before construction.
* Step-size resolution is part-specific (e.g., 0.25 dB for ADRF5720).
  Setting a value that isn't on the supported grid gets clamped.

See also
--------

* :doc:`Concepts <../../concepts>`
* :doc:`RF Transceivers <rf_transceivers>` — common pairing.

Reference (per-part API)
------------------------

.. toctree::
   :maxdepth: 1

   ../adi.ada4961
   ../adi.adl5240
   ../adi.adl5960
   ../adi.adl8113
   ../adi.admv8818
   ../adi.adrf5720
