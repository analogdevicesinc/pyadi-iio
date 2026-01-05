# Copyright (C) 2023-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import pickle
from time import sleep

import numpy as np

import adi
from adi.adar1000 import adar1000_array
from adi.adf4159 import adf4159


class CN0566(adf4159, adar1000_array):
    """CN0566 class inherits from adar1000_array and adf4159 and adds
    operations for beamforming like default configuration,
    calibration, set_beam_phase_diff, etc.
    _gpios (as one-bit-adc-dac) are instantiated internally.
    ad7291 temperature / voltage monitor instantiated internally.
    CN0566.sdr property is an instance of a Pluto SDR with updated firmware,
    and updated to 2t2r.

    parameters:
        uri: type=string
            URI of Raspberry Pi attached to the phaser board
        verbose: type=boolean
            Print extra debug information
    """

    # MWT: Open question: Refactor to nest rather than inherit?

    num_elements = 8
    """Number of antenna elements"""
    phase_step_size = 2.8125  # it is 360/2**number of bits. (number of bits = 6)
    """Phase adjustment resolution"""
    c = 299792458
    """speed of light in m/s"""
    element_spacing = 0.015
    """Element to element spacing of the antenna in meters"""
    device_mode = "rx"
    """For future RX/TX operation. Set to RX."""

    # Scaling factors for voltage AD7291 monitor, straight from schematic.
    _v0_vdd1v8_scale = 1.0 + (10.0 / 10.0)  # Resistances in k ohms.
    _v1_vdd3v0_scale = 1.0 + (10.0 / 10.0)
    _v2_vdd3v3_scale = 1.0 + (10.0 / 10.0)
    _v3_vdd4v5_scale = 1.0 + (30.1 / 10.0)
    _v4_vdd_amp_scale = 1.0 + (69.8 / 10.0)
    _v5_vinput_scale = 1.0 + (30.1 / 10.0)
    _v6_imon_scale = 1.0  # LTC4217 IMON = 50uA/A * 20k = 1 V / A
    _v7_vtune_scale = 1.0 + (69.8 / 10.0)

    def __init__(
        self,
        uri=None,
        sdr=None,
        _chip_ids=["BEAM0", "BEAM1"],
        _device_map=[[1], [2]],
        _element_map=[[1, 2, 3, 4, 5, 6, 7, 8]],  # [[1, 2, 3, 4], [5, 6, 7, 8]],
        _device_element_map={
            1: [7, 8, 5, 6],  # i.e. channel2 of device1 (BEAM0), maps to element 8
            2: [3, 4, 1, 2],
        },
        verbose=False,
    ):
        """ Set up devices, properties, helper methods, etc. """
        if verbose is True:
            print("attempting to open ADF4159, uri: ", str(uri))
        adf4159.__init__(self, uri)
        if verbose is True:
            print("attempting to open ADAR1000 array, uri: ", str(uri))
        sleep(0.5)
        adar1000_array.__init__(
            self, uri, _chip_ids, _device_map, _element_map, _device_element_map
        )

        if verbose is True:
            print("attempting to open gpios , uri: ", str(uri))
        sleep(0.5)
        self._gpios = adi.one_bit_adc_dac(uri)

        if verbose is True:
            print("attempting to open AD7291 v/t monitor, uri: ", str(uri))
        sleep(0.5)
        self._monitor = adi.ad7291(uri)

        """ Initialize all the class variables for the project. """

        self.Averages = 16  # Number of Avg to be taken.

        self.pcal = [0.0 for i in range(0, (self.num_elements))]
        """ Phase calibration array. Add this value to the desired phase. Initialize to zero (no correction). """
        self.ccal = [0.0, 0.0]
        """ Gain compensation for the two RX channels in dB. Includes all errors, including the SDRs """
        self.gcal = [1.0 for i in range(0, self.num_elements)]
        """ Per-element gain compensation, AFTER above channel compensation. Use to scale value sent to ADAR1000. """
        self.ph_deltas = [
            0 for i in range(0, (self.num_elements) - 1)
        ]  # Phase delta between elements
        self.sdr = sdr  # rx_device/sdr that rx and plots
        self.gain_cal = False  # gain/phase calibration status flag it goes True when performing calibration
        self.phase_cal = False

        ### Initialize ADF4159 / Local Oscillator ###

        self.lo = 10.5e9  # Nominal operating frequency

        BW = 500e6 / 4
        num_steps = 1000
        self.freq_dev_range = int(
            BW
        )  # frequency deviation range in Hz.  This is the total freq deviation of the complete freq ramp
        self.freq_dev_step = int(
            BW / num_steps
        )  # frequency deviation step in Hz.  This is fDEV, in Hz.  Can be positive or negative
        self.freq_dev_time = int(
            1e3
        )  # total time (in us) of the complete frequency ramp
        self.ramp_mode = "disabled"  # ramp_mode can be:  "disabled", "continuous_sawtooth", "continuous_triangular", "single_sawtooth_burst", "single_ramp_burst"
        self.delay_word = 4095  # 12 bit delay word.  4095*PFD = 40.95 us.  For sawtooth ramps, this is also the length of the Ramp_complete signal
        self.delay_clk = "PFD"  # can be 'PFD' or 'PFD*CLK1'
        self.delay_start_en = 0  # delay start
        self.ramp_delay_en = 0  # delay between ramps.
        self.trig_delay_en = 0  # triangle delay
        self.sing_ful_tri = 0  # full triangle enable/disable -- this is used with the single_ramp_burst mode
        self.tx_trig_en = 0  # start a ramp with TXdata
        # pll.clk1_value = 100
        # pll.phase_value = 3
        self.powerdown = 0
        self.enable = 0  # 0 = PLL enable.  Write this last to update all the registers

        ### Initialize gpios / set outputs ###
        self._gpios.gpio_vctrl_1 = 1  # Onboard PLL/LO source
        self._gpios.gpio_vctrl_2 = 1  # Send LO to TX circuitry

        self._gpios.gpio_div_mr = 0  # TX switch toggler divider reset
        self._gpios.gpio_div_s0 = 0  # TX toggle divider lsb (1s)
        self._gpios.gpio_div_s1 = 0  # TX toggle divider 2s
        self._gpios.gpio_div_s2 = 0  # TX toggle divider 4s
        self._gpios.gpio_rx_load = 0  # ADAR1000 RX load (cycle through RAM table)
        self._gpios.gpio_tr = 0  # ADAR1000 transmit / receive mode. RX = 0 (assuming)
        self._gpios.gpio_tx_sw = (
            0  # Direct control of TX switch when div=[000]. 0 = TX_OUT_2, 1 = TX_OUT_1
        )
        # Read input
        self.muxout = (
            self._gpios.gpio_muxout
        )  # PLL MUXOUT, assign to PLL lock in the future

    def set_tx_sw_div(self, div_ratio):
        """ Set TX switch toggle divide ratio. Possible values are:
                0 (direct TX_OUT control via gpio_tx_sw)
                divide by 2, 4, 8, 16, 32, 64, 128"""
        div_pin_map = {0: 0, 2: 1, 4: 2, 8: 3, 16: 4, 32: 5, 64: 6, 128: 7}
        if div_pin_map.__contains__(div_ratio):
            self._gpios.gpio_div_s0 = 0b001 & div_pin_map[div_ratio]
            self._gpios.gpio_div_s1 = (0b010 & div_pin_map[div_ratio]) >> 1
            self._gpios.gpio_div_s2 = (0b100 & div_pin_map[div_ratio]) >> 2
        else:
            print(
                "Invalid divide ratio, options are 0 for direct control"
                " via gpio_tx_sw, 2, 4, 8, 16, 32, 64, 128"
            )

    def read_monitor(self, verbose=False):
        """ Read all voltage / temperature monitor channels.

        Parameters
        ----------
        verbose: type=bool
            Print each channel's information if true.
        returns:
            An array of all readings in SI units (deg. C, Volts)
        """
        board_temperature = self._monitor.temp0()
        v0_vdd1v8 = self._monitor.voltage0() * self._v0_vdd1v8_scale / 1000.0
        v1_vdd3v0 = self._monitor.voltage1() * self._v1_vdd3v0_scale / 1000.0
        v2_vdd3v3 = self._monitor.voltage2() * self._v2_vdd3v3_scale / 1000.0
        v3_vdd4v5 = self._monitor.voltage3() * self._v3_vdd4v5_scale / 1000.0
        v4_vdd_amp = self._monitor.voltage4() * self._v4_vdd_amp_scale / 1000.0
        v5_vinput = self._monitor.voltage5() * self._v5_vinput_scale / 1000.0
        v6_imon = self._monitor.voltage6() * self._v6_imon_scale / 1000.0
        v7_vtune = self._monitor.voltage7() * self._v7_vtune_scale / 1000.0
        if verbose is True:
            print("Board temperature: ", board_temperature)
            print("1.8V supply: ", v0_vdd1v8)
            print("3.0V supply: ", v1_vdd3v0)
            print("3.3V supply: ", v2_vdd3v3)
            print("4.5V supply: ", v3_vdd4v5)
            print("Vtune amp supply: ", v4_vdd_amp)
            print("USB C input supply: ", v5_vinput)
            print("Board current: ", v6_imon)
            print("VTune: ", v7_vtune)
        return [
            board_temperature,
            v0_vdd1v8,
            v1_vdd3v0,
            v2_vdd3v3,
            v3_vdd4v5,
            v4_vdd_amp,
            v5_vinput,
            v6_imon,
            v7_vtune,
        ]

    @property
    def lo(self):
        """Get the VCO output frequency, accounting for the /4 ahead of the ADF4159 RFIN."""
        return self.frequency * 4.0

    @lo.setter
    def lo(self, value):
        """Set the VCO output frequency, accounting for the /4 ahead of the ADF4159 RFIN."""
        self.frequency = int(value / 4)

    def configure(self, device_mode="rx"):
        """
        Configure the device/beamformer properties like RAM bypass, Tr source etc.

        Parameters
        ----------
        device_mode: type=string
            ("rx", "tx", "disabled", default = "rx")
        """
        self.device_mode = device_mode
        for device in self.devices.values():  # Configure ADAR1000s
            device.sequencer_enable = False
            # False sets a bit high and SPI control
            device.beam_mem_enable = (
                False  # RAM control vs SPI control of the adar state, reg 0x38, bit 6.
            )
            device.bias_mem_enable = (
                False  # RAM control vs SPI control of the bias state, reg 0x38, bit 5.
            )
            device.pol_state = False  # Polarity switch state, reg 0x31, bit 0. True outputs -5V, False outputs 0V
            device.pol_switch_enable = (
                False  # Enables switch driver for ADTR1107 switch, reg 0x31, bit 3
            )
            device.tr_source = "spi"  # TR source for chip, reg 0x31 bit 2. 'ext' sets bit high, 'spi' sets a bit low
            device.tr_spi = "rx"  # TR SPI control, reg 0x31 bit 1.  'tx' sets bit high, 'rx' sets a bit low
            device.tr_switch_enable = (
                True  # Switch driver for external switch, reg0x31, bit 4
            )
            device.external_tr_polarity = (
                True  # Sets polarity of TR switch compared to TR state of ADAR1000.
            )

            device.rx_vga_enable = True  # Enables Rx VGA, reg 0x2E, bit 0.
            device.rx_vm_enable = True  # Enables Rx VGA, reg 0x2E, bit 1.
            device.rx_lna_enable = True  # Enables Rx LNA, reg 0x2E, bit 2. bit3,4,5,6 enables RX for all the channels
            device._ctrl.reg_write(
                0x2E, 0x7F
            )  # bit3,4,5,6 enables RX for all the channels.
            device.rx_lna_bias_current = (
                8  # Sets the LNA bias to the middle of its range
            )
            device.rx_vga_vm_bias_current = (
                22  # Sets the VGA and vector modulator bias.
            )

            device.tx_vga_enable = True  # Enables Tx VGA, reg 0x2F, bit0
            device.tx_vm_enable = True  # Enables Tx Vector Modulator, reg 0x2F, bit1
            device.tx_pa_enable = True  # Enables Tx channel drivers, reg 0x2F, bit2
            device.tx_pa_bias_current = 6  # Sets Tx driver bias current
            device.tx_vga_vm_bias_current = 22  # Sets Tx VGA and VM bias.

            if self.device_mode == "rx":
                # Configure the device for Rx mode
                device.mode = "rx"  # Mode of operation, bit 5 of reg 0x31. "rx", "tx", or "disabled".

                SELF_BIASED_LNAs = True
                if SELF_BIASED_LNAs:
                    # Allow the external LNAs to self-bias
                    # this writes 0xA0 0x30 0x00. Disabling it allows LNAs to stay in self bias mode all the time
                    device.lna_bias_out_enable = False
                    # self._ctrl.reg_write(0x30, 0x00)   #Disables PA and DAC bias
                else:
                    # Set the external LNA bias
                    device.lna_bias_on = -0.7  # this writes 0x25 to register 0x2D.
                    # self._ctrl.reg_write(0x30, 0x20)   #Enables PA and DAC bias.

                # Enable the Rx path for each channel
                for channel in device.channels:
                    channel.rx_enable = True  # this writes reg0x2E with data 0x00, then reg0x2E with data 0x20.
                    channel.rx_gain = 127
                    #  So it overwrites 0x2E, and enables only one channel

            # Configure the device for Tx mode
            elif self.device_mode == "tx":
                device.mode = "tx"

                # Enable the Tx path for each channel and set the external PA bias
                for channel in device.channels:
                    channel.tx_enable = True
                    channel.tx_gain = 127
                    channel.pa_bias_on = -2

            else:
                raise ValueError(
                    "Configure Device in proper mode"
                )  # If device mode is neither Rx nor Tx

            if self.device_mode == "rx":
                device.latch_rx_settings()  # writes 0x01 to reg 0x28.
            elif self.device_mode == "tx":
                device.latch_tx_settings()  # writes 0x02 to reg 0x28.

    def save_channel_cal(self, filename="channel_cal_val.pkl"):
        """ Saves channel calibration file."""
        with open(filename, "wb") as file1:
            pickle.dump(self.ccal, file1)  # save calibrated gain value to a file
            file1.close()

    def save_gain_cal(self, filename="gain_cal_val.pkl"):
        """ Saves gain calibration file."""
        with open(filename, "wb") as file1:
            pickle.dump(self.gcal, file1)  # save calibrated gain value to a file
            file1.close()

    def save_phase_cal(self, filename="phase_cal_val.pkl"):
        """ Saves phase calibration file."""
        with open(filename, "wb") as file:
            pickle.dump(self.pcal, file)  # save calibrated phase value to a file
            file.close()

    def load_channel_cal(self, filename="channel_cal_val.pkl"):
        """
        Load channel gain compensation values, if not calibrated set all to 0.

        Parameters
        ----------
        filename: string
            Path/name of channel calibration file
        """
        try:
            with open(filename, "rb") as file:
                self.ccal = pickle.load(file)  # Load gain cal values
        except FileNotFoundError:
            print("file not found, loading default (no channel gain compensation)")
            self.ccal = [0.0] * 2

    def load_gain_cal(self, filename="gain_cal_val.pkl"):
        """Load gain calibrated value, if not calibrated set all channel gain to maximum.

        Parameters
        ----------
        filename: type=string
            Provide path of gain calibration file
        """
        try:
            with open(filename, "rb") as file1:
                self.gcal = pickle.load(file1)  # Load gain cal values
        except FileNotFoundError:
            print("file not found, loading default (all gain at maximum)")
            self.gcal = [1.0] * 8  # .append(0x7F)

    def load_phase_cal(self, filename="phase_cal_val.pkl"):
        """Load phase calibrated value, if not calibrated set all channel phase correction to 0.

        Parameters
        ----------
        filename: type=string
            Provide path of phase calibration file
        """
        try:
            with open(filename, "rb") as file:
                self.pcal = pickle.load(file)  # Load gain cal values
        except FileNotFoundError:
            print("file not found, loading default (no phase shift)")
            self.pcal = [0.0] * 8

    def set_rx_hardwaregain(self, gain, apply_cal=True):
        """ Set Pluto channel gains

        Parameters
        ----------
        gain: type=float
            Gain to set both channels to
        apply_cal: type=bool
            Optionally apply channel gain correction
        """
        if apply_cal is True:
            self.sdr.rx_hardwaregain_chan0 = int(gain + self.ccal[0])
            self.sdr.rx_hardwaregain_chan1 = int(gain + self.ccal[1])

        else:
            self.sdr.rx_hardwaregain_chan0 = int(gain)
            self.sdr.rx_hardwaregain_chan1 = int(gain)

    def set_all_gain(self, value=127, apply_cal=True):
        """ Set all channel gains to a single value

        Parameters
        ----------
        value: type=int
            gain for all channels. Default value is 127 (maximum).
        apply_cal: type=bool
            Optionally apply gain calibration to all channels.
        """
        for i in range(0, 8):
            if apply_cal is True:
                self.elements.get(i + 1).rx_gain = int(value * self.gcal[i])
            else:  # Don't apply gain calibration
                self.elements.get(i + 1).rx_gain = value
            # Important if you're relying on elements being truly zero'd out
            self.elements.get(i + 1).rx_attenuator = not bool(value)
        self.latch_tx_settings()  # writes 0x01 to reg 0x28

    def set_chan_gain(self, chan_no: int, gain_val, apply_cal=True):
        """ Setl gain of the individua channel/s.

        Parameters
        ----------
        chan_no: type=int
            It is the index of channel whose gain you want to set
        gain_val: type=int or hex
            gain_val is the value of gain that you want to set
        apply_cal: type=bool
            Optionally apply gain calibration for the selected channel
        """
        if apply_cal is True:
            cval = int(gain_val * self.gcal[chan_no])
            # print(
            #     "Cal = true, setting channel x to gain y, gcal value: ",
            #     chan_no,
            #     ", ",
            #     cval,
            #     ", ",
            #     self.gcal[chan_no],
            # )
            self.elements.get(chan_no + 1).rx_gain = cval
            # print("reading back: ", self.elements.get(chan_no + 1).rx_gain)
        else:  # Don't apply gain calibration
            # print(
            #     "Cal = false, setting channel x to gain y: ",
            #     chan_no,
            #     ", ",
            #     int(gain_val),
            # )
            self.elements.get(chan_no + 1).rx_gain = int(gain_val)
        # Important if you're relying on elements being truly zero'd out
        self.elements.get(chan_no + 1).rx_attenuator = not bool(gain_val)
        self.latch_rx_settings()

    def set_chan_phase(self, chan_no: int, phase_val, apply_cal=True):
        """ Setl phase of the individua channel/s.

        Parameters
        ----------
        chan_no: type=int
            It is the index of channel whose gain you want to set
        phase_val: float
            phase_val is the value of phase that you want to set
        apply_cal: type=bool
            Optionally apply phase calibration

        Notes
        -----
        Each device has 4 channels but for top level channel numbers are 1 to 8 so took device number as Quotient of
        channel num div by 4 and channel of that dev is overall chan num minus 4 x that dev number. For e.g:
        if you want to set gain of channel at index 5 it is 6th channel or 2nd channel of 2nd device so 5//4 = 1
        i.e. index of 2nd device and (5 - 4*(5//4) = 1 i.e. index of channel
        """

        # list(self.devices.values())[chan_no // 4].channels[(chan_no - (4 * (chan_no // 4)))].rx_phase = phase_val
        # list(self.devices.values())[chan_no // 4].latch_rx_settings()
        if apply_cal is True:
            self.elements.get(chan_no + 1).rx_phase = (
                phase_val + self.pcal[chan_no]
            ) % 360.0
        else:  # Don't apply gain calibration
            self.elements.get(chan_no + 1).rx_phase = (phase_val) % 360.0

        self.latch_rx_settings()

    def set_beam_phase_diff(self, Ph_Diff):
        """ Set phase difference between the adjacent channels of devices

        Parameters
        ----------
        Ph-Diff: type=float
                Ph_diff is the phase difference b/w the adjacent channels of devices

        Notes
        -----
        A public method to sweep the phase value from -180 to 180 deg, calculate phase values of all the channel
        and set them. If we want beam angle at fixed angle you can pass angle value at which you want center lobe

        Create an empty list. Based on the device number and channel of that device append phase value to that empty
        list this creates a list of 4 items. Now write channel of each device, phase values acc to created list
        values. This is the structural integrity mentioned above.
        """

        # j = 0  # j is index of device and device indicate the adar1000 on which operation is currently done
        # for device in list(self.devices.values()):  # device in dict of all adar1000 connected
        #     channel_phase_value = []  # channel phase value to be written on ind channel
        #     for ind in range(0, 4):  # ind is index of current channel of current device
        #         channel_phase_value.append((((np.rint(Ph_Diff * ((j * 4) + ind) / self.phase_step_size)) *
        #                                      self.phase_step_size) + self.pcal[((j * 4) + ind)]) % 360)
        #     j += 1
        #     i = 0  # i is index of channel of each device
        #     for channel in device.channels:
        #         # Set phase depending on the device mode
        #         if self.device_mode == "rx":
        #             channel.rx_phase = channel_phase_value[
        #                 i]  # writes to I and Q registers values according to Table 13-16 from datasheet.
        #         i = i + 1
        #     if self.device_mode == "rx":
        #         device.latch_rx_settings()
        #     else:
        #         device.latch_tx_settings()
        #     # print(channel_phase_value)

        for ch in range(0, 8):
            self.elements.get(ch + 1).rx_phase = (
                ((np.rint(Ph_Diff * ch / self.phase_step_size)) * self.phase_step_size)
                + self.pcal[ch]
            ) % 360.0

        self.latch_rx_settings()

    def SDR_init(self, SampleRate, TX_freq, RX_freq, Rx_gain, Tx_gain, buffer_size):
        """ Initialize Pluto rev C for operation with the phaser. This is a convenience
            method that sets several default values, and provides a handle for a few
            other CN0566 methods that need access (i.e. set_rx_hardwaregain())

        parameters
        ----------
        SampleRate: type=int
            ADC/DAC sample rate.
        TX_freq: type=float
            Transmit frequency. lo-sdr.TX_freq is what shows up at the TX connector.
        RX_freq: type=float
            Receive frequency. lo-sdr.RX_freq is what shows up at RX outputs.
        Rx_gain: type=float
            Receive gain. Set indirectly via set_rx_hardwaregain()
        Tx_gain: type=float
            Transmit gain, controls TX output amplitude.
        buffer_size: type=int
            Receive buffer size
        """
        self.sdr._ctrl.debug_attrs[
            "adi,frequency-division-duplex-mode-enable"
        ].value = "1"  # set to fdd mode
        self.sdr._ctrl.debug_attrs[
            "adi,ensm-enable-txnrx-control-enable"
        ].value = "0"  # Disable pin control so spi can move the states
        self.sdr._ctrl.debug_attrs["initialize"].value = "1"
        self.sdr.rx_enabled_channels = [
            0,
            1,
        ]  # enable Rx1 (voltage0) and Rx2 (voltage1)
        self.sdr.gain_control_mode_chan0 = "manual"  # We must be in manual gain control mode (otherwise we won't see the peaks and nulls!)
        self.sdr.gain_control_mode_chan1 = "manual"  # We must be in manual gain control mode (otherwise we won't see the peaks and nulls!)
        self.sdr._rxadc.set_kernel_buffers_count(
            1
        )  # Default is 4 Rx buffers are stored, but we want to change and immediately measure the result, so buffers=1
        rx = self.sdr._ctrl.find_channel("voltage0")
        rx.attrs[
            "quadrature_tracking_en"
        ].value = "1"  # set to '1' to enable quadrature tracking
        self.sdr.sample_rate = int(SampleRate)
        self.sdr.rx_lo = int(RX_freq)
        self.sdr.rx_buffer_size = int(
            buffer_size
        )  # small buffers make the scan faster -- and we're primarily just looking at peak power
        self.sdr.tx_lo = int(TX_freq)
        self.sdr.tx_cyclic_buffer = True
        self.sdr.tx_hardwaregain_chan0 = int(-88)  # turn off Tx1
        self.sdr.tx_hardwaregain_chan1 = int(Tx_gain)
        self.sdr.rx_hardwaregain_chan0 = int(Rx_gain)
        self.sdr.rx_hardwaregain_chan1 = int(Rx_gain)
        self.sdr.filter = (
            "LTE20_MHz.ftr"  # Handy filter for fairly widdeband measurements
        )
        # sdr.filter = "/usr/local/lib/osc/filters/LTE5_MHz.ftr"
        # sdr.rx_rf_bandwidth = int(SampleRate*2)
        # sdr.tx_rf_bandwidth = int(SampleRate*2)
        signal_freq = int(SampleRate / 8)
        if (
            True
        ):  # use either DDS or sdr.tx(iq) to generate the Tx waveform.  But don't do both!
            self.sdr.dds_enabled = [
                1,
                1,
                1,
                1,
                1,
                1,
                1,
                1,
            ]  # DDS generator enable state
            self.sdr.dds_frequencies = [
                signal_freq,
                0,
                signal_freq,
                0,
                signal_freq,
                0,
                signal_freq,
                0,
            ]  # Frequencies of DDSs in Hz
            self.sdr.dds_scales = [
                0.5,
                0,
                0.5,
                0,
                0.9,
                0,
                0.9,
                0,
            ]  # Scale of DDS signal generators Ranges [0,1]
        else:
            fs = int(SampleRate)
            N = 1000
            fc = int(signal_freq / (fs / N)) * (fs / N)
            ts = 1 / float(fs)
            t = np.arange(0, N * ts, ts)
            i = np.cos(2 * np.pi * t * fc) * 2 ** 15
            q = np.sin(2 * np.pi * t * fc) * 2 ** 15
            iq = 0.9 * (i + 1j * q)
            self.sdr.tx([iq, iq])
