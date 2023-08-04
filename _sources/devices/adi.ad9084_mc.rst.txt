ad9084\_mc
=====================

The multi-chip python interface for ad9084 is scalable to any number of ad9084s within a single libIIO context. It will automatically determine the correct main driver, manage the CDDC/FDDC/CDUC/FDUC arrangement uniquely for each chip, and DMA/DDS IP. However, the interface a bit unique with **pyadi-iio** since it is almost identical to the single ad9084 class but it exposes properties in a slightly different way.

When using **adi.ad9084**, properties are generally simple types like strings, ints, floats, or lists of these types. For example, when reading back the **rx_channel_nco_frequencies** you would observe something like:

.. code-block:: bash

 >>> import adi
 >>> dev = adi.ad9084()
 >>> dev.rx_channel_nco_frequencies
 [0, 0, 0, 0]


For the case of a multi-chip configuration a dict is returned with an entry for each MxFE chip:

.. code-block:: bash

 >>> import adi
 >>> dev = adi.ad9084_mc()
 >>> dev.rx_channel_nco_frequencies
 {'axi-ad9084-rx1': [0, 0, 0, 0],
  'axi-ad9084-rx2': [0, 0, 0, 0],
  'axi-ad9084-rx3': [0, 0, 0, 0],
  'axi-ad9084-rx-hpc': [0, 0, 0, 0]}

The same dict can be passed back to the property when writing, which will contain all or a subset of the chips to be address if desired. Alternatively, a list can be passed with only the values themselves if a dict does not want to be used. This is useful when performing array based DSP were data is approach in aggregate. However, in this case entries must be provided for all chip, not just a subset. Otherwise an error is returned.

When passing a list only, the chips are address based on the attribute **_default_ctrl_names**. Below is an example of this API:

.. code-block:: bash

 >>> import adi
 >>> dev = adi.ad9084_mc()
 >>> dev.rx_channel_nco_frequencies
 {'axi-ad9084-rx1': [0, 0, 0, 0],
  'axi-ad9084-rx2': [0, 0, 0, 0],
  'axi-ad9084-rx3': [0, 0, 0, 0],
  'axi-ad9084-rx-hpc': [0, 0, 0, 0]}
 >>> dev.rx_channel_nco_frequencies = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
 >>> dev.rx_channel_nco_frequencies
 {'axi-ad9084-rx1': [0, 1, 2, 3],
  'axi-ad9084-rx2': [4, 5, 6, 7],
  'axi-ad9084-rx3': [8, 9, 10, 11],
  'axi-ad9084-rx-hpc': [12, 13, 14, 15]}


.. automodule:: adi.ad9084_mc
   :members:
   :undoc-members:
   :show-inheritance:
