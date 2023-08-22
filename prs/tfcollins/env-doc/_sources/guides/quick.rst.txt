Quick Start
===============

Before installing pyadi-iio make sure you have `libiio <https://github.com/analogdevicesinc/libiio>`_ and `its python bindings <https://github.com/analogdevicesinc/libiio/blob/master/bindings/python/iio.py>`_ installed. Since libiio v0.21, the libiio python bindings have been available on pypi and conda. The conda package includes the built library but the pypi install will require that it is installed beforehand. If you install pyadi-iio directly from pypi or conda they will automatically install the python bindings for libiio (pylibiio).

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

Using Virtual Environments
--------------------------

It is recommended to use virtual environments when installing pyadi-iio. This will prevent any conflicts with other python packages that may be installed on your system. Newer versions of such Linux distributions, like Debian, do not allow the installation of global packages either. Therefore, if a package is not within their package managers you must your virtual environments. To create a virtual environment run:

.. code-block:: bash

  python3 -m venv /path/to/new/virtual/environment

To activate the virtual environment run:

.. code-block:: bash

  source /path/to/new/virtual/environment/bin/activate

To deactivate the virtual environment run:

.. code-block:: bash

  deactivate

Once the virtual environment is activated, you can install pyadi-iio as normal with pip.

Here is a full example of a virtual environment setup and install of pyadi-iio:

.. code-block:: bash

  dave@hal:~$ python3 -m venv /home/dave/venv/pyadi-iio
  dave@hal:~$ source /home/dave/venv/pyadi-iio/bin/activate
  (pyadi-iio) dave@hal:~$ pip install pyadi-iio
  Collecting pyadi-iio
    Downloading ...


Conda Install
-------------

For those who use the Anaconda or Conda environments, it is possible to install libiio from within those environments with the provided package managers. To install libiio, pylibiio, and pyadi-iio run:

.. code-block:: bash

   conda install -c conda-forge pyadi-iio

Install Checks
--------------

For check for libiio with the following from a command prompt or terminal:

.. code-block:: bash

  dave@hal:~$ python3
  Python 3.6.8 (default, Jan 14 2019, 11:02:34)
  [GCC 8.0.1 20180414 (experimental) [trunk revision 259383]] on linux
  Type "help", "copyright", "credits" or "license" for more information.
  >>> import iio
  >>> iio.version
  (0, 18, 'eec5616')


If that worked, try the follow to see if pyadi-iio is there:

.. code-block:: bash

  dave@hal:~$ python3
  Python 3.6.8 (default, Jan 14 2019, 11:02:34)
  [GCC 8.0.1 20180414 (experimental) [trunk revision 259383]] on linux
  Type "help", "copyright", "credits" or "license" for more information.
  >>> import adi
  >>> adi.__version__
  '0.0.5'
  >>> adi.name
  'Analog Devices Hardware Interfaces'
