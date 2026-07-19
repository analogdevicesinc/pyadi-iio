CN0532 vibration sensor board
=============================

The :class:`adi.cn0532.cn0532` interface extends the CN0540 data-acquisition
interface for the CN0532 vibration sensor board and its ADXL1002 accelerometer.
It inherits CN0540 buffered acquisition, sample-rate, bias-voltage, and GPIO
controls and adds automatic offset calibration.

Capture vibration data
----------------------

.. code-block:: python

   import adi

   sensor = adi.cn0532(uri="ip:192.168.2.1")
   sensor.sample_rate = 256000
   sensor.rx_buffer_size = 4096

   acceleration_signal = sensor.rx()
   sensor.rx_destroy_buffer()

The returned array contains the board's single AD7768-1 receive channel as
floating-point samples. Convert the samples to application-specific vibration
units using the sensor configuration and calibration for your setup.

Offset calibration
------------------

Call :meth:`~adi.cn0532.cn0532.calibrate` while the sensor is stationary and
connected. Calibration adjusts the LTC2606 bias DAC over 20 iterations to make
the AD7768-1 ADC codes approach zero mean:

.. code-block:: python

   sensor = adi.cn0532(uri="ip:192.168.2.1")
   sensor.calibrate()

Calibration destroys an active RX buffer before changing the DAC. A subsequent
``rx()`` call creates a new buffer. If the required correction is outside the
DAC range, the method clamps the setting and prints a warning that calibration
may not converge.

Inherited board controls
------------------------

CN0532 inherits the CN0540 controls, including
:attr:`~adi.cn0540.cn0540.shift_voltage`,
:attr:`~adi.cn0540.cn0540.sensor_voltage`,
:attr:`~adi.cn0540.cn0540.fda_mode`, and
:attr:`~adi.cn0540.cn0540.monitor_powerup`. See :doc:`adi.cn0540` for the full
board-control overview.

API reference
-------------

.. autoclass:: adi.cn0532.cn0532
   :members:
   :inherited-members:
   :show-inheritance:
