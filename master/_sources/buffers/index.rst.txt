Buffers
==================

Using buffers or transmitting and receiving data is done through interacting with two methods.

For receivers this is the **rx** method. How data is captured and therefore produced by this method is dependent on two main properties:

* **rx_enabled_channels**: This is an array of integers and the number of elements in the array will determine the number of list items returned by **rx**. For devices with complex data types these are the indexes of the complex channels, not the individual I or Q channels.
* **rx_buffer_size**: This is the number of samples returned in each column. If the device produces complex data, like a transceiver, it will return complex data. This is defined by the author of each device specific class.

For transmitters this is the **tx** method. How data is sent and therefore must be passed by this method is dependent on one main property:

* **tx_enabled_channels**: This is an array of integers and the number of elements in the array will determine the number of items in list to be submitted to **tx**. Like for **rx_enabled_channels**, devices with complex data types these are the indexes of the complex channels, not the individual I or Q channels.

**rx_enabled_channels** must have a length greater than zero but **tx_enabled_channels** can be set to None or an empty list. In this case when **tx** is called it must be called without inputs. This is a special case and will connect a zero source into the TX input stream within the FPGA for FPGA based devices. For background on how this internally works with FPGA based devices reference the generic `DAC driver <https://wiki.analog.com/resources/tools-software/linux-drivers/iio-dds/axi-dac-dds-hdl>`_.

Cyclic Mode
--------------
In many cases, it can be useful to continuously transmit a signal over and over, even for just debugging and testing. This can be especially handy when the hardware you are using has very high transmit or receive rates, and therefore impossible to keep providing data to. To complement these use cases it is possible to create transmit buffer which repeats, which we call **cylic buffers**. Cyclic buffers are identical or normal or non-cylic buffers, except when they reach hardware they will continuously repeat or be transmitted. Here is a small example on how to create a cyclic buffer:

.. code-block:: python

 import adi

 sdr = adi.ad9361()
 # Create a complex sinusoid
 fc = 3000000
 N = 1024
 ts = 1 / 30000000.0
 t = np.arange(0, N * ts, ts)
 i = np.cos(2 * np.pi * t * fc) * 2 ** 14
 q = np.sin(2 * np.pi * t * fc) * 2 ** 14
 iq = i + 1j * q
 # Enable cyclic buffers
 sdr.tx_cyclic_buffer = True
 # Send data cyclically
 sdr.tx(iq)

At this point, the transmitter will keep transmitting the create sinusoid indefinitely until the buffer is destroyed or the *sdr* object destructor is called. Once data is pushed to hardware with a cyclic buffer the buffer must be manually destroyed or an error will occur if more data push. To update the buffer use the **tx_destroy_buffer** method before passing a new vector to the **tx** method.

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
 # Get complex data back
 sdr.rx_enabled_channels = [0]
 chan1 = sdr.rx()

Collect data from two channels

.. code-block:: python

 import adi

 sdr = adi.ad9361()
 # Get both complex channel back
 sdr.rx_enabled_channels = [0, 1]
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
