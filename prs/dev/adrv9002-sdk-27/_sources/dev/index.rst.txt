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



New Hardware Requirements
^^^^^^^^^^^^^^^^^^^^^^^^^

In order to maintain pyadi-iio, for all new drivers the development team will require emulation contexts to be submitted alongside the new class interfaces. This is to ensure that the new drivers are tested and maintained. Emulation contexts can be created using `xml_gen <https://pytest-libiio.readthedocs.io/en/latest/emulation/#adding-device-support>`_. CI will automatically validate that all hardware interfaces have emulation contexts and prevent merging if they are missing.

.. note::
        Note that xml_gen is not the same as iio_genxml, as iio_genxml does not capture default values of properties required for emulation.


Test Functions and Fixtures
^^^^^^^^^^^^^^^^^^^^^^^^^^^

pyadi-iio has a large set of parameterizable fixtures for testing different device specific class interfaces. See the links belows to the different test categories:

.. toctree::
   :maxdepth: 4

   test_attr
   test_dma
   test_generics


Set Up Isolated Environment
---------------------------

This section will discuss a method to do isolated development with the correct package versions. The main purpose here is to eliminate any discrepancies that can arise (especially with the linting tools) when running precommit and other checks. This is also useful to not pollute your local global packages. The approach here relies upon leveraging **pyenv** and **pipenv** together.


Install pyenv
^^^^^^^^^^^^^^^^^

**pyenv** is a handy tool for installing different and isolated versions of python on your system. Since distributions can ship with rather random versions of python, pyenv can help us install exactly the versions we want. The quick way to install pyenv is with their bash script:


.. code-block:: bash

 curl https://pyenv.run | bash


Add to your path and shell startup script (.bashrc, .zshrc, ...)

.. code-block:: bash

 export PATH="/home/<username>/.pyenv/bin:$PATH
 eval "$(pyenv init -)"
 eval "$(pyenv virtualenv-init -)"


Install the desired python version

.. code-block:: bash

  pyenv install 3.6.9


Create isolated install with pipenv
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Get the repo, set python version, and setup env

.. code-block:: bash

  pip3 install -U pipenv
  pyenv local 3.6.9
  git clone git@github.com:analogdevicesinc/pyadi-iio.git
  pipenv install
  pipenv shell
  pipenv install -r requirements.txt
  pipenv install -r requirements_dev.txt


Now at this point we have all the necessary development packages to start working. If you close the current shell you will lose the environment. To return to it, go to the project folder and run:

.. code-block:: bash

  cd <project folder>
  pyenv local 3.6.9
  pipenv shell

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
