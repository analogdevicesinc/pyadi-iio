Contributing
===========================

New Hardware Requirements
^^^^^^^^^^^^^^^^^^^^^^^^^

In order to maintain pyadi-iio, for all new drivers the development team will require emulation contexts to be submitted alongside the new class interfaces. This is to ensure that the new drivers are tested and maintained. Emulation contexts can be created using `xml_gen <https://pytest-libiio.readthedocs.io/en/latest/emulation/#adding-device-support>`_. CI will automatically validate that all hardware interfaces have emulation contexts and prevent merging if they are missing.

.. note::
        Note that xml_gen is not the same as iio_genxml, as iio_genxml does not capture default values of properties required for emulation.

New Device Class Interfaces
---------------------------

New device-specific classes should build on the common base classes in
``adi.device_base`` rather than reimplementing the device discovery and channel
initialization pattern. See:

.. toctree::
   :maxdepth: 2

   device_base
