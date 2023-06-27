from collections import OrderedDict

import numpy as np
from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx

class max14906(rx, context_manager):

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
		return self._ctrl.reg_read(reg)
		# return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

	def reg_write(self, reg, value):
		return self._ctrl.reg_write(reg, value)
		# return self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)

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

		@property
		def current_limit(self):
			if not self.output:
				return 0
			return self._get_iio_attr(self.name, "current_limit", self.output)

		@current_limit.setter
		def current_limit(self, value):
			if not self.output:
				return 0
			return self._get_iio_attr(self.name, "current_limit", self.output, value)

		@property
		def current_limit_available(self):
			if not self.output:
				return 0
			return self._get_iio_attr(self.name, "current_limit_available", self.output)

		@property
		def do_mode(self):
			if not self.output:
				return 0
			return self._get_iio_attr(self.name, "do_mode", self.output)

		@do_mode.setter
		def do_mode(self, value):
			if not self.output:
				return 0
			return self._set_iio_attr(self.name, "do_mode", self.output, value)

		@property
		def do_mode_available(self):
			if not self.output:
				return 0
			return self._get_iio_attr(self.name, "do_mode_available", self.output)

		@property
		def IEC_type(self):
			if self.output:
				return 0
			return self._get_iio_attr(self.name, "IEC_Type", self.output)

		@IEC_type.setter
		def IEC_type(self, value):
			if self.output:
				return 0
			return self._set_iio_attr(self.name, "IEC_Type", self.output, value)

		@property
		def IEC_type_available(self):
			if self.output:
				return 0
			return self._get_iio_attr(self.name, "IEC_Type_available", self.output)