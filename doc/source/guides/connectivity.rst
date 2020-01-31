Connectivity
===================

Since pyadi-iio is built on top of libiio, it can use the different `backends <https://wiki.analog.com/resources/tools-software/linux-software/libiio>`_ which allow device control and data transfer to and from devices remotely. These backends include serial, Ethernet, PCIe, USB, and of course locally connected devices can be controlled through the local backend. Connecting to a board remotely over a specific backend is done by defining a specific universal resource indicator (URI) and passing it the class constructors for a specific device. Here is a simple example that uses the Ethernet backend with a target board with IP address 192.168.2.1:

.. code-block:: python

  # Import the library
  import adi

  # Create a device interface
  sdr = adi.ad9361(uri="ip:192.168.2.1")
  # Read back properties from hardware
  print(sdr.rx_hardwaregain)
