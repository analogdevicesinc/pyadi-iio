Buffers
==================

Using buffers or transmitting and receiving data is done through interacting with two methods.

For receivers this is the **rx** method. How data is captured and therefore produced by this method is dependent on two main properties:

* **rx_enabled_channels**: This is an array of integers (or channel names) and the number of elements in the array will determine the number of list items returned by **rx**. For devices with complex data types these are the indexes of the complex channels, not the individual I or Q channels. When len(**rx_enabled_channels**) == 1, **rx** will return just a single array and not a single array within a list.
* **rx_buffer_size**: This is the number of samples returned in each array within the list. If the device produces complex data, like a transceiver, it will return complex data. This is defined by the author of each device specific class.

For transmitters this is the **tx** method. How data is sent and therefore must be passed by this method is dependent on one main property:

* **tx_enabled_channels**: This is an array of integers and the number of elements in the array will determine the number of items in the list to be submitted to **tx**. Like for **rx_enabled_channels**, devices with complex data types these are the indexes of the complex channels, not the individual I or Q channels. When only a single channel is enabled the data can be passed to **tx** as just an array and not an array within a list.

**rx_enabled_channels** must have a length greater than zero but **tx_enabled_channels** can be set to None or an empty list. In this case when **tx** is called it must be called without inputs. This is a special case and will connect a zero source into the TX input stream within the FPGA for FPGA based devices. For background on how this internally works with FPGA based devices reference the generic `DAC driver <https://wiki.analog.com/resources/tools-software/linux-drivers/iio-dds/axi-dac-dds-hdl>`_.

Cyclic Mode
--------------
In many cases, it can be useful to continuously transmit a signal over and over, even for just debugging and testing. This can be especially handy when the hardware you are using has very high transmit or receive rates, and therefore impossible to keep providing data to in real-time. To complement these use cases it is possible to create transmit buffer which repeats, which we call **cyclic buffers**. Cyclic buffers are identical or normal or non-cyclic buffers, except when they reach hardware they will continuously repeat or be transmitted. Here is a small example on how to create a cyclic buffer:

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

Annotated Buffers
------------------

By default buffers appear as an array or a list of arrays. This can be confusing if all your channels do not produce similar data. For example, for IMUs like ADI16495 certain channels are for acceleration data and others are for angular velocity. To label this data the *rx_annotated* property can be used. When setting it to True the output of the **rx** method will be a dictionary with keys as channel names. Here an example:

.. code-block:: python

 import adi

 dev = adi.adis16495()
 dev.rx_enabled_channels = [0, 3]
 print(dev.rx())
 dev.rx_annotated = True
 print(dev.rx())

With output

.. code-block:: bash

   [array([    35681,     84055,   -175914,   -203645,    698249,    -51670,
         -1770250,   1529968,   2586191,  -5353355,   -827741,  11736339,
         -9847894, -17242014,  97421833, 277496774], dtype=int32),
   array([     49151,     753663,    3571711,    9928703,   18956287,
            25165823,   18612223,  -10125313,  -60850176, -114491392,
         -131350528,  -61521920,  135069695,  466845695,  899235839,
         1362378751], dtype=int32)]
   {'accel_x': array([1775091711, 2072264703, 2147483647, 2147483647, 2147483647,
         2147483647, 2143404031, 2125430783, 2123120639, 2130821119,
         2139488255, 2144911359, 2147041279, 2147467263, 2147483647,
         2147483647], dtype=int32),
   'anglvel_x': array([357750219, 335109279, 323033231, 337667193, 337100396, 330408402,
         333459194, 335322576, 333247166, 333223475, 333996322, 333805525,
         333659152, 333664680, 333718473, 333895650], dtype=int32)}


Buffer Units
---------------

For certain devices it is possible to convert types to scientific units, such as volts, degrees, or meters per second among others. This is controlled by setting the property **rx_output_type** to either *raw* or *SI*. If set to *SI*, returned data from the **rx** method will be in scientific units (assuming its supported by the driver). Below is an example using an IMU:

.. code-block:: python

 import adi

 dev = adi.adis16495()
 dev.rx_annotated = True  # Make channel names appear in data
 dev.rx_enabled_channels = [3]  # channel 0 is angular velocity in the x direction
 print(dev.rx())
 dev.rx_output_type = "SI"
 print(dev.rx())

With output

.. code-block:: bash

 {'anglvel_x': array([    35644,     84039,   -175647,   -203867,    697612,    -50201,
        -1770177,   1526291,   2589741,  -5349126,   -839188,  11738313,
        -9824911, -17267701,  97333042, 277410285], dtype=int32)}
 {'anglvel_x': array([9.29996712, 9.71257202, 9.40097973, 9.78345151, 9.77009362,
       9.59662456, 9.67300333, 9.71593538, 9.65847317, 9.6580597 ,
       9.68022501, 9.67715545, 9.67511814, 9.67609361, 9.67323293,
       9.67104074])}


To understand the exact scaling the driver documentation should be reviewed.

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
