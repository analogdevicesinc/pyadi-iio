from collections import OrderedDict

import numpy as np
from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx

class max14906(context_manager):

	_device_name = "max14906"

	def __init__(self, uri=""):
		context_manager.__init__(self, uri, self._device_name)
		self._ctrl = self._ctx.find_device("max14906")
		self._rx_channel_names = []
		self._tx_channel_names = []

		if not self._ctrl:
			raise Exception("No max14906 device found")

		_channels = []
		for ch in self._ctrl.channels:
			if ch.output:
				self._tx_channel_names.append(ch.id)
			else:
				self._rx_channel_names.append(ch.id)
			_channels.append((ch.id, self._channel(self._ctrl, ch.id, ch.output)))
		self.channel = OrderedDict(_channels)

	def reg_read(self, reg):
		self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
		return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

	def reg_write(self, reg, value):
		self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)

	class _channel(attribute):

		def __init__(self, ctrl, channel_name, output):
			self.name = channel_name
			self._ctrl = ctrl
			self.output = output

		@property
		def raw(self):
			return self._get_iio_attr(self.name, "raw", self.output)

		@raw.setter
		def raw(self, value):
			return self._set_iio_attr(self.name, "raw", self.output, value)

		@property
		def scale(self):
			return self._get_iio_attr(self.name, "scale", self.output)

		@property
		def offset(self):
			return self._get_iio_attr(self.name, "offset", self.output)
