IMUs & Motion Sensors
=====================

Inertial measurement units (ADIS16xxx series) and standalone motion
sensors (ADXL accelerometers, ADXRS gyros). The ADIS family is the
flagship — 6-DOF or 10-DOF IMUs with on-chip filtering, calibration,
and SPI/UART interfaces. The ADXL/ADXRS parts are lighter-weight
accelerometers and gyros without the full IMU pipeline.

Parts in this family
--------------------

.. list-table::
   :header-rows: 1
   :widths: 30 50 20

   * - Part
     - Highlights
     - Interface
   * - :doc:`ADIS16375 <../adi.adis16375>` (and 16480/85/88/90/95/97)
     - Tactical-grade IMUs, 6/10 DOF
     - SPI
   * - :doc:`ADIS16460 <../adi.adis16460>`
     - Industrial-grade 6-DOF IMU
     - SPI
   * - :doc:`ADIS16475 <../adi.adis16475>`
     - Industrial 6-DOF, low-noise
     - SPI
   * - :doc:`ADIS16507 <../adi.adis16507>`
     - High-performance 6-DOF
     - SPI
   * - :doc:`ADIS16545 / 16547 <../adi.adis16545>`
     - Precision 6-DOF
     - SPI
   * - :doc:`ADIS16550 <../adi.adis16550>`
     - Next-gen 6-DOF
     - SPI
   * - :doc:`ADXL313 / 345 / 355 / 380 <../adi.adxl345>`
     - 3-axis accelerometers, varying precision
     - SPI / I²C
   * - :doc:`ADXRS290 <../adi.adxrs290>`
     - Dual-axis ultra-low-noise gyro
     - SPI

Mental model
------------

IMUs expose multiple channel types: ``accel_x/y/z``, ``anglvel_x/y/z``,
``temp``, and (on some parts) ``magn_x/y/z`` and ``deltaangl_*``,
``deltavelocity_*``. The default ``rx()`` returns a list of arrays in the
order of ``rx_enabled_channels``, which can be confusing across mixed
units (m/s² for accel, rad/s for gyro).

For mixed-unit IMUs, set ``rx_annotated = True`` to get a dict keyed by
channel name. Set ``rx_output_type = "SI"`` to get floats in m/s² / rad/s
instead of raw integer codes.

Minimal example
---------------

.. code-block:: python

   import adi

   imu = adi.adis16495(uri="serial:/dev/ttyUSB0,115200")
   imu.rx_enabled_channels = [3, 0, 6]   # accel_x, anglvel_x, temp
   imu.rx_buffer_size = 32
   imu.rx_annotated = True
   imu.rx_output_type = "SI"

   data = imu.rx()
   print(data["accel_x"])

Common properties
-----------------

* ``rx_enabled_channels`` — indices map to channel names; see the
  per-part autodoc for the order.
* ``rx_annotated`` — return a dict instead of a list.
* ``rx_output_type`` — "raw" or "SI".
* ``sample_rate`` — internal sample rate (most parts run from an
  internal clock).
* ``burst_data_selection`` (ADIS parts) — selects which fields go in
  the burst-read packet.

Common gotchas
--------------

* Channel indexing varies between ADIS sub-families. The order
  ``[accel_x, accel_y, accel_z, anglvel_x, anglvel_y, anglvel_z]`` is
  common but not universal. Use ``rx_annotated = True`` if you're not
  sure.
* SI scaling for the ``temp`` channel converts to °C; for accel/gyro
  it's m/s² / rad/s. The same scaling does not apply to the deltangle /
  deltvelocity channels in the same way.
* Some ADIS parts require a hard reset (toggle the reset pin) after
  power-up before they respond on SPI.
* ADXL parts have low-power modes that quietly halve the effective
  sample rate — read back ``sampling_frequency`` after configuration.
* Mag-equipped IMUs (ADIS16480, 16488, etc.) need a calibration step
  for the magnetometer to give useful values.

See also
--------

* :doc:`Concepts <../../concepts>` — annotated output and SI units.
* :doc:`Examples: annotated IMU output <../../guides/examples>`

Reference (per-part API)
------------------------

.. toctree::
   :maxdepth: 1

   ../adi.adis16375
   ../adi.adis16460
   ../adi.adis16475
   ../adi.adis16480
   ../adi.adis16485
   ../adi.adis16488
   ../adi.adis16490
   ../adi.adis16495
   ../adi.adis16497
   ../adi.adis16507
   ../adi.adis16545
   ../adi.adis16547
   ../adi.adis16550
   ../adi.adxl313
   ../adi.adxl345
   ../adi.adxl355
   ../adi.adxl380
   ../adi.adxrs290
