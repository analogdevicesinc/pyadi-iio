ad5592r
=================

.. automodule:: adi.ad5592r
   :members:
   :undoc-members:
   :show-inheritance:


The number of individual channels is based on the hardware configuration of the device. The are individually accessed as properties like so:

.. code-block:: python

      dev = adi.ad5592r(uri="ip:analog")
      dev.dac_0.raw = 10
      dev.dac_1.raw = 30
      data = dev.adc_0.raw
      print(data)
      temp_c = (dev.temp_0.raw + dev.temp_0.offset) * dev.temp_0.scale
      print(temp_c)
