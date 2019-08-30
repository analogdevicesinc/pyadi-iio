Buffers
==================

Using buffers or transmitting and receiving data is done through interacting with two methods.

For receivers this is the **rx** method. How data is captured and therefore produced by this method is dependent on two main properties:

* **rx_enabled_channels**: This is an array of integers and the number of elements in the array will determine the number of columns returned by **rx**.
* **rx_buffer_size**: This is the number of samples returned in each column. If the device produces complex data, like a transceiver, it will return complex data. This is defined by the author of each device specific class.

For transmitters this is the **tx** method. How data is sent and therefore must be passed by this method is dependent on one main property:

* **tx_enabled_channels**: This is an array of integers and the number of elements in the array will determine the number of columns to be submitted to **tx**.


.. toctree::
   :maxdepth: 1

   members
   examples
