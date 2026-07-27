Examples
===================

Here is a collection of small examples which demonstrate how to interface with different devices in different ways.

Configuring hardware properties and reading back settings

.. code-block:: python

  # Import the library
  import adi

  # Create a device interface
  sdr = adi.ad9361()
  # Configure properties
  sdr.rx_rf_bandwidth = 4000000
  sdr.rx_lo = 2000000000
  sdr.tx_lo = 2000000000
  sdr.tx_cyclic_buffer = True
  sdr.tx_hardwaregain = -30
  sdr.gain_control_mode = "slow_attack"
  # Read back properties from hardware
  print(sdr.rx_hardwaregain)

Send data to a device and receiving data from a device

.. code-block:: python

  import adi
  import numpy as np

  sdr = adi.ad9361()
  data = np.arange(1, 10, 3)
  # Send
  sdr.tx(data)
  # Receive
  data_rx = sdr.rx()

Configure the DDS of a transmit capable FPGA based device

.. code-block:: python

  import adi

  sdr = adi.DAQ2()
  # Configure DDS
  tone_freq_hz = 1000  # In Hz
  tone_scale = 0.9  # Range: 0-1.0
  tx_channel = 1  # Starts at 0
  sdr.dds_single_tone(tone_freq_hz, tone_scale, tx_channel)


Using URIs to access specific devices over the network

.. code-block:: python

  import adi

  # Create device from specific uri address
  sdr = adi.ad9361(uri="ip:192.168.2.1")
  data = sdr.rx()

Using URIs to access specific devices over USB

.. code-block:: python

  import adi

  # Create device from specific uri address
  sdr = adi.Pluto(uri="usb:1.24.5")
  data = sdr.rx()


Other complex examples are available in the `source repository <https://github.com/analogdevicesinc/pyadi-iio/tree/master/examples>`_
