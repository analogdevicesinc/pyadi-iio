Quick Start
===============

Before installing pyadi-iio make sure you have `libiio <https://github.com/analogdevicesinc/libiio>`_ and `its python bindings <https://github.com/analogdevicesinc/libiio/blob/main/bindings/python/README.md>`_ installed. Since libiio v0.21, the libiio python bindings have been available on pypi and conda. The conda package includes the built library but the pypi install will require that it is installed beforehand. If you install pyadi-iio directly from pypi or conda they will automatically install the python bindings for libiio (pylibiio).

.. note::

  libiio (the C library) does not currently have a pip installer, but releases are available on `GitHub <https://github.com/analogdevicesinc/libiio/releases>`_ along with the `source <https://github.com/analogdevicesinc/libiio>`_.
  For releases v0.19+ of libiio, when building from source the -DPYTHON_BINDINGS=ON flag is required

pyadi-iio can by installed from pip

.. code-block:: bash

  (sudo) pip install pyadi-iio

or by grabbing the source directly for a more up to date version

.. code-block:: bash

  git clone https://github.com/analogdevicesinc/pyadi-iio.git
  cd pyadi-iio
  (sudo) pip install .

To install the optional dependencies for JESD debugging and control

.. code-block:: bash

  (sudo) pip install pyadi-iio[jesd]

Note that this is only needed for the ADRV9009-ZU11EG multi-SOM configuration.

.. note::

  On Linux the libiio python bindings are sometimes installed in locations not on path when building from source. On Ubuntu this is a common fix

  .. code-block:: bash

    export PYTHONPATH=$PYTHONPATH:/usr/lib/python{PYTHON VERSION}/site-packages

  Python packages under the exported path are also inherited by virtual environments.

Using Virtual Environments
--------------------------

It is recommended to use virtual environments when installing pyadi-iio. This will prevent any conflicts with other python packages that may be installed on your system. Newer versions of such Linux distributions, like Debian, do not allow the installation of global packages either. Therefore, if a package is not within their package managers you must your virtual environments. To create a virtual environment run:

.. code-block:: bash

  python3 -m venv /path/to/new/virtual/environment

.. note::

  To inherit system packages, such as libiio python binding, either set ``PYTHONPATH`` described earlier, or use ``--system-site-packages`` if ``iio`` is already on path.

To activate the virtual environment run:

.. code-block:: bash

  source /path/to/new/virtual/environment/bin/activate

To deactivate the virtual environment run:

.. code-block:: bash

  deactivate

.. note::

   For development work on pyadi-iio itself (not just using it), run
   ``make dev`` from the repo root. It creates ``venv/``, activates it,
   and installs the dev requirements in one step.

Once the virtual environment is activated, you can install pyadi-iio as normal with pip.

Conda Install
-------------

For those who use the Anaconda or Conda environments, it is possible to install libiio from within those environments with the provided package managers. To install libiio, pylibiio, and pyadi-iio run:

.. code-block:: bash

   conda install -c conda-forge pyadi-iio

Install Checks
--------------

Check for libiio with the following from a command prompt or terminal:

.. code-block:: bash

  $ python3
  Python 3.10.12 (main, Sep 12 2023, 09:00:00) [GCC 11.4.0] on linux
  Type "help", "copyright", "credits" or "license" for more information.
  >>> import iio
  >>> iio.version
  (1, 0, 'release')

If that worked, check that pyadi-iio is there:

.. code-block:: bash

  $ python3
  Python 3.10.12 (main, Sep 12 2023, 09:00:00) [GCC 11.4.0] on linux
  Type "help", "copyright", "credits" or "license" for more information.
  >>> import adi
  >>> adi.__version__
  '0.0.21'
  >>> adi.name
  'Analog Devices Hardware Interfaces'

pyadi-iio supports libiio v0.x and v1.x; the version above is illustrative
and the library handles both transparently through ``adi.compat``.

When using virtual environments, ``iio`` can be imported from outside but not from inside by default because virtual environments do not inherit system packages.
Either install the python environment with ``--system-site-packages`` to inherit all system packages or set ``PYTHONPATH`` environment variable to inherit from some paths.

What next
---------

* :doc:`Concepts <../concepts>` — the rx/tx/attribute/URI mental model.
* :doc:`Supported devices <../devices/index>` — find your part by family.
* :doc:`Troubleshooting <troubleshooting>` — common errors during install or first connection.
