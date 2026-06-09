Architecture
============

This section describes the internal architecture of **pyadi-iio** and its relationship with the underlying system.

System Stack
------------

**pyadi-iio** is a high-level abstraction layer. It sits on top of several other components:

1.  **Hardware (FPGA/ASIC)**: The actual Analog Devices silicon and associated HDL.
2.  **Linux Kernel Drivers**: Industrial I/O (IIO) drivers in the kernel manage the hardware and provide a standard interface via `sysfs` and character devices.
3.  **libiio (C Library)**: A cross-platform library that provides an easy-to-use API for interfacing with IIO devices locally or over a network.
4.  **pylibiio (Python Bindings)**: The low-level Python wrapper around `libiio`.
5.  **pyadi-iio**: The top-level library (this one) which provides device-specific classes (e.g., `adi.ad9361`), easy-to-use properties, and NumPy integration.

.. code-block:: text

    +------------------------------------------+
    |               Application                |
    +------------------------------------------+
    |               pyadi-iio                  |
    +------------------------------------------+
    |         pylibiio (iio.py)                |
    +------------------------------------------+
    |          libiio (C Library)              |
    +------------------------------------------+
           |                 |                 |
    +--------------+  +--------------+  +--------------+
    | Local Driver |  |  Network/IP  |  |  USB/Serial  |
    +--------------+  +--------------+  +--------------+

Design Principles
-----------------

*   **Attribute Mapping**: Kernel IIO attributes are mapped to Python properties. For example, reading `sdr.rx_lo` might map to reading a `voltage0/out_altvoltage0_RX_LO_frequency` attribute in sysfs.
*   **Abstraction**: Complexity like buffer management, channel enabling, and device discovery is handled automatically during object instantiation.
*   **NumPy Integration**: All data buffers are converted to NumPy arrays for immediate use in scientific computing.
*   **Uniformity**: Devices follow a similar API pattern (e.g., `rx()`, `tx()`, `rx_buffer_size`) to make switching between hardware easy.
