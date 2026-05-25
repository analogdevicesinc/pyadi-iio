Sensors & Specialty
===================

Non-IMU sensing parts and specialty converters that don't fit a cleaner
bucket: temperature, capacitance, isolated inputs, resolver-to-digital,
optical / photoplethysmography, current sense, and lidar.

Parts in this family
--------------------

.. list-table::
   :header-rows: 1
   :widths: 25 60 15

   * - Part
     - Highlights
     - Quantity
   * - :doc:`AD2S1210 <../adi.ad2s1210>`
     - Resolver-to-digital converter
     - Angle
   * - :doc:`AD5940 <../adi.ad5940>`
     - High-precision impedance / electrochemical AFE
     - Impedance
   * - :doc:`AD7291 <../adi.ad7291>`
     - 8-channel voltage + temperature monitor
     - V / °C
   * - :doc:`AD7405 <../adi.ad7405>`
     - Isolated 16-bit sigma-delta modulator
     - V
   * - :doc:`AD7746 <../adi.ad7746>`
     - Capacitance-to-digital converter
     - F
   * - :doc:`ADA4356 LiDAR <../adi.ada4356_lidar>`
     - LiDAR analog front-end
     - Optical
   * - :doc:`ADPD188 / ADPD410x / ADPD1080 <../adi.adpd1080>`
     - Optical / photoplethysmography front-ends
     - Optical
   * - :doc:`ADT7420 <../adi.adt7420>`
     - High-accuracy I²C digital temperature sensor
     - °C
   * - :doc:`FMCLIDAR1 <../adi.fmclidar1>`
     - FMC LiDAR evaluation card
     - Time-of-flight
   * - :doc:`LM75 <../adi.lm75>`
     - I²C temperature sensor (legacy)
     - °C
   * - :doc:`LTC2983 <../adi.ltc2983>`
     - Multi-channel temperature measurement
     - °C
   * - :doc:`MAX14001 <../adi.max14001>`
     - Isolated analog input
     - V
   * - :doc:`MAX31855 / MAX31865 <../adi.max31855>`
     - Thermocouple / RTD-to-digital
     - °C
   * - :doc:`MAX9611 <../adi.max9611>`
     - Current-sense amplifier + 12-bit ADC
     - A

Mental model
------------

Most parts in this family expose one or more channels with ``raw`` and
``scale`` (or a SI-output mode). Conversion runs on demand —
``adc.rx()`` (where supported) or ``adc.channel[i].raw`` (for
register-poll parts) triggers a conversion.

Some parts have a streaming buffer (ADPD410x, AD5940) for continuous
optical / impedance capture. Most don't.

Minimal example
---------------

.. code-block:: python

   import adi

   temp = adi.adt7420(uri="ip:analog.local")
   # The ADT7420 exposes a single ``temp`` channel; read its value:
   print(temp.temp.temp_val)   # raw temperature reading (millidegrees C on Linux)

Common properties
-----------------

* ``temp.temp_val`` (temperature-class parts) — direct read from the
  temperature channel.
* ``channel[i].raw`` / ``channel[i].scale`` — raw codes and scaling.
* ``rx_output_type = "SI"`` — for streaming parts that support it.

Common gotchas
--------------

* Thermocouple parts (MAX31855) and RTD parts (MAX31865) report fault
  conditions through separate properties; a read of the temperature
  value may return garbage during a fault.
* Optical parts (ADPD series) have complex LED / sample-timing
  configuration — read the per-part datasheet for the right setup
  sequence.
* AD5940 has many modes (impedance, electrochemical, temperature);
  each requires a different setup script.
* The FMCLIDAR1 card and the ADA4356-LiDAR AFE both relate to LiDAR
  but operate at different levels — FMCLIDAR1 is a board-level eval
  product; ADA4356-LiDAR is the discrete AFE.

See also
--------

* :doc:`Concepts <../../concepts>` — raw vs. SI units.

Reference (per-part API)
------------------------

.. toctree::
   :maxdepth: 1

   ../adi.ad2s1210
   ../adi.ad5940
   ../adi.ad7291
   ../adi.ad7405
   ../adi.ad7746
   ../adi.ada4356_lidar
   ../adi.adpd188
   ../adi.adpd410x
   ../adi.adpd1080
   ../adi.adt7420
   ../adi.fmclidar1
   ../adi.lm75
   ../adi.ltc2983
   ../adi.max14001
   ../adi.max31855
   ../adi.max31865
   ../adi.max9611
