Buffers
==================

Using buffers or transmitting and receiving data is done through interacting with two methods.

For receivers this is the **rx** method. How data is captured and therefore produced by this method is dependent on two main properties:

* **rx_enabled_channels**: This is an array of integers and the number of elements in the array will determine the number of columns returned by **rx**.
* **rx_buffer_size**: This is the number of samples returned in each column. If the device produces complex data, like a transceiver, it will return complex data. This is defined by the author of each device specific class.

For transmitters this is the **tx** method. How data is sent and therefore must be passed by this method is dependent on one main property:

* **tx_enabled_channels**: This is an array of integers and the number of elements in the array will determine the number of columns to be submitted to **tx**.


Members
--------------
.. automodule:: adi.rx_tx
   :members:


Buffer Examples
---------------

Collect data from one channel

.. code-block:: python

 import adi
 sdr = adi.ad9361()
 # Get both complex channel back
 sdr.rx_enabled_channels = [0]
 chan1 = sdr.rx()

Collect data from two channels

.. code-block:: python

 import adi
 sdr = adi.ad9361()
 # Get both complex channel back
 sdr.rx_enabled_channels = [0 1]
 data = sdr.rx()
 chan1 = data[0]
 chan2 = data[1]

Send data on two channels

.. code-block:: python

 import adi
 import numpy as np
 # Create radio
 sdr = adi.ad9371()
 sdr.tx_enabled_channels = [0, 1]
 # Create a sinewave waveform
 N = 1024
 fs = int(sdr.tx_sample_rate)
 fc = 40000000
 ts = 1 / float(fs)
 t = np.arange(0, N * ts, ts)
 i = np.cos(2 * np.pi * t * fc) * 2 ** 14
 q = np.sin(2 * np.pi * t * fc) * 2 ** 14
 iq = i + 1j * q
 fc = -30000000
 i = np.cos(2 * np.pi * t * fc) * 2 ** 14
 q = np.sin(2 * np.pi * t * fc) * 2 ** 14
 iq2 = i + 1j * q
 # Send data to both channels
 sdr.tx([iq, iq2])
