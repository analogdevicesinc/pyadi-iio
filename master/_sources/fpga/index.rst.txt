FPGA Features
===================

Direct Digital Synthesizers
---------------------------

For FPGA based systems ADI reference designs include direct digital synthesizer (DDS) which can generate tones with arbitrary phase, frequency, and amplitude. For each individual DAC channel there are two DDSs which can have a unique phase, frequency, and phase. To configure the DDSs there are a number of methods and properties available depending on the complexity of the configuration.

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

Methods
---------------------------
.. automodule:: adi.dds
   :members:
