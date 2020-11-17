Developers
===================

.. warning::
    This section is only for developers and advanced users.

When submitting code or running tests, there are a few ways things are done in pyadi-iio.

Invoke
---------------------------
To make repetitve tasks easier, pyadi-iio utilizes pyinvoke. To see the available options (once pyinvoke is installed) run:

.. code-block:: console

        invoke --list
        Available tasks:

          build           Build python package
          builddoc        Build sphinx doc
          changelog       Print changelog from last release
          checkparts      Check for missing parts in supported_parts.md
          createrelease   Create GitHub release
          libiiopath      Search for libiio python bindings
          precommit       Run precommit checks
          setup           Install required python packages for development through pip
          test            Run pytest tests



Precommit
---------------------------
**pre-commit** is heavily relied on for keeping code in order and for eliminating certain bugs. Be sure to run these checks before submitting code. This can be run through pyinvoke or directly from the repo root as:

.. code-block:: console

        invoke precommit

.. code-block:: console

        pre-commit run --all-files

Testing
---------------------------

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


Test Functions
^^^^^^^^^^^^^^^^^^
.. toctree::
   :maxdepth: 4

   test
