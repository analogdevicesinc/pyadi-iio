Connectivity
===================

Since pyadi-iio is built on top of libiio, it can use the different `backends <https://wiki.analog.com/resources/tools-software/linux-software/libiio>`_ which allow device control and data transfer to and from devices remotely. These backends include serial, Ethernet, PCIe, USB, and of course locally connected devices can be controlled through the local backend. Connecting to a board remotely over a specific backend is done by defining a specific universal resource indicator (URI) and passing it to the class constructors for a specific device. Here is a simple example that uses the Ethernet backend with a target board with IP address 192.168.2.1:

.. code-block:: python

  # Import the library
  import adi

  # Create a device interface
  sdr = adi.ad9361(uri="ip:192.168.2.1")
  # Read back properties from hardware
  print(sdr.rx_hardwaregain0)


Devices that are connected over USB or are on a system with IIO devices like a ZC706 or Zedboard, should be able to automatically connect without defining a URI like:

.. code-block:: python

  # Import the library
  import adi

  # Create a device interface
  sdr = adi.Pluto()
  # Read back properties from hardware
  print(sdr.tx_rf_bandwidth)

Whoever if you have multiple USB device connected an want to pick one specifically, the set the USB URI similar to IP:

.. code-block:: python

  # Import the library
  import adi

  # Create a device interface
  sdr = adi.Pluto(uri="usb:1.24.5")
  # Read back properties from hardware
  print(sdr.tx_rf_bandwidth)

If you are not sure of the device URI you can utilize libiio command-line tools like `iio_info <https://wiki.analog.com/resources/tools-software/linux-software/libiio/iio_info>`_ and `iio_attr <https://wiki.analog.com/resources/tools-software/linux-software/libiio/iio_attr>`_.
