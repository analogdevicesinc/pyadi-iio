Performance Optimization
========================

Achieving maximum throughput and reliability with pyadi-iio requires understanding how buffers and data transfers work.

Buffer Management
-----------------

**Buffer Size**

The `rx_buffer_size` attribute (defaulting to 1024 or similar depending on the device) controls how many samples are collected per transfer.

* **Small Buffers**: Low latency, but higher CPU overhead due to frequent interrupts/system calls. Prone to "buffer overflow" or missed samples at high rates.
* **Large Buffers**: High throughput, lower overhead, but increased latency.

.. code-block:: python

    sdr = adi.ad9361()
    sdr.rx_buffer_size = 2 ** 18  # Increase for high-speed streaming

**Cyclic Buffers**

For transmit (TX), use `tx_cyclic_buffer = True` if you want to repeat the same data indefinitely without re-uploading it. This significantly reduces CPU and bus usage.

.. code-block:: python

    sdr.tx_cyclic_buffer = True
    sdr.tx(my_waveform)  # Uploads once and repeats hardware-side

Data Handling
-------------

**NumPy Integration**

pyadi-iio returns data as NumPy arrays. To maintain performance:
* Avoid frequent conversions between types.
* Use in-place operations where possible.
* Pre-allocate arrays if you are doing manual buffering.

**Real-Time Considerations**

Python is not a real-time language. For high-speed continuous streaming:
* **Multiprocessing/Threading**: Use a separate thread or process for data acquisition to avoid UI or processing blocks.
* **Queueing**: Use `multiprocessing.Queue` to pass data between an acquisition process and a processing process.

Throughput Limits
-----------------

Throughput is often limited by the physical interface:
* **USB 2.0**: ~20-30 MB/s (practical limit).
* **1G Ethernet**: ~100-110 MB/s (practical limit).
* **USB 3.0 / PCIe**: Much higher, usually limited by CPU processing or memory bandwidth.

If you hit these limits, consider:
* **Decimation/Interpolation**: Reduce the sample rate at the hardware level if the full bandwidth isn't needed.
* **Complex vs Real**: Complex data (I/Q) takes twice as much bandwidth as real data.
