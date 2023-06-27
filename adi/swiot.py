from collections import OrderedDict

import numpy as np
from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx

class swiot(rx, context_manager, attribute):

	_device_name = "swiot"

	def __init__(self, uri=""):
                context_manager.__init__(self, uri, self._device_name)
                self._ctrl = self._ctx.find_device("swiot")

                if not self._ctrl:
                        raise Exception("No swiot device found")

                _channels = []
                for ch in self._ctrl.channels:
                        self._rx_channel_names.append(ch.id)
                        _channels.append((ch.id, self._channel(self._ctrl, ch.id)))
                self.channel = OrderedDict(_channels)

	@property
	def ch0_function(self):	
		return self._get_iio_dev_attr_str("ch0_function")

	@ch0_function.setter
	def ch0_function(self, value):
		return self._set_iio_dev_attr_str("ch0_function", value)

	@property
	def ch0_device(self):	
		return self._get_iio_dev_attr_str("ch0_device")

	@ch0_device.setter
	def ch0_device(self, value):
		return self._set_iio_dev_attr_str("ch0_device", value)

	@property
	def ch0_enable(self):
		return self._get_iio_dev_attr_str("ch0_enable")

	@ch0_enable.setter
	def ch0_enable(self, value):
		return self._set_iio_dev_attr_str("ch0_enable", value)

	@property
	def ch1_function(self):	
		return self._get_iio_dev_attr_str("ch1_function")

	@ch1_function.setter
	def ch1_function(self, value):
		return self._set_iio_dev_attr_str("ch1_function", value)

	@property
	def ch1_device(self):	
		return self._get_iio_dev_attr_str("ch1_device")

	@ch1_device.setter
	def ch1_device(self, value):
		return self._set_iio_dev_attr_str("ch1_device", value)

	@property
	def ch1_enable(self):
		return self._get_iio_dev_attr_str("ch1_enable")

	@ch1_enable.setter
	def ch1_enable(self, value):
		return self._set_iio_dev_attr_str("ch1_enable", value)

	@property
	def ch2_function(self):	
		return self._get_iio_dev_attr_str("ch2_function")

	@ch2_function.setter
	def ch2_function(self, value):
		return self._set_iio_dev_attr_str("ch2_function", value)

	@property
	def ch2_device(self):	
		return self._get_iio_dev_attr_str("ch2_device")

	@ch2_device.setter
	def ch2_device(self, value):
		return self._set_iio_dev_attr_str("ch2_device", value)

	@property
	def ch2_enable(self):
		return self._get_iio_dev_attr_str("ch2_enable")

	@ch2_enable.setter
	def ch2_enable(self, value):
		return self._set_iio_dev_attr_str("ch2_enable", value)

	@property
	def ch3_function(self):	
		return self._get_iio_dev_attr_str("ch3_function")

	@ch3_function.setter
	def ch3_function(self, value):
		return self._set_iio_dev_attr_str("ch3_function", value)

	@property
	def ch3_device(self):	
		return self._get_iio_dev_attr_str("ch3_device")

	@ch3_device.setter
	def ch3_device(self, value):
		return self._set_iio_dev_attr_str("ch3_device", value)

	@property
	def ch3_enable(self):
		return self._get_iio_dev_attr_str("ch3_enable")

	@ch3_enable.setter
	def ch3_enable(self, value):
		return self._set_iio_dev_attr_str("ch3_enable", value)

	@property
	def mode(self):
		return self._get_iio_dev_attr_str("mode")

	@mode.setter
	def mode(self, value):
		self._set_iio_dev_attr_str("mode", value)

	@property
	def identify(self):
		return self._get_iio_dev_attr_str("identify")

	@identify.setter
	def identify(self, value):
		return self._set_iio_dev_attr_str("identify", value)