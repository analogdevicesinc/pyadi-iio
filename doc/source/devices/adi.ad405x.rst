ad405x
================

.. autoclass:: adi.ad405x.ad405x
   :members:
   :undoc-members:
   :show-inheritance:


------------------

Component Channels
------------------

This devices support component channels that are available as objects in the **channels** attribute.

.. autoclass:: adi.ad405x.rx_buffered_channel
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:


Examples channel usage:

.. code:: python

   import adi

   dev = adi.ad405x(uri="ip:analog")
   data = dev.channels[0].raw
