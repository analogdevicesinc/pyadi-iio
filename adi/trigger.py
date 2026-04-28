# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import iio

from adi.attribute import attribute
from adi.context_manager import context_manager


class hrtimer_trig(context_manager, attribute):
    """High-Resolution Timer Trigger

    This class provides an interface for controlling an IIO hrtimer trigger.
    The trigger must be created first:
    * Ensure the iio-trig-hrtimer kernel module is loaded or built-in into the kernel
    * Ensure configfs is mounted at /sys/kernel/config
    * Create the a new trigger with:
        * mkdir /config/iio/triggers/hrtimer/mytrig
    * Restart iiod service if relying on a remote iio context
    """

    def __init__(self, uri="", trig_name="trigger0"):
        """Initialize the hrtimer trigger

        :param uri:
            URI string for connecting to the hardware
        :param trig_name:
            Trigger id or name. Default: trigger0
        """
        context_manager.__init__(self, uri)

        self._ctrl = self._ctx.find_device(trig_name)  # type: iio.Trigger
        if not self._ctrl:
            raise Exception(f"Trigger '{trig_name}' not found")

        if not isinstance(self._ctrl, iio.Trigger):
            raise ValueError(f"'{self._ctrl.name}' is not an IIO Trigger")

        if "sampling_frequency" not in self._ctrl.attrs:
            raise Exception(
                f"Trigger '{self._ctrl.name}' is not a hrtimer trigger"
            )

    @property
    def sampling_frequency(self):
        """Get/Set sampling frequency of the trigger"""
        return self._get_iio_dev_attr("sampling_frequency", self._ctrl)

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        self._set_iio_dev_attr("sampling_frequency", value, self._ctrl)

    @property
    def name(self):
        """Get the name of the trigger"""
        return self._ctrl.name


class sysfs_trig(context_manager, attribute):
    """Sysfs Trigger

    This class provides an interface for controlling an IIO sysfs trigger.
    The trigger must be created first:
    * Ensure the iio-trig-sysfs kernel module is loaded or built-in into the kernel
    * Create the a new trigger with:
        * echo 0 > /sys/bus/iio/devices/iio_sysfs_trigger/add_trigger
    * Restart iiod service if relying on a remote iio context
    """

    def __init__(self, uri="", trig_name="sysfstrig0"):
        """Initialize the sysfs trigger

        :param uri:
            URI string for connecting to the hardware
        :param trig_id:
            Trigger id or name. Default: sysfstrig0
        """
        context_manager.__init__(self, uri)

        self._ctrl = self._ctx.find_device(trig_name)
        if not self._ctrl:
            raise Exception(f"Trigger '{trig_name}' not found")

        if not isinstance(self._ctrl, iio.Trigger):
            raise ValueError(f"'{self._ctrl.name}' is not an IIO Trigger")

        if (
            not self._ctrl.name.startswith("sysfstrig")
            or "trigger_now" not in self._ctrl.attrs
        ):
            raise Exception(
                f"Trigger '{self._ctrl.name}' is not a sysfs trigger"
            )

    @property
    def name(self):
        """Get the name of the trigger"""
        return self._ctrl.name

    def trigger_now(self):
        """Trigger an immediate event"""
        self._set_iio_dev_attr("trigger_now", 1, self._ctrl)
