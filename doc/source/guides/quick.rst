Quick Start
===============

Before installing pyadi-iio make sure you have `libiio <https://github.com/analogdevicesinc/libiio>`_ and `its python bindings <https://github.com/analogdevicesinc/libiio/blob/master/bindings/python/iio.py>`_ installed.

.. note::

  libiio does not currently have a pip installer, but releases are available on `GitHub <https://github.com/analogdevicesinc/libiio/releases>`_ along with the `source <https://github.com/analogdevicesinc/libiio>`_.
  For releases v0.19+ of libiio, when building from source the -DPYTHON_BINDINGS=ON flag is required

pyadi-iio can by installed from pip

.. code-block:: bash

  (sudo) pip install pyadi-iio

or by grabbing the source directly

.. code-block:: bash

  git clone https://github.com/analogdevicesinc/pyadi-iio.git
  cd pyadi-iio
  (sudo) python3 setup.py install

.. note::

  On Linux the libiio python bindings are sometimes installed in locations not on path. On Ubuntu this is a common fix

  .. code-block:: bash

    export PYTHONPATH=$PYTHONPATH:/usr/lib/python{PYTHON VERSION}/site-packages

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
