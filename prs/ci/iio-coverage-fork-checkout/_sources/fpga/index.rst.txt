FPGA Features
===================

Direct Digital Synthesizers
---------------------------

For FPGA based systems ADI reference designs include direct digital synthesizers (DDS) which can generate tones with arbitrary phase, frequency, and amplitude. For each individual DAC channel there are two DDSs which can have a unique phase, frequency, and phase. To configure the DDSs there are a number of methods and properties available depending on the complexity of the configuration.

For the most basic or easiest configuration options use the methods **dds_single_tone** and **dds_dual_tone** which generate a one tone or two tones respectively on a specific channel.

.. code-block:: python

 import adi

 sdr = adi.ad9361()
 # Generate a single complex tone
 dds_freq_hz = 10000
 dds_scale = 0.9
 # Enable all DDSs
 sdr.dds_single_tone(dds_freq_hz, dds_scale)


To configure DDSs individually a list of scales can be passed to the properties **dds_scales**, **dds_frequencies**, and **dds_phases**.

.. code-block:: python

 import adi

 sdr = adi.ad9361()
 n = len(sdr.dds_scales)
 # Enable all DDSs
 sdr.dds_enabled = [True] * n
 # Set all DDSs to same frequency, scale, and phase
 dds_freq_hz = 10000
 sdr.dds_phases = [0] * n
 sdr.dds_frequencies = [dds_freq_hz] * n
 sdr.dds_scales = [0.9] * n

DDS Methods
---------------------------
.. automodule:: adi.dds
   :members:


DMA Synchronization
---------------------------

In certain HDL reference designs it is possible to synchronize transfers between the transmit and receive data paths. This is useful for applications such as radar processing, communications, instrumentation, and general testing.

This works by leveraging special control signals inside the HDL design to trigger receive captures from transmitted buffers. These are controlled through the **sync_start** class, which provide explicit control over when data is transmitted or released from the DMA in the FPGA fabric. This transmit or trigger will in turn allow data into the receive DMA at this moment in time. The exact methods and their sequence are described in the flowchart below.

.. mermaid:: dma_sync.mmd


A full example that leverages this control is `ad9081_sync_start_example.py <https://github.com/analogdevicesinc/pyadi-iio/blob/master/examples/ad9081_sync_start_example.py>`_.

Sync_Start Methods
---------------------------
.. automodule:: adi.sync_start
   :members:
