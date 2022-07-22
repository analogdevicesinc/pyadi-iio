.. Analog Devices Hardware Python Interfaces documentation master file, created by
   sphinx-quickstart on Wed Jun 26 11:46:55 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Analog Devices Hardware Python Interfaces
=====================================================================

**pyadi-iio** is a python abstraction module for ADI hardware with IIO drivers to make them easier to use. The libIIO interface although extremely flexible can be cumbersome to use due to the amount of boilerplate code required for even simple examples, especially when interfacing with buffers. This module has custom interfaces classes for specific parts and development systems which can generally make them easier to understand and use. To get up and running with a device can be as simple as a few lines of code:

.. code-block:: python

 import adi

 # Create device from specific uri address
 sdr = adi.ad9361(uri="ip:192.168.2.1")
 # Get data from transceiver
 data = sdr.rx()

.. figure:: ../../images/PyADI-IIO_Logo_72.png

.. image:: https://secure.travis-ci.org/analogdevicesinc/pyadi-iio.png
    :target: http://travis-ci.org/analogdevicesinc/pyadi-iio
.. image:: https://badge.fury.io/py/pyadi-iio.svg
    :target: https://badge.fury.io/py/pyadi-iio
.. image:: https://app.codacy.com/project/badge/Grade/200b7479f5024f6ea386350ca1049077
    :target: https://www.codacy.com/gh/analogdevicesinc/pyadi-iio/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=analogdevicesinc/pyadi-iio&amp;utm_campaign=Badge_Grade

Requirements
==================
* `libiio <http://github.com/analogdevicesinc/libiio/>`_
* `(Optional) libad9361 for AD9361 specific devices <http://github.com/analogdevicesinc/libad9361/>`_

Sections
==================
.. toctree::
   :maxdepth: 2

   guides/quick
   attr/index
   guides/examples
   guides/connectivity
   devices/index
   buffers/index
   fpga/index
   dev/index
   libiio
   support

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
