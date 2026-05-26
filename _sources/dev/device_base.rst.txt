Device Base Classes
===================

For new device-specific class interfaces, pyadi-iio provides a set of common
parent classes in ``adi.device_base`` that encapsulate the boilerplate required
for device discovery, channel initialization, and buffer setup. New drivers
should use these base classes rather than re-implementing the initialization
pattern, so behavior stays consistent across the library and future changes to
the common pattern only need to be made in one place.

Available Base Classes
----------------------

All base classes live in ``adi/device_base.py``:

``device_base``
    Core mixin that handles device name validation against ``compatible_parts``,
    device index selection, and channel instance creation via
    ``_add_channel_instances``. Not used directly — combined with an RX/TX
    class below.

``rx_chan_comp`` / ``rx_chan_comp_no_buff``
    RX device with (or without) buffer support, plus complex channel object
    support. Use the ``_no_buff`` variant for devices that do not expose a
    capture buffer.

``tx_chan_comp`` / ``tx_chan_comp_no_buff``
    TX equivalents of the above.

Required Class Attributes
-------------------------

A subclass must set the following:

``compatible_parts``
    List of device names this class supports. The first entry is used as the
    default when no ``device_name`` is passed. An ``Exception`` is raised if a
    user passes a ``device_name`` that is not in this list.

``_channel_def``
    A callable (typically a channel class extending ``attribute``) that is
    instantiated once per IIO channel found on the control device. Each
    instance is assigned as an attribute on the device object, named after the
    channel id, and appended to ``self.channel``.

Optional attributes:

``_ignore_channels``
    List of channel ids to skip during ``_add_channel_instances``.

``_complex_data``
    Set to ``True`` for devices that expose paired I/Q channels.

Minimal Example
---------------

The following is a minimal RX device class that uses ``rx_chan_comp``:

.. code-block:: python

    from adi.attribute import attribute
    from adi.device_base import rx_chan_comp


    class ad4080_channel(attribute):
        """AD4080 channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def scale(self):
            return self._get_iio_attr(self.name, "scale", False)


    class ad4080(rx_chan_comp):
        """AD4080 ADC"""

        compatible_parts = ["ad4080", "ad4081", "ad4083"]
        _complex_data = False
        _channel_def = ad4080_channel

        @property
        def sampling_frequency(self):
            return self._get_iio_dev_attr("sampling_frequency", False)

No custom ``__init__`` is required; ``rx_chan_comp.__init__`` handles URI
connection, device lookup, and channel instantiation. Additional device-level
properties are added as normal.

Supporting Multiple Devices With the Same Name
----------------------------------------------

When a context exposes multiple IIO devices that share a name, pass
``device_index`` when constructing the class to select which one to bind to:

.. code-block:: python

    dev0 = ad4080(uri="ip:analog.local", device_index=0)
    dev1 = ad4080(uri="ip:analog.local", device_index=1)

When To Not Use These Classes
-----------------------------

These base classes target the common single-control-device pattern with one
optional RX or TX buffer. Devices with more complex topologies — for example,
multi-chip systems, mixed DMA paths, or non-standard channel discovery — should
continue to compose ``rx``, ``tx``, and ``context_manager`` directly.
