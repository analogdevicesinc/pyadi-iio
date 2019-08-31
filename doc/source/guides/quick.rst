Quick Start
===============

Before installing pyadi-iio make sure you have `libiio <https://github.com/analogdevicesinc/libiio>`_ and `its python bindings <https://github.com/analogdevicesinc/libiio/blob/master/bindings/python/iio.py>`_ installed.

.. note::

  libiio does not currently have a pip installer releases are available on `GitHub <https://github.com/analogdevicesinc/libiio/releases>`_ along with the `source <https://github.com/analogdevicesinc/libiio>`_.

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

    export PYTHONPATH=$PYTHONPATH:/usr/lib/python2.7/site-packages
