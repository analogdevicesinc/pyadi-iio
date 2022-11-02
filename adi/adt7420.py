# -*- coding: utf-8 -*-
"""
Created on Tue Sep 27 09:34:29 2022

@author: jsanbuen
"""

from adi.attribute import attribute
from adi.context_manager import context_manager


class adt7420(context_manager, attribute):
    _device_name = "adt7420"
    
    def __init__(self, uri=""):

        context_manager.__init__(self, uri, self._device_name)
        self.temp = self._channel(self._ctrl, "temp")
        self._ctrl = self._ctx.find_device("adt7420")
        
    class _channel(attribute):
        """ADT7420 Channel"""
        
        def __init__(self, ctrl, channel_name):
            self._ctrl = ctrl
            self.name = channel_name

        @property
        def temp(self):
            """ ADT7420 Channel Temperature Value """
            return self._get_iio_attr(self.name, "temp", False)

        @property        
        def temp_max(self):
            """ ADT7420 Channel Max Temperature """
            return self._get_iio_attr_str(self.name, "temp_max", False)
        
        @property
        def temp_min(self):
            """ ADT7420 Channel Min Temperature """
            return self._get_iio_attr_str(self.name, "temp_min", False)
        
        @property
        def temp_crit(self):
            """ ADT7420 Channel Critical Temperature """
            return self._get_iio_attr_str(self.name, "temp_crit", False)
        
        @property
        def temp_hyst(self):
            """ ADT7420 Channel Hysteresis Temperature """
            return self._get_iio_attr_str(self.name, "temp_hyst", False)
        