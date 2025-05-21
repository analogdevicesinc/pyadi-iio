ad3552r
=================

The device class in this module supports multiple parts, as follows:

**ad3552r:** ad3542r, ad3552r

By default, the device_name parameter in the class constructor is the
same as the class name (e.g. "ad3552r" for the ad3552r). To use the class
with another supported model, the name must be given when instantiating
the object. For example, if working with an ad3552r with a URI of
"10.2.5.222", use the ad3552r class, but specify the device_name.

The number of individual channels is based on the device variant.

.. automodule:: adi.ad3552r
   :members:
   :undoc-members:
   :show-inheritance:


.. code-block:: python

   dev = ad3552r("", "ad3552r")

   dev.channel[0].raw = 10
   dev.channel[1].raw = 30

   data = dev.channel[0].raw
   print(data)
