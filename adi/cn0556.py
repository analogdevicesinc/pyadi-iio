# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import adi


class cn0556(adi.cn0554):

    """The CN0556 class inherits features from the CN0554 (providing full
    control and monitoring of the input and output voltages and currents)
    and the one_bit_adc_dac (sets the mode of the regulator to either Buck
    or Boost and enables and disables the LT8228). These combined
    functionalities are utilized for a Programmable High Current and
    Voltage Source/Sink Power Supply.

    parameters:
        uri: type=string
            URI of the platform
    """

    _board_config = {
        "buck_input_current_limit": {
            "scale": -1.2174 / 1000.0,
            "offset": 11.345,
            "min": 0.07,
            "max": 10.0,
            "unit": "A"
            # I1P = 11.345-1.1274*ISET1P_CTL
        },
        "buck_output_current_limit": {
            "scale": -4.0108 / 1000.0,
            "offset": 39.623,
            "min": 0.0,
            "max": 35.0,
            "unit": "A"
            # I2P = 39.623-4.0108*ISET2P_CTL
        },
        "buck_input_undervoltage": {
            "scale": -5.1281 / 1000.0,
            "offset": 60.415,
            "min": 12.0,
            "max": 54.0,
            "unit": "V"
            # VUV1 = 60.415-5.1281*UV1_CTL
        },
        "buck_target_output_voltage": {
            "scale": -1.4666 / 1000.0,
            "offset": 15.685,
            "min": 2.0,
            "max": 14.0,
            "unit": "V"
            # V2D = 15.685-1.4666*FB2_CTL
        },
        "boost_input_current_limit": {
            "scale": -4.0108 / 1000.0,
            "offset": 39.623,
            "min": 0.0,
            "max": 35.0,
            "unit": "A"
            # I2N = 39.623-4.0108*ISET2N_CTL
        },
        "boost_output_current_limit": {
            "scale": -1.1274 / 1000.0,
            "offset": 11.345,
            "min": 0.07,
            "max": 10.0,
            "unit": "A"
            # I1N = 11.345-1.1274*ISET1N_CTL
        },
        "boost_input_undervoltage": {
            "scale": -1.2195 / 1000.0,
            "offset": 13.386,
            "min": 8.0,
            "max": 12.0,
            "unit": "V"
            # VUV2 = 13.386-1.2195*UV2_CTL
        },
        "boost_target_output_voltage": {
            "scale": -4.859 / 1000.0,
            "offset": 61.995,
            "min": 14.0,
            "max": 56.0,
            "unit": "V"
            # V2D = 61.995-4.859*FB1_CTL
        },
        # Measurements
        "buck_input_voltage": {
            "scale": 243.0 / 1000.0,
            "offset": 0.0,
            # V1 = V1_ADC*(243k/10k)
        },
        "buck_input_current": {
            "scale": 4.0 / 100.0,
            "offset": 0.0,
            # IV1 = 4*VMON1
        },
        "buck_output_current": {
            "scale": 14.0 / 100.0,
            "offset": 0.0,
            # IV2 = 14*VMON1
        },
        "buck_output_voltage": {
            "scale": 51.0 / 1000.0,
            "offset": 0.0,
            # V2 = V2_ADC*(51k/10k)
        },
        "boost_input_voltage": {
            "scale": 51.0 / 1000.0,
            "offset": 0.0,
            # V2 = V2_ADC*(51k/10k)
        },
        "boost_input_current": {
            "scale": 14.0 / 100.0,
            "offset": 0.0,
            # IV2 = 14*VMON1
        },
        "boost_output_current": {
            "scale": 4.0 / 100.0,
            "offset": 0.0,
            # IV1 = 4*VMON1
        },
        "boost_output_voltage": {
            "scale": 243.0 / 1000.0,
            "offset": 0.0,
            # V1 = V1_ADC*(243k/10k)
        },
        "intvcc_voltage": {"scale": 1 / 100.0, "offset": 0.0},
        "share_voltage": {"scale": 1 / 100.0, "offset": 0.0},
    }

    def __init__(self, uri="ip:analog.local"):
        adi.cn0554.__init__(self, uri=uri)
        self.gpio = adi.one_bit_adc_dac(uri=uri)

        # Enable ADC Channels for reading Voltage and Current Monitoring, INTVCC, SHARE
        self.rx_enabled_channels = [0, 4, 8, 10, 12, 14]
        self.adc_scale = self.adc.channel[0].scale

    @property
    def drxn(self):
        """drxn: operating mode of the board. Returns '1' if in Buck Mode and '0' if in Boost Mode"""
        return self.gpio.gpio_drxn

    @drxn.setter
    def drxn(self, value):
        """drxn: Buck or Boost Mode Setter. Options are: 1 (Buck Mode), 0 (Boost Mode)."""
        if value != 1 and value != 0:
            raise Exception(
                "Invalid Input. Valid values are '1' for Buck Mode and '0' for Boost Mode"
            )

        self.gpio.gpio_drxn = value

    @property
    def enable(self):
        """enable the LT8228 device when True.
        When set to false, device is disabled, DAC outputs set to 0, and sets the DRXN to boost mode."""
        return self.gpio.gpio_en

    @enable.setter
    def enable(self, value):
        if value:
            self.gpio.gpio_en = 1
        else:
            self.dac.voltage0.volt = 0
            self.dac.voltage2.volt = 0
            self.dac.voltage4.volt = 0
            self.dac.voltage6.volt = 0
            self.dac.voltage8.volt = 0
            self.dac.voltage10.volt = 0
            self.dac.voltage12.volt = 0
            self.dac.voltage14.volt = 0
            self.gpio.gpio_en = 0
            self.drxn = 0

    @property
    def intvcc_voltage(self):
        """Return voltage at INTVCC pin in volts (V)"""
        return self.read_value(
            self.adc.channel[10],
            "raw",
            self._board_config["intvcc_voltage"]["scale"] * self.adc_scale,
            self._board_config["intvcc_voltage"]["offset"],
        )

    @property
    def share_voltage(self):
        """Return voltage at SHARE pin in volts (V)"""
        return self.read_value(
            self.adc.channel[12],
            "raw",
            self._board_config["share_voltage"]["scale"] * self.adc_scale,
            self._board_config["share_voltage"]["offset"],
        )

    @property
    def report(self):
        """Check if REPORT is triggered. Returns True if REPORT pin is HIGH."""
        return self.gpio.gpio_report

    @property
    def fault(self):
        """fault: checks if a fault is present. Returns True if a fault occurred."""
        return self.gpio.gpio_fault

    @property
    def buck_output_voltage(self):
        """Read buck output voltage at V2 terminals. Convert ADC data using scale and offset factors based on resistor divider network."""
        return self.read_value(
            self.adc.channel[4],
            "raw",
            self._board_config["buck_output_voltage"]["scale"] * self.adc_scale,
            self._board_config["buck_output_voltage"]["offset"],
        )

    @property
    def buck_target_output_voltage(self):
        """
        Compute for the target buck output voltage set at V2 side
        using DAC data and scale and offset factors based on resistor divider network at FB2 node.

        returns buck target output voltage and DAC output voltage in volts (V)
        return type: (float, float)

        """
        return (
            self.read_value(
                self.dac.voltage2,
                "volt",
                self._board_config["buck_target_output_voltage"]["scale"],
                self._board_config["buck_target_output_voltage"]["offset"],
            ),
            self.dac.voltage2.volt / 1000,
        )

    @buck_target_output_voltage.setter
    def buck_target_output_voltage(self, value):
        """Set buck output voltage at V2 side. Valid values are 2 to 14."""
        try:
            self.set_value(
                value,
                self.dac.voltage2,
                "volt",
                self._board_config["buck_target_output_voltage"]["scale"],
                self._board_config["buck_target_output_voltage"]["offset"],
                self._board_config["buck_target_output_voltage"]["min"],
                self._board_config["buck_target_output_voltage"]["max"],
                self._board_config["buck_target_output_voltage"]["unit"],
            )
        except Exception as e:
            raise e

    @property
    def buck_input_voltage(self):
        """Read buck input voltage at V1 terminals. Convert ADC data using scale and offset factors based on a resistor divider network."""
        return self.read_value(
            self.adc.channel[14],
            "raw",
            self._board_config["buck_input_voltage"]["scale"] * self.adc_scale,
            self._board_config["buck_input_voltage"]["offset"],
        )

    @property
    def buck_output_current(self):
        """Read buck output current at V2 terminals. Convert ADC data using scale and offset factors based on resistor divider at IMON2 node."""
        return self.read_value(
            self.adc.channel[8],
            "raw",
            self._board_config["buck_output_current"]["scale"] * self.adc_scale,
            self._board_config["buck_output_current"]["offset"],
        )

    @property
    def buck_input_current(self):
        """Read buck input current at V1 terminals. Convert ADC data using scale and offset factors based on resistor divider at IMON1 node."""
        return self.read_value(
            self.adc.channel[0],
            "raw",
            self._board_config["buck_input_current"]["scale"] * self.adc_scale,
            self._board_config["buck_input_current"]["offset"],
        )

    @property
    def buck_input_undervoltage(self):
        """
        Compute for the buck input undervoltage set at V1 side
        using DAC data and scale and offset factors based on resistor divider network at UV1 node.

        returns buck input undervoltage and DAC output voltage in volts (V)
        return type: (float, float)

        """

        return (
            self.read_value(
                self.dac.voltage4,
                "volt",
                self._board_config["buck_input_undervoltage"]["scale"],
                self._board_config["buck_input_undervoltage"]["offset"],
            ),
            self.dac.voltage4.volt / 1000,
        )

    @buck_input_undervoltage.setter
    def buck_input_undervoltage(self, value):
        """Set buck input undervoltage V1 side. Valid values are 12 to 54."""
        try:
            self.set_value(
                value,
                self.dac.voltage4,
                "volt",
                self._board_config["buck_input_undervoltage"]["scale"],
                self._board_config["buck_input_undervoltage"]["offset"],
                self._board_config["buck_input_undervoltage"]["min"],
                self._board_config["buck_input_undervoltage"]["max"],
                self._board_config["buck_input_undervoltage"]["unit"],
            )
        except Exception as e:
            raise e

    @property
    def buck_input_current_limit(self):
        """
        Compute for the target buck input current limit set
        using DAC data and scale and offset factors based on resistor divider network at ISET1P node.

        returns buck target input current limit and DAC output voltage in volts (V)
        return type: (float, float)

        """
        return (
            self.read_value(
                self.dac.voltage8,
                "volt",
                self._board_config["buck_input_current_limit"]["scale"],
                self._board_config["buck_input_current_limit"]["offset"],
            ),
            self.dac.voltage8.volt / 1000,
        )

    @buck_input_current_limit.setter
    def buck_input_current_limit(self, value):
        """Set buck input current limit V1 side. Valid values are 0.07 to 10."""
        try:
            self.set_value(
                value,
                self.dac.voltage8,
                "volt",
                self._board_config["buck_input_current_limit"]["scale"],
                self._board_config["buck_input_current_limit"]["offset"],
                self._board_config["buck_input_current_limit"]["min"],
                self._board_config["buck_input_current_limit"]["max"],
                self._board_config["buck_input_current_limit"]["unit"],
            )
        except Exception as e:
            raise e

    @property
    def buck_output_current_limit(self):
        """
        Compute for the target buck output current limit set
        using DAC data and scale and offset factors based on resistor divider network at ISET2P node.

        returns buck target output current limit and DAC output voltage in volts (V)
        return type: (float, float)

        """
        return (
            self.read_value(
                self.dac.voltage12,
                "volt",
                self._board_config["buck_output_current_limit"]["scale"],
                self._board_config["buck_output_current_limit"]["offset"],
            ),
            self.dac.voltage12.volt / 1000,
        )

    @buck_output_current_limit.setter
    def buck_output_current_limit(self, value):
        """Set buck output current limit V2 side. Valid values are 0 to 35."""
        try:
            self.set_value(
                value,
                self.dac.voltage12,
                "volt",
                self._board_config["buck_output_current_limit"]["scale"],
                self._board_config["buck_output_current_limit"]["offset"],
                self._board_config["buck_output_current_limit"]["min"],
                self._board_config["buck_output_current_limit"]["max"],
                self._board_config["buck_output_current_limit"]["unit"],
            )
        except Exception as e:
            raise e

    @property
    def boost_output_voltage(self):
        """Read boost output voltage at V1 terminals. Convert ADC data using scale and offset factors based on resistor divider network."""
        return self.read_value(
            self.adc.channel[14],
            "raw",
            self._board_config["boost_output_voltage"]["scale"] * self.adc_scale,
            self._board_config["boost_output_voltage"]["offset"],
        )

    @property
    def boost_target_output_voltage(self):
        """
        Compute for the target boost output voltage set at V1 side
        using DAC data and scale and offset factors based on resistor divider network at FB1 node.

        returns boost target output voltage and DAC output voltage in volts (V)
        return type: (float, float)

        """
        return (
            self.read_value(
                self.dac.voltage0,
                "volt",
                self._board_config["boost_target_output_voltage"]["scale"],
                self._board_config["boost_target_output_voltage"]["offset"],
            ),
            self.dac.voltage0.volt / 1000,
        )

    @boost_target_output_voltage.setter
    def boost_target_output_voltage(self, value):
        """Set boost output voltage at V1 side. Valid values are 14 to 56."""
        try:
            self.set_value(
                value,
                self.dac.voltage0,
                "volt",
                self._board_config["boost_target_output_voltage"]["scale"],
                self._board_config["boost_target_output_voltage"]["offset"],
                self._board_config["boost_target_output_voltage"]["min"],
                self._board_config["boost_target_output_voltage"]["max"],
                self._board_config["boost_target_output_voltage"]["unit"],
            )
        except Exception as e:
            raise e

    @property
    def boost_input_voltage(self):
        """Read boost input voltage at V2 terminals. Convert ADC data using scale and offset factors based on resistor divider network."""
        return self.read_value(
            self.adc.channel[4],
            "raw",
            self._board_config["boost_input_voltage"]["scale"] * self.adc_scale,
            self._board_config["boost_input_voltage"]["offset"],
        )

    @property
    def boost_output_current(self):
        """Read boost output current at V1 terminals. Convert ADC data using scale and offset factors based on resistor divider at IMON1 node."""
        return self.read_value(
            self.adc.channel[0],
            "raw",
            self._board_config["boost_output_current"]["scale"] * self.adc_scale,
            self._board_config["boost_output_current"]["offset"],
        )

    @property
    def boost_input_current(self):
        """Read boost input current at V2 terminals. Convert ADC data using scale and offset factors based on resistor divider at IMON2 node."""
        return self.read_value(
            self.adc.channel[8],
            "raw",
            self._board_config["boost_input_current"]["scale"] * self.adc_scale,
            self._board_config["boost_input_current"]["offset"],
        )

    @property
    def boost_input_undervoltage(self):
        """
        Compute for the boost input undervoltage set at V2 side
        using DAC data and scale and offset factors based on resistor divider network at UV2 node.

        returns boost input undervoltage and DAC output voltage in volts (V)
        return type: (float, float)

        """
        return (
            self.read_value(
                self.dac.voltage6,
                "volt",
                self._board_config["boost_input_undervoltage"]["scale"],
                self._board_config["boost_input_undervoltage"]["offset"],
            ),
            self.dac.voltage6.volt / 1000,
        )

    @boost_input_undervoltage.setter
    def boost_input_undervoltage(self, value):
        """Set boost input undervoltage V2 side. Valid values are 8 to 12."""
        try:
            self.set_value(
                value,
                self.dac.voltage6,
                "volt",
                self._board_config["boost_input_undervoltage"]["scale"],
                self._board_config["boost_input_undervoltage"]["offset"],
                self._board_config["boost_input_undervoltage"]["min"],
                self._board_config["boost_input_undervoltage"]["max"],
                self._board_config["boost_input_undervoltage"]["unit"],
            )
        except Exception as e:
            raise e

    @property
    def boost_input_current_limit(self):
        """
        Compute for the target boost input current limit set
        using DAC data and scale and offset factors based on resistor divider network at ISET2N node.

        returns boost target input current limit and DAC output voltage in volts (V)
        return type: (float, float)

        """
        return (
            self.read_value(
                self.dac.voltage14,
                "volt",
                self._board_config["boost_input_current_limit"]["scale"],
                self._board_config["boost_input_current_limit"]["offset"],
            ),
            self.dac.voltage14.volt / 1000,
        )

    @boost_input_current_limit.setter
    def boost_input_current_limit(self, value):
        """Set boost input current limit V2 side. Valid values are 0 to 35."""
        try:
            self.set_value(
                value,
                self.dac.voltage14,
                "volt",
                self._board_config["boost_input_current_limit"]["scale"],
                self._board_config["boost_input_current_limit"]["offset"],
                self._board_config["boost_input_current_limit"]["min"],
                self._board_config["boost_input_current_limit"]["max"],
                self._board_config["boost_input_current_limit"]["unit"],
            )
        except Exception as e:
            raise e

    @property
    def boost_output_current_limit(self):
        """
        Compute for the target boost output current limit set
        using DAC data and scale and offset factors based on resistor divider network at ISET1N node.

        returns boost target output current limit and DAC output voltage in volts (V)
        return type: (float, float)

        """
        return (
            self.read_value(
                self.dac.voltage10,
                "volt",
                self._board_config["boost_output_current_limit"]["scale"],
                self._board_config["boost_output_current_limit"]["offset"],
            ),
            self.dac.voltage10.volt / 1000,
        )

    @boost_output_current_limit.setter
    def boost_output_current_limit(self, value):
        """Set boost output current limit V1 side. Valid values are 0.07 to 10."""
        try:
            self.set_value(
                value,
                self.dac.voltage10,
                "volt",
                self._board_config["boost_output_current_limit"]["scale"],
                self._board_config["boost_output_current_limit"]["offset"],
                self._board_config["boost_output_current_limit"]["min"],
                self._board_config["boost_output_current_limit"]["max"],
                self._board_config["boost_output_current_limit"]["unit"],
            )
        except Exception as e:
            raise e

    def read_value(self, ctrl, ctrl_name, scale, offset):
        """Convert ADC data using the scale factor and offset based on simplified formulas derived and scaling
        factors derived using the resistor divider networks at the feedback nodes."""
        return (getattr(ctrl, ctrl_name) * scale) + offset

    def set_value(self, value, ctrl, ctrl_name, scale, offset, val_min, val_max, unit):
        """Convert user input value to equivalent DAC output voltage to control the output voltage and current limits
        using the scale factor and offset based on simplified formulas derived using the resistor
        divider networks at the feedback nodes."""
        if value < val_min or value > val_max:
            raise Exception(
                "Invalid value. Valid values for this property: {} to {} {}".format(
                    val_min, val_max, unit
                )
            )
        setattr(ctrl, ctrl_name, (value - offset) / scale)
