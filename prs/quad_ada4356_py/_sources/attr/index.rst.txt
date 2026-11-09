Attributes
==================

To simplify hardware configuration through different IIO drivers, basic class properties are exposed at the top-level of each device specific class. These properties abstract away the need to know a specific channel name, attribute type, source device name, and other details required in the libIIO API. Instead properties have easy to understand names, documentation, and error handling to help manage interfacing with different hardware. Property data can be read and written as follows from a given device interface class:

.. code-block:: python

 import adi

 lidar = adi.fmclidar1()
 # Read current pulse width
 print(lidar.laser_pulse_width)
 # Change laser frequency to 1 MHz
 lidar.laser_frequency = 1000000

If more detail is required about a specific property it can be directly inspected in the class definitions documnentation or in python itself through the help methods:


.. literalinclude:: pluto_help.cli
  :language: none

For complete documentation about class properties reference the :doc:`supported devices</devices/index>` classes.
