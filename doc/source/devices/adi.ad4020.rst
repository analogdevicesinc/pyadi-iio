ad4020
=================

Each device class in this module supports multiple parts, as follows:

**ad4020:** ad4020, ad4021, ad4022

**ad4000:** ad4000, ad4004, ad4008

**ad4001:** ad4001, ad4005

**ad4002:** ad4002, ad4006, ad4010

**ad4003:** ad4003, ad4007, ad4011

**adaq4003:** adaq4001, adaq4003

By default, the device_name parameter in the class constructor is the
same as the class name (e.g. "ad4001" for the ad4001). To use the class
with another supported model, the name must be given when instantiating
the object. For example, if working with an ad4007 with a URI of
"10.2.5.222", use the ad4003 class, but specify the device_name
parameter explicitly:

.. code-block:: bash

   import adi
   adc = adi.ad4003(uri="ip:10.2.5.222", device_name="ad4007")
   ...


.. automodule:: adi.ad4020
   :members:
   :undoc-members:
   :show-inheritance:
