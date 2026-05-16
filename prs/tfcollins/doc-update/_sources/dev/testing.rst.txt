Testing
===========================

Testing pyadi-iio requires hardware, but fortunately by default it assumes no hardware is connected unless found. It will only load specific tests for hardware it can find and skip all other tests. **pytest**, which is the framework pyadi-iio uses, can be call as following:

.. code-block:: console

        invoke test

.. code-block:: console

        python3 -m pytest <add more arguments as needed>

Test Configuration
^^^^^^^^^^^^^^^^^^

There are several advanced features of pytest that are utilized by pyadi-iio. Specifically custom markers and custom plugins.

Markers are a way of labeling tests, which can be then used to filter specific tests. Markers are provided through the `test_map.py <https://github.com/analogdevicesinc/pyadi-iio/blob/master/test/test_map.py>`_ file in the test directory. These markers are used to map FPGA based boards with daughtercards to specific tests. `Reference design folder names <https://wiki.analog.com/resources/tools-software/linux-software/embedded_arm_images>`_ from the ADI SD cards are using as the markers, which them can be passed through the *-m* flag to enabled certain tests. For example, the following would enable all tests related to *ADRV9009*, assuming the hardware is available:

.. code-block:: console

        python3 -m pytest -m zynqmp-zcu102-rev10-adrv9009


To help manage libiio contexts, filter tests based on those contexts, and map drivers to board definitions, pyadi-iio utilizes the pytest plugin `pytest-libiio <https://pypi.org/project/pytest-libiio/>`_. This must be installed before tests are run since all test implementations rely on `pytest-libiio fixtures <https://pytest-libiio.readthedocs.io/en/latest/fixtures/>`_. Generally, pyadi-iio will also use the `standard hardware map <https://pytest-libiio.readthedocs.io/en/latest/cli/#hardware-maps>`_ provided by *pytest-libiio* to map drivers to board definitions. To enable the hardware make requires the *--adi-hw-map* flag as:

.. code-block:: console

        python3 -m pytest --adi-hw-map

If you are working on a driver or board that is not in the hardware map, a custom one can be created as documentation in the `pytest-libiio CLI <https://pytest-libiio.readthedocs.io/en/latest/cli/#hardware-maps>`_.

Test Functions and Fixtures
^^^^^^^^^^^^^^^^^^^^^^^^^^^

pyadi-iio has a large set of parameterizable fixtures for testing different device specific class interfaces. See the links belows to the different test categories:

.. toctree::
   :maxdepth: 4

   test_attr
   test_dma
   test_generics
   test_jesd

Emulation
---------------------------

By leveraging `iio-emu <https://github.com/analogdevicesinc/iio-emu>`_, hardware or contexts can be emulated for testing without physical devices. However, currently this emulation does not validate attribute rates, states of drivers, or equivalent data sources. This feature should be used to test a library itself rather than hardware drivers.

**pyadi-iio** uses *iio-emu* through *pytest-libiio*, which handles loading the correct context files based on the fixtures used for each test. Essentially, when *pytest* is run, based on the fixture below, *pytest-libiio* will spawn the correct context with *iio-emu* and pass the URI of that context to the test.


.. code-block:: python

 import pytest
 import iio


 @pytest.mark.iio_hardware("pluto", False)  # Set True disables test during emulation
 def test_libiio_device(iio_uri):
     ctx = iio.Context(iio_uri)
     ...

To create and add more context files for testing with **pyadi-iio** follow `this page <https://pytest-libiio.readthedocs.io/en/latest/emulation/>`_.
