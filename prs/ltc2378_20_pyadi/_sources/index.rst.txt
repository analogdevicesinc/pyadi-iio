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

.. image:: _static/logos/PyADI-IIO_Logo_w_600.png?://
   :class: only-dark
   :width: 700px
   :alt: PyADI-IIO Logo

.. image:: _static/logos/PyADI-IIO_Logo_600.png?://
   :class: only-light
   :width: 700px
   :alt: PyADI-IIO Logo

.. flex::
   :class: badges

   .. image:: https://github.com/analogdevicesinc/pyadi-iio/actions/workflows/test.yml/badge.svg
      :target: https://github.com/analogdevicesinc/pyadi-iio/actions
      :alt: Build Status

   .. image:: https://badge.fury.io/py/pyadi-iio.svg
      :target: https://badge.fury.io/py/pyadi-iio
      :alt: PyPI version

   .. image:: https://app.codacy.com/project/badge/Grade/200b7479f5024f6ea386350ca1049077
      :target: https://www.codacy.com/gh/analogdevicesinc/pyadi-iio/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=analogdevicesinc/pyadi-iio&amp;utm_campaign=Badge_Grade
      :alt: Codacy Badge

   .. image:: https://img.shields.io/pypi/pyversions/pyadi-iio
      :target: https://www.python.org/downloads/
      :alt: Python Version

.. flex::
   :class: badges

   .. image:: https://img.shields.io/badge/docs-GitHub%20Pages-blue.svg
      :target: http://analogdevicesinc.github.io/pyadi-iio/
      :alt: GitHub Pages

   .. image:: https://img.shields.io/badge/Support-on%20EngineerZone-blue.svg
      :target: https://ez.analog.com/sw-interface-tools/f/q-a
      :alt: EngineerZone Support

   .. image:: https://img.shields.io/badge/Wiki-on%20wiki.analog.com-blue.svg
      :target: https://wiki.analog.com/resources/tools-software/linux-software/pyadi-iio
      :alt: Analog Wiki


Requirements
==================
* `libiio <http://github.com/analogdevicesinc/libiio/>`_
* numpy
* (Optional) paramiko for JESD204 debugging
* `(Optional) libad9361 for AD9361 specific devices <http://github.com/analogdevicesinc/libad9361-iio/>`_
* `(Optional) libad9166 for the CN0511 raspberry pi based DDS  <http://github.com/analogdevicesinc/libad9166-iio/>`_
* `(Optional) libadrv9002 for ADRV9002 specific devices <http://github.com/analogdevicesinc/libadrv9002-iio/>`_

Sections
==================
.. toctree::
   :maxdepth: 1

   guides/quick
   attr/index
   guides/examples
   guides/connectivity
   buffers/index
   fpga/index
   libiio
   support
   dev/index
   devices/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
