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

When running tests a single URI can be provided to the command line. Devices can be dynamically scanned for on the network, and they can be provided through a configuration file. URIs for hardware are descripted in the **uri-map** section of the pyadi_test.yaml file with the convention "<uri>: hardware1, hardware2,...". Here is an example where the URI ip:192.168.2.1 applied to tests looking for the hardware adrv9361 or fmcomms2.

.. code-block:: yaml

        uri-map:
          "ip:192.168.86.35": adrv9361, fmcomms2

This file will automatically be loaded when it is in the location **/etc/default/pyadi_test.yaml** on Linux machines. Otherwise, it can be provided to pytest through the **--test-configfilename** argument.

Available Tests
---------------------------
.. automodule:: test.conftest
   :members:
