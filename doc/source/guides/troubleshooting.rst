Troubleshooting
===============

This guide covers common issues encountered when using pyadi-iio and how to resolve them.

Connectivity Issues
-------------------

**No devices found / "No such device" error**

* **Check Physical Connection**: Ensure the device is powered and connected via the intended interface (USB, Ethernet, etc.).
* **Verify URI**: If using a remote connection, ensure the IP address or USB URI is correct. Use `iio_info -s` to list available devices and their URIs.
* **Firewall/Network**: For network connections (IP backend), ensure port 30431 (default IIO port) is open on the target.
* **USB Permissions (Linux)**: If a USB device is not detected without `sudo`, you likely need to install udev rules.

  .. code-block:: bash

    # Example udev rule for PlutoSDR (/etc/udev/rules.d/53-adi-plutosdr-usb.rules)
    SUBSYSTEM=="usb", ATTRS{idVendor}=="0456", ATTRS{idProduct}=="b673", MODE="666"

**"Backend not found"**

* Ensure `libiio` was compiled with the necessary backend support (e.g., `-DENABLE_USB_BACKEND=ON`, `-DENABLE_NETWORK_BACKEND=ON`).

Library and Dependency Issues
-----------------------------

**"ModuleNotFoundError: No module named 'iio'"**

* This means the `libiio` Python bindings are not in your Python path.
* If you built `libiio` from source, ensure you used `-DPYTHON_BINDINGS=ON`.
* Check if you need to set `PYTHONPATH` (common on Ubuntu/Debian):

  .. code-block:: bash

    export PYTHONPATH=$PYTHONPATH:/usr/lib/python3/dist-packages

**Version Mismatch**

* `pyadi-iio` often relies on features in newer versions of `libiio`. Ensure you are using at least `libiio` v0.21 or later.
* Check versions in Python:

  .. code-block:: python

    import iio
    import adi

    print(iio.version)
    print(adi.__version__)

Buffer and Data Issues
----------------------

**"Buffer deadline missed" or "Timeout"**

* **Sample Rate too high**: The interface (USB 2.0, Ethernet) may not be able to keep up with the data rate. Try lowering the sample rate.
* **Buffer Size**: Try increasing the buffer size (e.g., `sdr.rx_buffer_size = 2**20`).
* **Processing Delay**: Ensure your Python code is processing data fast enough. Avoid heavy computations inside the capture loop.

**Attribute Error: "device has no attribute X"**

* Verify the device driver supports the attribute. Not all drivers implement all IIO attributes.
* Check `iio_attr -d <device_name>` to see available attributes.
