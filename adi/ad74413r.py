from collections import OrderedDict

import numpy as np
from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx

class ad74413r(rx, context_manager):

	_device_name = "ad74413r"

	def __init__(self, uri=""):
		context_manager.__init__(self, uri, self._device_name)
		self._ctrl = self._ctx.find_device("ad74413r")
		self._rxadc = self._ctx.find_device("ad74413r")
		self._trigger = self._ctx.find_device("ad74413r-dev0")
		self._rxadc._set_trigger(self._trigger)
		self._rx_channel_names = []
		self._tx_channel_names = []

		self.rx_channel = []
		self.tx_channel = []

		if not self._ctrl:
			raise Exception("No ad74413r device found")

		_rx_channels = []
		_tx_channels = []
		_channels = []
		for ch in self._ctrl.channels:
			if ch.output:
				self._tx_channel_names.append(ch.id)
				self.tx_channel.append((ch.id, self._channel(self._ctrl, ch.id, ch.output)))
				_tx_channels.append((ch.id, self._channel(self._ctrl, ch.id, ch.output)))
			else:
				self._rx_channel_names.append(ch.id)
				self.rx_channel.append((ch.id, self._channel(self._ctrl, ch.id, ch.output)))
				_rx_channels.append((ch.id, self._channel(self._ctrl, ch.id, ch.output)))
			_channels.append((ch.id, self._channel(self._ctrl, ch.id, ch.output)))
		self.channel = OrderedDict(_channels)
		self.rx_channel = OrderedDict(_rx_channels)
		self.tx_channel = OrderedDict(_tx_channels)

		rx.__init__(self)

	def reg_read(self, reg):
		return self._ctrl.reg_read(reg)

	def reg_write(self, reg, value):
		return self._ctrl.reg_write(reg, value)

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
		def sampling_frequency(self):
			return self._get_iio_attr(self.name, "sampling_frequency", self.output)

		@sampling_frequency.setter
		def sampling_frequency(self, value):
			return self._set_iio_attr(self.name, "sampling_frequency", self.output, value)

		@property
		def sampling_frequency_available(self):
			return self._get_iio_attr(self.name, "sampling_frequency_available", self.output)

		@property
		def processed(self):
			return self._get_iio_attr(self.name, "processed", self.output)

		@property
		def threshold(self):
			return self._get_iio_attr(self.name, "threshold", self.output)

		@threshold.setter
		def threshold(self, value):
			return self._set_iio_attr(self.name, "threshold", self.output, value)

		@property
		def diag_function(self):
			return self._get_iio_attr_str(self.name, "diag_function", self.output)

		@property
		def diag_function_available(self):
			return self._get_iio_attr_str(self.name, "diag_function_available", self.output)

		@diag_function.setter
		def diag_function(self, value):
			return self._set_iio_attr(self.name, "diag_function", self.output, value)


