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

.. raw:: html

    <center>
    <div style="width:70%;">
    <div id="indexlogo" class="only-light">
    <img src="_static/logos/PyADI-IIO_Logo_600.png" alt="PyADI-IIO Logo" />
    </div>
    <div id="indexlogo" class="only-dark">
    <img src="_static/logos/PyADI-IIO_Logo_w_600.png" alt="PyADI-IIO Logo" />
    </div>
    </div>
    </center>

.. raw:: html

    <div align="center" id="badges">
    <a href="https://github.com/analogdevicesinc/pyadi-iio/actions">
    <img src="https://github.com/analogdevicesinc/pyadi-iio/actions/workflows/test.yml/badge.svg" alt="Build Status">
    </a>

    <a href="https://badge.fury.io/py/pyadi-iio">
    <img src="https://badge.fury.io/py/pyadi-iio.svg" alt="PyPI version">
    </a>

    <a href="https://www.codacy.com/gh/analogdevicesinc/pyadi-iio/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=analogdevicesinc/pyadi-iio&amp;utm_campaign=Badge_Grade">
    <img src="https://app.codacy.com/project/badge/Grade/200b7479f5024f6ea386350ca1049077" alt="Codacy Badge">
    </a>

    <a href="https://www.python.org/download/releases/3.6.0/">
    <img src="https://img.shields.io/badge/python-3.6+-blue.svg" alt="Python Version">
    </a>
    </div>

    <div align="center" id="badges">
    <a href="http://analogdevicesinc.github.io/pyadi-iio/">
    <img alt="GitHub Pages" src="https://img.shields.io/badge/docs-GitHub%20Pages-blue.svg">
    </a>

    <a href="https://ez.analog.com/sw-interface-tools/f/q-a">
    <img alt="EngineerZone" src="https://img.shields.io/badge/Support-on%20EngineerZone-blue.svg">
    </a>

    <a href="https://wiki.analog.com/resources/tools-software/linux-software/pyadi-iio">
    <img alt="Analog Wiki" src="https://img.shields.io/badge/Wiki-on%20wiki.analog.com-blue.svg">
    </a>
    </div>


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
