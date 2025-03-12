# Copyright (C) 2022-2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import rx


class pqmon(rx, context_manager, attribute):
    """ The AD-PQMON-SL is a power quality monitoring solution based on the ADE9430,\n
      which is a high performance, polyphase energy and Class S power quality monitoring \n
      and energy metering device.
    """

    _device_name = "AD-PQMON-SL"
    swell_events = []
    dip_events = []
    rvc_events = []
    intrpt_events = []

    _rx_channel_names = [
        "voltage0",
        "current0",
        "voltage1",
        "current1",
        "voltage2",
        "current2",
        "current3",
    ]

    def __repr__(self):
        retstr = f"""
pqmon(uri="{self.uri}, device_name={self._device_name})"

{self.__doc__}
"""

        return retstr

    def __init__(self, uri=""):

        context_manager.__init__(self, uri)

        found = False
        for device in self._ctx.devices:
            if "pqm" in device.name:
                self._ctrl = device
                self._rxadc = device
                self.rx_output_type = "SI"
                found = True
                break

        if not found:
            raise Exception("Could not find PQM device")

        self.current_a = self.current_channel_phase(self._ctrl, "current0")
        self.current_b = self.current_channel_phase(self._ctrl, "current1")
        self.current_c = self.current_channel_phase(self._ctrl, "current2")
        self.current_n = self.current_channel(self._ctrl, "current3")
        self.voltage_a = self.voltage_channel(self._ctrl, "voltage0")
        self.voltage_b = self.voltage_channel(self._ctrl, "voltage1")
        self.voltage_c = self.voltage_channel(self._ctrl, "voltage2")
        self.config = self.config(self._ctrl, "config")

        rx.__init__(self)

        self.rx_buffer_size = 256
        self.rx_enabled_channels = [0, 1, 2, 3, 4, 5, 6]

    class current_channel(attribute):
        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl
            self._output = False

        @property
        def rms(self):
            return self._get_iio_attr(self.name, "rms", False)

        @property
        def angle(self):
            return self._get_iio_attr(self.name, "angle", False)

        @property
        def scale(self):
            return self._get_iio_attr(self.name, "scale", False)

        @property
        def raw(self):
            return self._get_iio_attr(self.name, "raw", False)

    class current_channel_phase(current_channel):
        @property
        def harmonics(self):
            har = self._get_iio_attr(self.name, "harmonics", False)
            return [float(x) for x in har]

        @property
        def inter_harmonics(self):
            har = self._get_iio_attr(self.name, "inter_harmonics", False)
            return [float(x) for x in har]

        @property
        def thd(self):
            return self._get_iio_attr(self.name, "thd", False)

    class voltage_channel(attribute):
        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl
            self._output = False

        @property
        def rms(self):
            return self._get_iio_attr(self.name, "rms", False)

        @property
        def angle(self):
            return self._get_iio_attr(self.name, "angle", False)

        @property
        def harmonics(self):
            har = self._get_iio_attr(self.name, "harmonics", False)
            return [float(x) for x in har]

        @property
        def inter_harmonics(self):
            har = self._get_iio_attr(self.name, "inter_harmonics", False)
            return [float(x) for x in har]

        @property
        def scale(self):
            return self._get_iio_attr(self.name, "scale", False)

        @property
        def thd(self):
            return self._get_iio_attr(self.name, "thd", False)

        @property
        def raw(self):
            return self._get_iio_attr(self.name, "raw", False)

        @property
        def deviation_under(self):
            return self._get_iio_attr(self.name, "deviation_under", False)

        @property
        def deviation_over(self):
            return self._get_iio_attr(self.name, "deviation_over", False)

        @property
        def pinst(self):
            return self._get_iio_attr(self.name, "pinst", False)

        @property
        def pst(self):
            return self._get_iio_attr(self.name, "pst", False)

        @property
        def plt(self):
            return self._get_iio_attr(self.name, "plt", False)

        @property
        def magnitude1012(self):
            return self._get_iio_attr(self.name, "magnitude1012", False)

        @property
        def max_magnitude(self):
            return self._get_iio_attr(self.name, "maxMagnitude", False)

    def read_events(self):
        dips_cnt = self._get_iio_attr("dips", "countEvent", True)
        swells_cnt = self._get_iio_attr("swells", "countEvent", True)
        rvc_cnt = self._get_iio_attr("rvc", "countEvent", True)
        intrpt_cnt = self._get_iio_attr("intrpt", "countEvent", True)

        self.rvc_events = []
        self.intrpt_events = []
        self.swell_events = []
        self.dip_events = []

        if dips_cnt != 0:
            test = self._get_iio_attr("dips", "startTime", True)
            print(test)
            start_time = [int(x) for x in self._get_iio_attr("dips", "startTime", True)]
            end_time = [int(x) for x in self._get_iio_attr("dips", "endTime", True)]
            duration = [
                int(x) for x in self._get_iio_attr("dips", "durationInCycles", True)
            ]
            min_mag = [int(x) for x in self._get_iio_attr("dips", "minMag", True)]

            for i in range(dips_cnt):
                self.dip_events.append(
                    self._dip_event(start_time[i], end_time[i], duration[i], min_mag[i])
                )

        if swells_cnt != 0:
            start_time = [
                int(x) for x in self._get_iio_attr("swells", "startTime", True)
            ]
            end_time = [int(x) for x in self._get_iio_attr("swells", "endTime", True)]
            duration = [
                int(x) for x in self._get_iio_attr("swells", "durationInCycles", True)
            ]
            max_mag = [int(x) for x in self._get_iio_attr("swells", "maxMag", True)]

            for i in range(swells_cnt):
                self.swell_events.append(
                    self._swell_event(
                        start_time[i], end_time[i], duration[i], max_mag[i]
                    )
                )

        if rvc_cnt != 0:
            start_time = [int(x) for x in self._get_iio_attr("rvc", "startTime", True)]
            end_time = [int(x) for x in self._get_iio_attr("rvc", "endTime", True)]
            duration = [
                int(x) for x in self._get_iio_attr("rvc", "durationInCycles", True)
            ]
            delta_umax = [int(x) for x in self._get_iio_attr("rvc", "deltaUmax", True)]
            delta_uss = [int(x) for x in self._get_iio_attr("rvc", "deltaUss", True)]

            for i in range(rvc_cnt):
                self.rvc_events.append(
                    self._rvc_event(
                        start_time[i],
                        end_time[i],
                        duration[i],
                        delta_umax[i],
                        delta_uss[i],
                    )
                )

        if intrpt_cnt != 0:
            start_time = [
                int(x) for x in self._get_iio_attr("intrpt", "startTime", True)
            ]
            end_time = [int(x) for x in self._get_iio_attr("intrpt", "endTime", True)]
            duration = [
                int(x) for x in self._get_iio_attr("intrpt", "durationInCycles", True)
            ]

            for i in range(intrpt_cnt):
                self.intrpt_events.append(
                    self._event(start_time[i], end_time[i], duration[i])
                )

        pass

    class _event:
        def __init__(self, start_time, end_time, duration):
            self.start_time = start_time
            self.end_time = end_time
            self.duration = duration

        def __repr__(self):
            return (self.start_time, self.end_time, self.duration)

    class _swell_event(_event):
        def __init__(self, start_time, end_time, duration, max_mag):
            super().__init__(start_time, end_time, duration)
            self.max_mag = max_mag

        def __repr__(self):
            return (self.start_time, self.end_time, self.duration, self.max_mag)

    class _dip_event(_event):
        def __init__(self, start_time, end_time, duration, min_mag):
            super().__init__(start_time, end_time, duration)
            self.min_mag = min_mag

        def __repr__(self):
            return (self.start_time, self.end_time, self.duration, self.min_mag)

    class _rvc_event(_event):
        def __init__(self, start_time, end_time, duration, delta_umax, delta_uss):
            super().__init__(start_time, end_time, duration)
            self.delta_umax = delta_umax
            self.delta_uss = delta_uss

        def __repr__(self):
            return (
                self.start_time,
                self.end_time,
                self.duration,
                self.delta_umax,
                self.delta_uss,
            )

    class config(attribute):
        """ The config class is used to configure the AD-PQMON-SL device power analysis
        parameters as required by the ADSW-PQ-CLS library

        This class also implements the process_data attribute which is used to enable
        power quality measurements (when set to true) or waveform measurements (when set
        to false)

        The single_shot_acquisition attribute is used to enable single shot acquisition
        (by default True). When this attribute is set to False, the device is set up for
        continuous acquisition and it will not reset the process_data attribute between
        acquisitions.
        """

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl
            self._single_shot_acquisition = True

            self.v_consel_available = [
                "4W_WYE",
                "3W_DELTA_VA_VB_NEGVC",
                "4W_WYE_VB_NEGVA_NEGVC",
                "4W_DELTA_VB_NEGVA",
                "4W_DELTA_VA_VB_VC",
            ]
            self.flicker_model_available = [
                "230V_50HZ",
                "230V_60HZ",
                "120V_50HZ",
                "120V_60HZ",
            ]
            self.nominal_frequency_available = [50, 60]

        @property
        def u2(self):
            return self._get_iio_dev_attr("u2")

        @property
        def u0(self):
            return self._get_iio_dev_attr("u0")

        @property
        def sneg_voltage(self):
            return self._get_iio_dev_attr("sneg_voltage")

        @property
        def szro_voltage(self):
            return self._get_iio_dev_attr("szro_voltage")

        @property
        def i2(self):
            return self._get_iio_dev_attr("i2")

        @property
        def i0(self):
            return self._get_iio_dev_attr("i0")

        @property
        def sneg_current(self):
            return self._get_iio_dev_attr("sneg_current")

        @property
        def spos_current(self):
            return self._get_iio_dev_attr("spos_current")

        @property
        def szro_current(self):
            return self._get_iio_dev_attr("szro_current")

        @property
        def nominal_voltage(self):
            return self._get_iio_dev_attr("nominal_voltage")

        @nominal_voltage.setter
        def nominal_voltage(self, value):
            self._set_iio_dev_attr_str("nominal_voltage", value)

        @property
        def voltage_scale(self):
            return self._get_iio_dev_attr("voltage_scale")

        @voltage_scale.setter
        def voltage_scale(self, value):
            self._set_iio_dev_attr_str("voltage_scale", value)

        @property
        def current_scale(self):
            return self._get_iio_dev_attr("current_scale")

        @current_scale.setter
        def current_scale(self, value):
            self._set_iio_dev_attr_str("current_scale", value)

        @property
        def i_consel_en(self):
            return self._get_iio_dev_attr("i_consel_en")

        @i_consel_en.setter
        def i_consel_en(self, value):
            self._set_iio_dev_attr_str("i_consel_en", value)

        @property
        def dip_threshold(self):
            return self._get_iio_dev_attr("dip_threshold")

        @dip_threshold.setter
        def dip_threshold(self, value):
            self._set_iio_dev_attr_str("dip_threshold", value)

        @property
        def dip_hysteresis(self):
            return self._get_iio_dev_attr("dip_hysteresis")

        @dip_hysteresis.setter
        def dip_hysteresis(self, value):
            self._set_iio_dev_attr_str("dip_hysteresis", value)

        @property
        def swell_threshold(self):
            return self._get_iio_dev_attr("swell_threshold")

        @swell_threshold.setter
        def swell_threshold(self, value):
            self._set_iio_dev_attr_str("swell_threshold", value)

        @property
        def swell_hysteresis(self):
            return self._get_iio_dev_attr("swell_hysteresis")

        @swell_hysteresis.setter
        def swell_hysteresis(self, value):
            self._set_iio_dev_attr_str("swell_hysteresis", value)

        @property
        def intrp_hysteresis(self):
            return self._get_iio_dev_attr("intrp_hysteresis")

        @intrp_hysteresis.setter
        def intrp_hysteresis(self, value):
            self._set_iio_dev_attr_str("intrp_hysteresis", value)

        @property
        def intrp_threshold(self):
            return self._get_iio_dev_attr("intrp_threshold")

        @intrp_threshold.setter
        def intrp_threshold(self, value):
            self._set_iio_dev_attr_str("intrp_threshold", value)

        @property
        def rvc_threshold(self):
            return self._get_iio_dev_attr("rvc_threshold")

        @rvc_threshold.setter
        def rvc_threshold(self, value):
            self._set_iio_dev_attr_str("rvc_threshold", value)

        @property
        def rvc_hysteresis(self):
            return self._get_iio_dev_attr("rvc_hysteresis")

        @rvc_hysteresis.setter
        def rvc_hysteresis(self, value):
            self._set_iio_dev_attr_str("rvc_hysteresis", value)

        @property
        def msv_carrier_frequency(self):
            return self._get_iio_dev_attr("msv_carrier_frequency")

        @msv_carrier_frequency.setter
        def msv_carrier_frequency(self, value):
            self._set_iio_dev_attr_str("msv_carrier_frequency", value)

        @property
        def msv_record_length(self):
            return self._get_iio_dev_attr("msv_record_length")

        @msv_record_length.setter
        def msv_record_length(self, value):
            self._set_iio_dev_attr_str("msv_record_length", value)

        @property
        def msv_threshold(self):
            return self._get_iio_dev_attr("msv_threshold")

        @msv_threshold.setter
        def msv_threshold(self, value):
            self._set_iio_dev_attr_str("msv_threshold", value)

        @property
        def sampling_frequency(self):
            return self._get_iio_dev_attr("sampling_frequency")

        @property
        def v_consel(self):
            return self._get_iio_dev_attr("v_consel")

        @v_consel.setter
        def v_consel(self, value):
            if value not in self.v_consel_available:
                raise ValueError("v_consel must be in v_consel_available")
            self._set_iio_dev_attr_str("v_consel", value)

        @property
        def flicker_model(self):
            return self._get_iio_dev_attr("flicker_model")

        @flicker_model.setter
        def flicker_model(self, value):
            if value not in self.flicker_model_available:
                raise ValueError("flicker_model must be in flicker_model_available")
            self._set_iio_dev_attr_str("flicker_model", value)

        @property
        def nominal_frequency(self):
            return self._get_iio_dev_attr("nominal_frequency")

        @nominal_frequency.setter
        def nominal_frequency(self, value):
            if value not in self.nominal_frequency_available:
                raise ValueError(
                    "nominal_frequency must be in nominal_frequency_available"
                )
            self._set_iio_dev_attr_str("nominal_frequency", str(value))

        @property
        def firmware_version(self):
            return self._get_iio_dev_attr("fw_version")

        @property
        def process_data(self):
            return self._get_iio_dev_attr("process_data")

        @process_data.setter
        def process_data(self, value):
            self._set_iio_dev_attr_str("process_data", value)

        pass

        @property
        def single_shot_acquisition(self):
            return self._single_shot_acquisition

        @single_shot_acquisition.setter
        def single_shot_acquisition(self, value):
            self._single_shot_acquisition = value
            if value is True:
                self.process_data = True

    def rx(self):
        """ The AD-PQMON-SL device only allows for buffers where all channels are
        enabled at the same time with buffer sizes of 256 samples.
        """

        self._rx_channel_names = [
            "current0",
            "voltage0",
            "current1",
            "voltage1",
            "current2",
            "voltage2",
            "current3",
        ]
        self.rx_buffer_size = 256
        self.rx_enabled_channels = [0, 1, 2, 3, 4, 5, 6]

        self.config.process_data = False
        data = rx.rx(self)

        if self.config._single_shot_acquisition:
            self.config.process_data = True

        return data
