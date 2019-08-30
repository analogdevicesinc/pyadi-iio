Examples
===================


Configuring hardware properties

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

Using URIs to access specific devices

.. code-block:: python

  import adi
  # Create device from specific uri address
  sdr = adi.ad9361(uri="ip:192.168.2.1")
  data = sdr.rx()

Other complex examples are available in the `source repository <https://github.com/analogdevicesinc/pyadi-iio/tree/master/examples>`_
