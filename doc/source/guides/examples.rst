Examples
========

End-to-end workflows that combine connection, configuration, capture,
and post-processing. Each example assumes ``pyadi-iio``, ``numpy``, and
``matplotlib`` are installed; replace the example URI with one that
matches your hardware.

For shorter snippets covering one feature at a time, see the
:doc:`concepts page <../concepts>` and the :doc:`buffers page <../buffers/index>`.
For longer scripts (including FPGA-board-specific demos), see the
``examples/`` directory in the
`source repository <https://github.com/analogdevicesinc/pyadi-iio/tree/master/examples>`_.

Capture and plot
----------------

Connect to a PlutoSDR, configure the LO and sample rate, capture a
buffer, and plot the magnitude spectrum.

.. code-block:: python

   import adi
   import numpy as np
   import matplotlib.pyplot as plt

   sdr = adi.Pluto(uri="ip:192.168.2.1")
   sdr.sample_rate = 2_000_000
   sdr.rx_lo = 2_400_000_000
   sdr.rx_rf_bandwidth = 2_000_000
   sdr.gain_control_mode = "slow_attack"
   sdr.rx_buffer_size = 4096

   data = sdr.rx()  # complex128 ndarray, length 4096

   fft = np.fft.fftshift(np.fft.fft(data))
   psd = 20 * np.log10(np.abs(fft) + 1e-12)
   freqs = np.fft.fftshift(np.fft.fftfreq(len(data), 1 / sdr.sample_rate))

   plt.plot(freqs / 1e6, psd)
   plt.xlabel("Frequency offset (MHz)")
   plt.ylabel("Magnitude (dB)")
   plt.show()

The data shape is ``complex128`` because the Pluto is a complex part. The
:doc:`concepts page <../concepts>` covers the data shape contract for
both complex and real parts.

Cyclic TX of a tone
-------------------

Generate a complex sinusoid and transmit it in a loop. Cyclic mode is
the practical way to keep multi-MSPS transmitters fed from Python — see
the buffer mechanics on the :doc:`buffers page <../buffers/index>`.

.. code-block:: python

   import adi
   import numpy as np

   sdr = adi.Pluto(uri="ip:192.168.2.1")
   sdr.sample_rate = 2_000_000
   sdr.tx_lo = 2_400_000_000
   sdr.tx_rf_bandwidth = 2_000_000
   sdr.tx_hardwaregain_chan0 = -10

   N = 1024
   fc = 100_000
   t = np.arange(N) / sdr.sample_rate
   iq = (np.cos(2 * np.pi * fc * t) + 1j * np.sin(2 * np.pi * fc * t)) * 2**14

   sdr.tx_cyclic_buffer = True
   sdr.tx(iq)

   # The buffer is now repeating in hardware. Leave it running, or...
   sdr.tx_destroy_buffer()  # required before re-arming with new data

Common gotcha: once a cyclic buffer is loaded, any further ``tx()`` call
will fail until ``tx_destroy_buffer()`` is called.

Multi-channel capture
---------------------

A multi-channel ADC returns a list of arrays, one per enabled channel.

.. code-block:: python

   import adi

   adc = adi.ad7768_4(uri="ip:analog.local")
   adc.rx_buffer_size = 1024

   # Single channel — returns one ndarray
   adc.rx_enabled_channels = [0]
   chan0 = adc.rx()
   print(type(chan0), chan0.shape)  # ndarray, (1024,)

   # Two channels — returns a list of ndarrays
   adc.rx_enabled_channels = [0, 1]
   data = adc.rx()
   print(type(data), len(data), data[0].shape)  # list, 2, (1024,)

The single-vs-list output behavior is intentional: scalar in, scalar
out — but it can surprise users who expect a list of length 1 with one
channel enabled. See the :doc:`concepts page <../concepts>` for the
full data shape contract.

Annotated output for IMUs
-------------------------

For IMUs with mixed channel types (acceleration, angular velocity,
temperature) the array-of-arrays output is hard to read. Setting
``rx_annotated = True`` makes ``rx()`` return a dict keyed by channel
name.

.. code-block:: python

   import adi

   imu = adi.adis16495(uri="serial:/dev/ttyUSB0,115200")
   imu.rx_buffer_size = 16
   imu.rx_enabled_channels = [0, 3]  # accel_x and anglvel_x
   imu.rx_annotated = True

   data = imu.rx()
   print(data.keys())          # dict_keys(['accel_x', 'anglvel_x'])
   print(data["accel_x"][:4])

Combine with ``rx_output_type = "SI"`` to get the values in m/s² and
rad/s instead of raw codes.

See also
--------

* :doc:`Concepts <../concepts>`
* :doc:`Buffers <../buffers/index>`
* :doc:`FPGA features (DDS, DMA sync) <../fpga/index>`
* Longer scripts in the `examples/` directory of the repo.
