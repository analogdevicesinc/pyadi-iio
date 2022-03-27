# Copyright (C) 2021 Analog Devices, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     - Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     - Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.
#     - Neither the name of Analog Devices, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#     - The use of this software may or may not infringe the patent rights
#       of one or more patent holders.  This license does not release you
#       from the requirement that you obtain separate licenses from these
#       patent holders to use this software.
#     - Use of the software either in source or binary form, must be run
#       on or directly connected to an Analog Devices Inc. component.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT, MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.
#
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, INTELLECTUAL PROPERTY
# RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import pickle
from statistics import mean
from time import sleep

import adi
import numpy as np
from adi.adar1000 import adar1000_array
from adi.adf4159 import adf4159


def to_sup(angle):
    if angle > 180.0:
        angle -= 360.0
    return angle


class CN0566(adf4159, adar1000_array):
    """ CN0566 class inherits from adar1000_array and adf4159 and adds
        operations for beamforming like default configuration,
        calibration, set_beam_phase_diff, etc.
        gpios (as one-bit-adc-dac) are instantiated internally.
        """

    # MWT: Still up for debate - inheret, or nest? Nesting may actually be easier to understand.
    def __init__(
        self,
        uri=None,
        rx_dev=None,
        chip_ids=["BEAM0", "BEAM1"],
        device_map=[[1], [2]],
        element_map=[[1, 2, 3, 4, 5, 6, 7, 8]],  # [[1, 2, 3, 4], [5, 6, 7, 8]],
        device_element_map={
            1: [7, 8, 5, 6],  # i.e. channel2 of device1 (BEAM0), maps to element 8
            2: [3, 4, 1, 2],
        },
        verbose=False,
    ):
        if verbose is True:
            print("attempting to open ADF4159, uri: ", str(uri))
        adf4159.__init__(self, uri)

        if verbose is True:
            print("attempting to open ADAR1000 array, uri: ", str(uri))
        adar1000_array.__init__(
            self, uri, chip_ids, device_map, element_map, device_element_map
        )

        if verbose is True:
            print("attempting to open gpios , uri: ", str(uri))
        sleep(0.5)
        self.gpios = adi.one_bit_adc_dac(uri)

        if verbose is True:
            print("attempting to open AD7291 v/t monitor, uri: ", str(uri))
        sleep(0.5)
        self.monitor = adi.ad7291(uri)

        """ Initialize all the class variables for the project. """
        self.num_elements = 8  # eq. to 4 * len(list(self.devices.values()))
        self.device_mode = "rx"  # Default to RX.
        self.SignalFreq = 10492000000  # Frequency of source
        self.Averages = 16  # Number of Avg to be taken.
        self.phase_step_size = (
            2.8125  # it is 360/2**number of bits. (number of bits = 6)
        )
        self.steer_res = (
            2.8125  # It is steering resolution. This would be user selected value
        )
        self.c = 299792458  # speed of light in m/s
        self.element_spacing = (
            0.015  # element to element spacing of the antenna in meters
        )
        self.res_bits = 1  # res_bits and bits are two different var. It can be variable, but it is hardset to 1 for now
        self.pcal = [
            0.0 for i in range(0, (self.num_elements))
        ]  # default phase cal value i.e 0
        self.gcal = [
            1.0 for i in range(0, self.num_elements)
        ]  # default gain cal value i.e 127
        self.ph_deltas = [
            0 for i in range(0, (self.num_elements) - 1)
        ]  # Phase delta between elements
        self.rx_dev = rx_dev  # rx_device/sdr that rx and plots
        self.gain_cal = False  # gain/phase calibration status flag it goes True when performing calibration
        self.phase_cal = False
        # Scaling factors for voltage AD7291 monitor
        self.v0_vdd1v8_scale = 1.0 + (10.0 / 10.0)
        self.v1_vdd3v0_scale = 1.0 + (10.0 / 10.0)
        self.v2_vdd3v3_scale = 1.0 + (10.0 / 10.0)
        self.v3_vdd4v5_scale = 1.0 + (30.1 / 10.0)
        self.v4_vdd_amp_scale = 1.0 + (69.8 / 10.0)
        self.v5_vinput_scale = 1.0 + (30.1 / 10.0)
        self.v6_imon_scale = 10.0  # double check scaling, this is in mA
        self.v7_vtune_scale = 1.0 + (69.8 / 10.0)

        # set outputs
        self.gpios.gpio_vctrl_1 = 1  # Onboard PLL/LO source
        self.gpios.gpio_vctrl_2 = 1  # Send LO to TX circuitry

        self.gpios.gpio_div_mr = 0  # TX switch toggler divider reset
        self.gpios.gpio_div_s0 = 0  # TX toggle divider lsb (1s)
        self.gpios.gpio_div_s1 = 0  # TX toggle divider 2s
        self.gpios.gpio_div_s2 = 0  # TX toggle divider 4s
        self.gpios.gpio_rx_load = 0  # ADAR1000 RX load (cycle through RAM table)
        self.gpios.gpio_tr = 0  # ADAR1000 transmit / recieve mode. RX = 0 (assuming)
        self.gpios.gpio_tx_sw = (
            0  # Direct control of TX switch when div=[000]. 0 = J1, 1 = J2
        )
        # Read input
        muxout = self.gpios.gpio_muxout  # PLL MUXOUT, assign to PLL lock in the future

    def read_monitor(self, verbose=False):
        """ Read all voltage / temperature monitor channels.
            parameters:
                    verbose: type=bool
                              Print each channel's information if true.
            returns:
                An array of all readings in SI units (deg. C, Volts)
        """
        board_temperature = (
            self.monitor.channel[0].raw * self.monitor.channel[0].scale / 1000.0
        )  # convert from millidegrees
        v0_vdd1v8 = (
            self.monitor.channel[1].raw
            * self.monitor.channel[1].scale
            * self.v0_vdd1v8_scale
            / 1000.0
        )
        v1_vdd3v0 = (
            self.monitor.channel[2].raw
            * self.monitor.channel[2].scale
            * self.v1_vdd3v0_scale
            / 1000.0
        )
        v2_vdd3v3 = (
            self.monitor.channel[3].raw
            * self.monitor.channel[3].scale
            * self.v2_vdd3v3_scale
            / 1000.0
        )
        v3_vdd4v5 = (
            self.monitor.channel[4].raw
            * self.monitor.channel[4].scale
            * self.v3_vdd4v5_scale
            / 1000.0
        )
        v4_vdd_amp = (
            self.monitor.channel[5].raw
            * self.monitor.channel[5].scale
            * self.v4_vdd_amp_scale
            / 1000.0
        )
        v5_vinput = (
            self.monitor.channel[6].raw
            * self.monitor.channel[6].scale
            * self.v5_vinput_scale
            / 1000.0
        )
        v6_imon = (
            self.monitor.channel[7].raw
            * self.monitor.channel[7].scale
            * self.v6_imon_scale
            / 1000.0
        )
        v7_vtune = (
            self.monitor.channel[8].raw
            * self.monitor.channel[8].scale
            * self.v7_vtune_scale
            / 1000.0
        )
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
            v4_vdd_amp,
            v5_vinput,
            v6_imon,
            v7_vtune,
        ]

    def configure(self, device_mode="rx"):
        """ Configure the device/beamformer properties like RAM bypass, Tr source etc.
            parameters:
                device_mode: type=string
                ("rx", "tx", "disabled", default = "rx")
        """

        self.device_mode = device_mode
        for device in self.devices.values():  # For device in Dict of device array
            # Configure ADAR1000
            # adar.initialize_devices()  # Always Intialize the device 1st as reset is performed at Initialization
            # If ADAR1000 array is used initialization work otherwise reset each adar individually
            device.reset()  # Performs a soft reset of the device (writes 0x81 to reg 0x00)
            device._ctrl.reg_write(
                0x400, 0x55
            )  # This trims the LDO value to approx. 1.8V (to the center of its range)
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

    def load_gain_cal(self, filename="gain_cal_val.pkl"):
        """ Load gain calibrated value, if not calibrated set all channel gain to maximum.
            parameters:
                filename: type=string
                          Provide path of gain calibration file
        """
        try:
            with open(filename, "rb") as file1:
                self.gcal = pickle.load(file1)  # Load gain cal values
        except Exception:
            print("file not found, loading default (all gain at maximum)")
            self.gcal = [1.0] * 8  # .append(0x7F)

    def load_phase_cal(self, filename="phase_cal_val.pkl"):
        """ Load phase calibrated value, if not calibrated set all channel phase correction to 0.
            parameters:
                filename: type=string
                          Provide path of phase calibration file
        """
        try:
            with open(filename, "rb") as file:
                self.pcal = pickle.load(file)  # Load gain cal values
        except Exception:
            print("file not found, loading default (no phase shift)")
            self.pcal = [
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ]

    def set_all_gain(self, value=127, apply_cal=True):
        """ This will try to set gain of all the channels
            parameters:
                    value: type=int
                              Value is the value of gain that you want to set for all the channel
                              It is optional and it's default value is 127.
        """
        for i in range(0, 8):
            if apply_cal is True:
                self.elements.get(i + 1).rx_gain = int(value * self.gcal[i])
            else:  # Don't apply gain calibration
                self.elements.get(i + 1).rx_gain = value
            self.elements.get(i + 1).rx_attenuator = not bool(value)
        self.latch_tx_settings()  # writes 0x01 to reg 0x28

    def set_chan_gain(self, chan_no: int, gain_val, apply_cal=True):
        """ Setl gain of the individua channel/s.
            parameters:
                    chan_no: type=int
                              It is the index of channel whose gain you want to set
                    gain_val: type=int or hex
                              gain_val is the value of gain that you want to set
        """

        if apply_cal is True:
            print(
                "Cal = true, setting channel x to gain y, gcal value: ",
                chan_no,
                ", ",
                int(gain_val * self.gcal[chan_no]),
                ", ",
                self.gcal[chan_no],
            )
            #                list(self.devices.values())[chan_no // 4].channels[(chan_no - (4 * (chan_no // 4)))].rx_gain = int(gain_val * self.gcal[chan_no])
            self.elements.get(chan_no + 1).rx_gain = int(gain_val * self.gcal[chan_no])
        else:  # Don't apply gain calibration
            print(
                "Cal = false, setting channel x to gain y: ",
                chan_no,
                ", ",
                int(gain_val),
            )
            #                list(self.devices.values())[chan_no // 4].channels[(chan_no - (4 * (chan_no // 4)))].rx_gain = int(gain_val)
            self.elements.get(chan_no + 1).rx_gain = int(gain_val)
        #            list(self.devices.values())[chan_no // 4].latch_rx_settings()
        self.latch_rx_settings()

    def set_chan_phase(self, chan_no: int, phase_val, apply_cal=True):
        """ Setl phase of the individua channel/s.
            parameters:
                    chan_no: type=int
                              It is the index of channel whose gain you want to set
                    phase_val: float
                              phase_val is the value of phase that you want to set
        """

        """Each device has 4 channels but for top level channel numbers are 1 to 8 so took device number as Quotient of
           channel num div by 4 and channel of that dev is overall chan num minus 4 x that dev number. For e.g:
           if you want to set gain of channel at index 5 it is 6th channel or 2nd channel of 2nd device so 5//4 = 1
           i.e. index of 2nd device and (5 - 4*(5//4) = 1 i.e. index of channel"""

        # list(self.devices.values())[chan_no // 4].channels[(chan_no - (4 * (chan_no // 4)))].rx_phase = phase_val
        # list(self.devices.values())[chan_no // 4].latch_rx_settings()
        if apply_cal is True:
            self.elements.get(chan_no + 1).rx_phase = (
                phase_val + self.pcal[chan_no]
            ) % 360
        else:  # Don't apply gain calibration
            self.elements.get(chan_no + 1).rx_phase = (phase_val) % 360

        self.latch_rx_settings()

    def set_beam_phase_diff(self, Ph_Diff):
        """ Set phase difference between the adjacent channels of devices
            parameters:
                Ph-Diff: type=float
                            Ph_diff is the phase difference b/w the adjacent channels of devices
        """

        """ A public method to sweep the phase value from -180 to 180 deg, calculate phase values of all the channel
            and set them. If we want beam angle at fixed angle you can pass angle value at which you want center lobe

            Create an empty list. Based on the device number and channel of that device append phase value to that empty
            list this creates a list of 4 items. Now write channel of each device, phase values acc to created list
            values. This is the structural integrity mentioned above."""

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
            ) % 360

        self.latch_rx_settings()

    def calculate_plot(self, gcal_element=0, cal_element=0):
        """ Calculate all the values required to do different plots. It method calls set_beam_phase_diff and
            sets the Phases of all channel. All the math is done here.
            parameters:
                gcal_element: type=int
                            If gain calibration is taking place, it indicates element number whose gain calibration is
                            is currently taking place
                cal_element: type=int
                            If Phase calibration is taking place, it indicates element number whose phase calibration is
                            is currently taking place
        """

        sweep_angle = 180  # This swweps from -70 deg to +70
        # These are all the phase deltas (i.e. phase difference between Rx1 and Rx2, then Rx2 and Rx3, etc.) we'll sweep
        PhaseValues = np.arange(-(sweep_angle), (sweep_angle), self.phase_step_size)
        max_signal = (
            -100000
        )  # Reset max_signal.  We'll keep track of the maximum signal we get as we do this 140 loop.
        max_angle = (
            -90
        )  # Reset max_angle. This is the angle where we saw the max signal.
        gain, delta, beam_phase, angle, diff_error = (
            [],
            [],
            [],
            [],
            [],
        )  # Create empty lists
        NumSamples = self.rx_dev.rx_buffer_size
        win = np.blackman(NumSamples)

        for PhDelta in PhaseValues:  # These sweeps phase value from -180 to 180
            # set Phase of channels based on Calibration Flag status and calibration element

            self.set_beam_phase_diff(PhDelta)
            # arcsin argument must be between 1 and -1, or numpy will throw a warning
            if PhDelta >= 0:
                SteerAngle = np.degrees(
                    np.arcsin(
                        max(
                            min(
                                1,
                                (self.c * np.radians(np.abs(PhDelta)))
                                / (2 * np.pi * self.SignalFreq * self.element_spacing),
                            ),
                            -1,
                        )
                    )
                )  # positive PhaseDelta covers 0deg to 90 deg
            else:
                SteerAngle = -(
                    np.degrees(
                        np.arcsin(
                            max(
                                min(
                                    1,
                                    (self.c * np.radians(np.abs(PhDelta)))
                                    / (
                                        2
                                        * np.pi
                                        * self.SignalFreq
                                        * self.element_spacing
                                    ),
                                ),
                                -1,
                            )
                        )
                    )
                )  # negative phase delta covers 0 deg to -90 deg

            total_sum, total_delta, total_angle = 0, 0, 0

            for count in range(0, self.Averages):  # repeat loop and average the results
                data = (
                    self.rx_dev.rx()
                )  # read a buffer of data from Pluto using pyadi-iio library (adi.py)
                y_sum = (data[0] + data[1]) * win
                y_delta = (data[0] - data[1]) * win
                s_sum = np.fft.fftshift(np.absolute(np.fft.fft(y_sum))[1:-1])
                s_delta = np.fft.fftshift(np.absolute(np.fft.fft(y_delta))[1:-1])
                total_angle = total_angle + (
                    np.angle(s_sum[np.argmax(s_sum)])
                    - np.angle(s_delta[np.argmax(s_sum)])
                )
                s_mag_sum = np.maximum(
                    np.abs(s_sum[np.argmax(s_sum)]) * 2 / np.sum(win), 10 ** (-15)
                )  # Prevent taking log of zero
                s_mag_delta = np.maximum(
                    np.abs(s_delta[np.argmax(s_sum)]) * 2 / np.sum(win), 10 ** (-15)
                )
                total_sum = total_sum + (
                    20 * np.log10(s_mag_sum / (2 ** 12))
                )  # sum up all the loops, then we'll avg
                total_delta = total_delta + (20 * np.log10(s_mag_delta / (2 ** 12)))

            PeakValue_sum = total_sum / self.Averages
            PeakValue_delta = total_delta / self.Averages
            PeakValue_angle = total_angle / self.Averages

            if np.sign(PeakValue_angle) == -1:
                target_error = min(
                    -0.01,
                    (
                        np.sign(PeakValue_angle) * (PeakValue_sum - PeakValue_delta)
                        + np.sign(PeakValue_angle)
                        * (PeakValue_sum + PeakValue_delta)
                        / 2
                    )
                    / (PeakValue_sum + PeakValue_delta),
                )
            else:
                target_error = max(
                    0.01,
                    (
                        np.sign(PeakValue_angle) * (PeakValue_sum - PeakValue_delta)
                        + np.sign(PeakValue_angle)
                        * (PeakValue_sum + PeakValue_delta)
                        / 2
                    )
                    / (PeakValue_sum + PeakValue_delta),
                )

            if (
                PeakValue_sum > max_signal
            ):  # take the largest value, so that we know where to point the compass
                max_signal = PeakValue_sum
                max_angle = PeakValue_angle
                max_PhDelta = PhDelta
                data_fft = data[0] + data[1]
            gain.append(PeakValue_sum)
            delta.append(PeakValue_delta)
            beam_phase.append(PeakValue_angle)
            angle.append(SteerAngle)
            diff_error.append(target_error)

        y = data_fft * win
        sp = np.absolute(np.fft.fft(y))
        sp = sp[1:-1]
        sp = np.fft.fftshift(sp)
        s_mag = (
            np.abs(sp) * 2 / np.sum(win)
        )  # Scale FFT by window and /2 since we are using half the FFT spectrum
        s_mag = np.maximum(s_mag, 10 ** (-15))
        max_gain = 20 * np.log10(
            s_mag / (2 ** 12)
        )  # Pluto is a 12 bit ADC, so use that to convert to dBFS
        ts = 1 / float(self.rx_dev.sample_rate)
        xf = np.fft.fftfreq(NumSamples, ts)
        xf = np.fft.fftshift(
            xf[1:-1]
        )  # this is the x axis (freq in Hz) for our fft plot
        # Return values/ parameter based on Calibration Flag status

        if self.gain_cal:
            return mean(gain)
        # if self.phase_cal:
        #     return PhaseValues[gain.index(min(gain))]
        else:  # if not self.gain_cal and not self.phase_cal:
            return gain, angle, delta, diff_error, beam_phase, xf, max_gain, PhaseValues

    def gain_calibration(self, verbose=False):
        """ Perform the Gain Calibration routine."""

        """Set the gain calibration flag and create an empty gcal list. Looping through all the possibility i.e. setting
            gain of one of the channel to max and all other to 0 create a zero-list where number of 0's depend on total
            channels. Replace only 1 element with max gain at a time. Now set gain values according to above Note."""

        self.gain_cal = True  # Gain Calibration Flag
        gcalibrated_values = []  # Intermediate cal values list
        plot_data = []
        # gcal_element indicates current element/channel which is being calibrated
        for gcal_element in range(0, (self.num_elements)):
            if verbose is True:
                print("Calibrating Element " + str(gcal_element))

            gcal_val, spectrum = self.measure_element_gain(gcal_element, verbose=True)
            print("Measured element gain: ", gcal_val)
            if verbose is True:
                print("Element gain: " + str(gcal_val))
            gcalibrated_values.append(
                gcal_val
            )  # make a list of intermediate cal values
            plot_data.append(spectrum)

        """ Minimum gain of intermediated cal val is set to Maximum value as we cannot go beyond max value and gain
            of all other channels are set accordingly"""
        print("gcalibrated values: ", gcalibrated_values)
        for k in range(0, 8):
            #            x = ((gcalibrated_values[k] * 127) / (min(gcalibrated_values)))
            x = (gcalibrated_values[k]) / (min(gcalibrated_values))
            self.gcal[k] = x  # append final calibrated value to gcal list

        #        self.save_gain_cal()  # save the gcal list
        self.gain_cal = (
            False  # Reset the Gain calibration Flag once system gain is calibrated
        )
        return plot_data
        # print(self.gcal)

    def measure_element_gain(self, cal, verbose=False):  # Default to central element
        """ Calculate all the values required to do different plots. It method calls set_beam_phase_diff and
            sets the Phases of all channel. All the math is done here.
            parameters:
                gcal_element: type=int
                            If gain calibration is taking place, it indicates element number whose gain calibration is
                            is currently taking place
                cal_element: type=int
                            If Phase calibration is taking place, it indicates element number whose phase calibration is
                            is currently taking place
        """
        self.set_all_gain(0, apply_cal=False)  # Start with all gains set to zero
        self.set_chan_gain(
            cal, 127, apply_cal=False
        )  # Set element being measured to maximum
        if verbose:
            print("measuring element: ", cal)
        total_sum = 0
        win = np.blackman(self.rx_dev.rx_buffer_size)
        spectrum = np.zeros(self.rx_dev.rx_buffer_size - 2)
        for count in range(0, self.Averages):  # repeat loop and average the results
            self.rx_dev.rx()
            data = self.rx_dev.rx()  # read a buffer of data
            y_sum = (data[0] + data[1]) * win

            s_sum = np.fft.fftshift(np.absolute(np.fft.fft(y_sum))[1:-1])
            spectrum += s_sum

            s_mag_sum = np.maximum(
                np.abs(s_sum[np.argmax(s_sum)]) * 2 / np.sum(win), 10 ** (-15)
            )  # Prevent taking log of zero
            total_sum = total_sum + (
                20 * np.log10(s_mag_sum / (2 ** 12))
            )  # sum up all the loops, then we'll avg
        spectrum /= self.Averages
        PeakValue_sum = total_sum / self.Averages

        return PeakValue_sum, spectrum

    def phase_calibration(self, verbose=False):
        """ Perfome the Phase Calibration routine."""

        """ Set the phase calibration flag and create an empty pcal list. Looping through all the possibility
            i.e. setting gain of two adjacent channels to gain calibrated values and all other to 0 create a zero-list
            where number of 0's depend on total channels. Replace gain value of 2 adjacent channel.
            Now set gain values according to above Note."""

        #        self.phase_cal = True  # Gain Calibration Flag
        #        self.load_gain_cal('gain_cal_val.pkl')  # Load gain cal val as phase cal is dependent on gain cal
        self.pcal = [0, 0, 0, 0, 0, 0, 0, 0]
        self.ph_deltas = [0, 0, 0, 0, 0, 0, 0]
        plot_data = []
        # cal_element indicates current element/channel which is being calibrated
        # As there are 8 channels and we take two adjacent chans for calibration we have 7 cal_elements
        for cal_element in range(0, 7):
            if verbose is True:
                print("Calibrating Element " + str(cal_element))
            self.set_all_gain(0)  # Reset all elements to zero
            self.set_chan_gain(cal_element, 127)  # Set two adjacent elements to zero
            self.set_chan_gain(cal_element + 1, 127)
            # beam_cal = [0 for i in range(0, (self.num_elements))]  # set all gain to 0
            # # Only set th gain of current & it's adjacent element/channel to gain calibrated values
            # beam_cal[cal_element] = self.gcal[cal_element]
            # beam_cal[(cal_element + 1)] = self.gcal[(cal_element + 1)]

            PhaseValues, gain, beam_phase, max_gain = self.phase_cal_sweep(
                cal_element, cal_element + 1
            )

            ph_delta = to_sup((180 - PhaseValues[gain.index(min(gain))]) % 360.0)
            if verbose is True:
                print("Null found at ", PhaseValues[gain.index(min(gain))])
                print("Phase Delta to correct: ", ph_delta)
            self.ph_deltas[cal_element] = ph_delta

            self.pcal[cal_element + 1] = to_sup(
                (self.pcal[cal_element] - ph_delta) % 360.0
            )
            plot_data.append(gain)
        return PhaseValues, plot_data

    def phase_cal_sweep(self, ref=0, cal=1):
        """ Calculate all the values required to do different plots. It method calls set_beam_phase_diff and
            sets the Phases of all channel. All the math is done here.
            parameters:
                gcal_element: type=int
                            If gain calibration is taking place, it indicates element number whose gain calibration is
                            is currently taking place
                cal_element: type=int
                            If Phase calibration is taking place, it indicates element number whose phase calibration is
                            is currently taking place
        """

        self.set_chan_phase(ref, 0.0, apply_cal=False)  # Reference element

        sweep_angle = 180  # This swweps from -70 deg to +70
        # These are all the phase deltas (i.e. phase difference between Rx1 and Rx2, then Rx2 and Rx3, etc.) we'll sweep
        PhaseValues = np.arange(-(sweep_angle), (sweep_angle), self.phase_step_size)

        max_signal = (
            -100000
        )  # Reset max_signal.  We'll keep track of the maximum signal we get as we do this 140 loop.
        max_angle = (
            -90
        )  # Reset max_angle. This is the angle where we saw the max signal.
        gain, beam_phase = [], []  # Create empty lists
        for phase in PhaseValues:  # These sweeps phase value from -180 to 180
            # set Phase of channels based on Calibration Flag status and calibration element
            self.set_chan_phase(cal, phase, apply_cal=False)

            total_sum, total_angle = 0, 0
            win = np.blackman(self.rx_dev.rx_buffer_size)
            for count in range(0, self.Averages):  # repeat loop and average the results
                data = self.rx_dev.rx()  # read a buffer of data
                y_sum = (data[0] + data[1]) * win
                y_delta = (data[0] - data[1]) * win
                s_sum = np.fft.fftshift(np.absolute(np.fft.fft(y_sum))[1:-1])
                s_delta = np.fft.fftshift(np.absolute(np.fft.fft(y_delta))[1:-1])
                total_angle = total_angle + (
                    np.angle(s_sum[np.argmax(s_sum)])
                    - np.angle(s_delta[np.argmax(s_sum)])
                )
                s_mag_sum = np.maximum(
                    np.abs(s_sum[np.argmax(s_sum)]) * 2 / np.sum(win), 10 ** (-15)
                )  # Prevent taking log of zero
                total_sum = total_sum + (
                    20 * np.log10(s_mag_sum / (2 ** 12))
                )  # sum up all the loops, then we'll avg

            PeakValue_sum = total_sum / self.Averages
            PeakValue_angle = total_angle / self.Averages

            if (
                PeakValue_sum > max_signal
            ):  # take the largest value, so that we know where to point the compass
                max_signal = PeakValue_sum
                data_fft = data[0] + data[1]
            gain.append(PeakValue_sum)
            beam_phase.append(PeakValue_angle)

        NumSamples = len(data_fft)  # number of samples
        win = np.blackman(NumSamples)
        y = data_fft * win
        sp = np.absolute(np.fft.fft(y))
        sp = sp[1:-1]
        sp = np.fft.fftshift(sp)
        s_mag = (
            np.abs(sp) * 2 / np.sum(win)
        )  # Scale FFT by window and /2 since we are using half the FFT spectrum
        s_mag = np.maximum(s_mag, 10 ** (-15))
        max_gain = 20 * np.log10(
            s_mag / (2 ** 12)
        )  # Pluto is a 12 bit ADC, so use that to convert to dBFS

        return PhaseValues, gain, beam_phase, max_gain

    # def plot(self, plot_type: str):
    #     """ Plot the graph accoeding to Demo.
    #         parameters:
    #             plot_type: type=str
    #                 fft plots fft at peak-angle
    #                 monopulse plots output of monopulse tracking
    #                 polar plots polar plot
    #     """
    #     """ Gain plots sum_chan. Delta plots the difference and Error plots the diff of sum & delta chans."""
    #     gain, angle, delta, diff_error, beam_phase, xf, max_gain, calculate_plot = self.calculate_plot()
    #     if plot_type == "fft":
    #        return xf / 1e6, max_gain
    #     elif plot_type == "monopulse":
    #         print(angle[gain.index(max(gain))])
    #         return gain, angle
