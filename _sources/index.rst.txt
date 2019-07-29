.. Analog Devices Hardware Python Interfaces documentation master file, created by
   sphinx-quickstart on Wed Jun 26 11:46:55 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Analog Devices Hardware Python Interfaces
=====================================================================

This module provides a convenient way to access and control ADI hardware from Python through existing IIO drivers.

Requirements

* `libiio <http://github.com/analogdevicesinc/libiio/>`_
* `libad9361 for AD9361 specific devices <http://github.com/analogdevicesinc/libad9361/>`_

.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Devices
===================
.. automodule:: adi
   :noindex:
   :members:

AD936X Family
===================
.. automodule:: adi.ad9361
   :members:

AD9371
===================
.. automodule:: adi.ad9371
   :members:

FPGA Features
===================
.. automodule:: adi.dds
   :members:

Common
===================
.. automodule:: adi.rx_tx
   :members:

.. automodule:: adi.context_manager
   :members:

.. automodule:: adi.attribute
   :members:
