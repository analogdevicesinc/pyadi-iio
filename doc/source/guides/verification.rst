Verification
=================

Install Checks
--------------

Check for libiio with the following from a command prompt or terminal:

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

When using virtual environments, ``iio`` can be imported from outside but not from inside by default because virtual environments do not inherit system packages.
Either install the python environment with ``--system-site-packages`` to inherit all system packages or set ``PYTHONPATH`` environment variable to inherit from some paths.
