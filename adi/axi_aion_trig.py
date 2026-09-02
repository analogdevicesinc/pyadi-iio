# Copyright (C) 2025-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


from adi.attribute import attribute
from adi.context_manager import context_manager


class axi_aion_trig(context_manager, attribute):
    """axi_aion_trig IIO Device Interface

    This class provides an interface to the 'axi_aion_trig' IIO device, allowing
    control and monitoring of its voltage channels and associated attributes.

    Parameters
    ----------
    uri : str, optional
        URI of the IIO context to connect to. Defaults to an empty string.

    Attributes (per voltage channel)
    --------------------------------
    For each voltage channel (e.g., voltage0, voltage1, ...), the following
    properties are dynamically created:

    - trig{N}_en : bool
        Enable or disable the trigger for channel N.
    - trig{N}_phase : int
        Phase setting for channel N.
    - trig{N}_status : int
        Status of the trigger for channel N.
    - trig{N}_frequency : int
        Frequency setting for channel N.
    - trig{N}_internal_bsync_enable : bool
        Enable or disable internal bsync for channel N.
    - trig{N}_output_enable : bool
        Enable or disable output for channel N.
    - trig{N}_trigger_now : bool
        Trigger an immediate event on channel N.
    - trig{N}_trigger_select_gpio_enable : bool
        Enable or disable GPIO selection for trigger on channel N.

    Raises
    ------
    Exception
        If the 'axi_aion_trig' device is not found in the IIO context.

    Examples
    --------
    >>> trig = axi_aion_trig("ip:192.168.1.100")
    >>> trig.trig0_en = True
    >>> print(trig.trig0_status)
    """

    _device_name = "axi_aion_trig"

    def __init__(self, uri=""):
        context_manager.__init__(self, uri, self._device_name)
        self._ctrl = self._ctx.find_device(self._device_name)
        if not self._ctrl:
            raise Exception("axi_aion_trig device not found")
        self._add_channel_properties()

    def _make_channel_property(self, channel, attr):
        def getter(self):
            return self._get_iio_attr(channel, attr, False, self._ctrl)

        def setter(self, value):
            self._set_iio_attr(channel, attr, False, value, self._ctrl)

        return property(getter, setter)

    # Attributes for in_voltage channels and device properties
    _attrs = [
        "en",
        "phase",
        "status",
        "frequency",
        "internal_bsync_enable",
        "output_enable",
        "trigger_now",
        "trigger_select_gpio_enable",
    ]

    def _add_channel_properties(self):
        for ch in self._ctrl.channels:
            if not ch._id.startswith("voltage"):
                continue
            name = ch._id.replace("voltage", "")

            for attr in self._attrs:
                prop_name = f"trig{name}_{attr}"
                setattr(
                    self.__class__, prop_name, self._make_channel_property(ch._id, attr)
                )
