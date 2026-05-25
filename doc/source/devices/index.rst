Supported Devices
=================

pyadi-iio supports ~150 ADI parts. Devices are grouped into families that
share usage patterns. Pick the family that matches your part to read the
shared usage notes, then drill into the per-part API reference under it.

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Family
     - Description
   * - :doc:`RF Transceivers <families/rf_transceivers>`
     - Integrated wide-tuning RF transceivers (Pluto, AD9361, ADRV9002/9009).
   * - :doc:`High-Speed / JESD ADCs <families/jesd_adcs>`
     - GSPS-class ADCs with JESD204 data paths (AD9081, AD9084, AD9680, ...).
   * - :doc:`High-Speed / JESD DACs <families/jesd_dacs>`
     - GSPS-class DACs with JESD204 data paths (AD9136, AD9162, AD9172, ...).
   * - :doc:`Precision ADCs <families/precision_adcs>`
     - SAR / sigma-delta / integrated-signal-chain ADCs.
   * - :doc:`Precision DACs <families/precision_dacs>`
     - SPI/I2C DACs and DAC+ADC combos.
   * - :doc:`IMUs & Motion Sensors <families/imus_motion>`
     - ADIS16xxx IMUs, ADXL accelerometers, ADXRS gyroscopes.
   * - :doc:`Clocks, PLLs & Synthesizers <families/clocks_plls>`
     - ADF synthesizers and HMC clock generators.
   * - :doc:`RF Front-End <families/rf_frontend>`
     - Discrete amplifiers, attenuators, mixers, switches, tunable filters.
   * - :doc:`Beamformers & Phased Array <families/beamformers>`
     - ADAR1000, CN0566.
   * - :doc:`Sensors & Specialty <families/sensors_specialty>`
     - Temperature, capacitance, isolated, resolver, optical, lidar.
   * - :doc:`Multi-Chip / Eval Systems <families/eval_systems>`
     - FMC/DAQ daughter cards, CN0xxx reference designs, multi-SOM systems.
   * - :doc:`Utility / Infrastructure <families/utility>`
     - JESD debug, gen_mux, tdd, tddn, switches, helpers.

.. toctree::
   :hidden:

   families/rf_transceivers
   families/jesd_adcs
   families/jesd_dacs
   families/precision_adcs
   families/precision_dacs
   families/imus_motion
   families/clocks_plls
   families/rf_frontend
   families/beamformers
   families/sensors_specialty
   families/eval_systems
   families/utility

-----

.. automodule:: adi
   :members:
   :undoc-members:
   :show-inheritance:
