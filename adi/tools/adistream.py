# Copyright (C) 2023-2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import argparse
import sys
from time import sleep

import adi
import numpy as np
from genalyzer import WaveformGen
from pynput import keyboard


class ADIStream(object):
    """ ADIStream Class for DACs"""

    def __init__(
        self,
        classname,
        uri,
        v_ref_n,
        v_ref_p,
        npts,
        chn_list,
        v_req_l,
        v_req_u,
        out_freq,
        code_sel,
        wave_list,
        device_name,
        duty_cycle,
        channel_order,
    ):
        """Constructor for ADIStream Class

        :param classname: class name to stream data to
        :param uri: uri of the target device
        :param v_ref_n: negative reference voltage in volts
        :param v_ref_p: positive reference voltage in volts
        :param npts: number of data points required per wave
        :param chn_list: channels list to stream data to
        :param v_req_l: lower end Voltage required in volts
        :param v_req_u: upper end Voltage required in volts
        :param out_freq: output frequency in Hz
        :param code_sel: code select to stream data in
        :param wave_list: list of waveform type required
        :param device_name: part name if the class supports more than 1 generic
        :param duty_cycle: duty cycle in percent for pwm wave
        :param channel_order: channel wise data order streamed to the DAC"""

        self.sampling_freq = None
        self.data = []
        self.data_stream_abort = False
        self.classname = classname
        self.npts = npts
        self.v_ref_n = v_ref_n
        self.v_ref_p = v_ref_p
        self.v_req_l = v_req_l
        self.v_req_u = v_req_u
        self.out_freq = out_freq
        self.code_sel = code_sel
        self.duty_cyc = duty_cycle
        self.channel_order = channel_order

        self.stream = eval(
            "adi."
            + classname
            + "(uri='"
            + uri
            + "', device_name='"
            + device_name
            + "')"
        )
        self.stream.tx_cyclic_buffer = True
        self.wave_list = wave_list
        self.stream._ctx.set_timeout(100000)

        # Sort channels list
        chn_list.sort()

        # Get channel id and set enabled channels
        self.chan_list = []
        ch_name = self.stream.ctx.devices[0].channels[0].id
        ch_name = ch_name[:-1]
        for val in chn_list:
            self.chan_list += [ch_name + str(val)]
        self.stream.tx_enabled_channels = self.chan_list
        self.chn_cnt = len(chn_list)

        # assign sine waveform as the default waveform type for channels with no waveform type provided
        wave_cnt = len(self.wave_list)
        while self.chn_cnt - wave_cnt:
            self.wave_list[wave_cnt] = "sine"
            wave_cnt += 1

        # get the device resolution
        try:
            self.resolution = self.stream.output_bits[0]
        except AttributeError:
            self.resolution = self.stream.ctx.devices[0].channels[0].data_format.bits

        if "sampling_frequency" in self.stream.ctx.devices[0].attrs.keys():
            self.sampling_freq = self.stream._get_iio_dev_attr("sampling_frequency")
        else:
            raise Exception("No attribute with name sampling_frequency found")

        if self.out_freq is None:
            self.out_freq = self.sampling_freq / self.npts
        else:
            self.stream.sampling_frequency = self.out_freq * self.npts
            self.sampling_freq = int(self.stream.sampling_frequency)

        if self.v_req_l is None:
            self.v_req_l = self.v_ref_n

        if self.v_req_u is None:
            self.v_req_u = self.v_ref_p

    def write_buffered_data(self):
        # Send data from device
        if self.channel_order == "desc":
            # Stream the numpy array of channels data in descending order
            self.data = self.data[::-1]
        self.stream.tx(self.data)
        print("Data streaming started")

    def get_data(self):
        if self.out_freq > self.sampling_freq / self.npts:
            print(
                f"The nearest possible output frequency that can be generated "
                f"with the current config is {self.sampling_freq / self.npts} Hz"
            )
            self.out_freq = self.sampling_freq / self.npts
        elif self.out_freq < self.sampling_freq / self.npts:
            print(
                "Actual generated output frequency: ",
                str(int(self.sampling_freq) // self.npts),
            )

        gen_obj = WaveformGen(  # noqa: F841 ,variable is being used in the eval function below
            self.npts,
            self.out_freq,
            self.code_sel,
            self.resolution,
            self.v_ref_n,
            self.v_ref_p,
            self.v_req_l,
            self.v_req_u,
        )

        # get data using the genalyzer apis
        for val in range(self.chn_cnt):
            if self.chn_cnt == 1:
                if self.wave_list[val] == "pwm":
                    self.data = eval(
                        "gen_obj.gen_pwm_wave(duty_cycle = "
                        + str(self.duty_cyc / 100)
                        + ")"
                    )
                else:
                    self.data = eval("gen_obj.gen_" + self.wave_list[val] + "_wave()")
            else:
                if self.wave_list[val] == "pwm":
                    self.data.append(
                        eval(
                            "gen_obj.gen_pwm_wave(duty_cycle = "
                            + str(self.duty_cyc / 100)
                            + ")"
                        )
                    )
                else:
                    self.data.append(
                        eval("gen_obj.gen_" + self.wave_list[val] + "_wave()")
                    )

        self.data = np.array(self.data)

    def key_press_event(self, key):
        if key == keyboard.Key.esc:
            self.data_stream_abort = True

    def do_data_streaming(self):
        self.get_data()

        listener = keyboard.Listener(on_press=self.key_press_event)
        listener.start()

        print("Press " "escape" " key to stop cyclic data streaming..")
        sleep(2)

        self.write_buffered_data()

        while not self.data_stream_abort:
            # This should halt the control for the cyclic mode to work
            pass

        self.exit_data_streaming()

    def exit_data_streaming(self):
        self.stream.tx_destroy_buffer()
        self.stream._ctx.__del__()
        print("\r\nData streaming finished")


def run_adi_stream(argv=None, test_flag=False):
    parser = argparse.ArgumentParser(
        description="ADI data streaming app",
        formatter_class=argparse.RawTextHelpFormatter,
        usage="\nFor help, \n\t python adistream.py -h"
        "\nTo go with default configurations, provide the positional arguments"
        "\n\t python adistream.py  ad579x serial:COM13,230400 -10 10"
        "\nTo use available options,"
        "\nThe following command will generate a square wave at 1KHz"
        "\n\t python adistream.py  ad3530r serial:COM13,230400 0 2.5 -w square -f 1000"
        "\nThe following command will stream data to channels 0, 1, and 2"
        "\n\t python adistream.py ad3530r serial:COM13,230400 0 2.5 -cl 0 1 2",
    )
    parser.add_argument(
        "class", help="pyadi class name to stream data to", action="store"
    )
    parser.add_argument("uri", help="URI of target device", action="store")
    parser.add_argument(
        "neg_voltage_ref",
        help="Negative reference voltage of DAC in volts. \nInput 0 for unipolar DACs",
        action="store",
        type=float,
    )
    parser.add_argument(
        "pos_voltage_ref",
        help="Positive reference voltage of DAC in volts.",
        action="store",
        type=float,
    )
    parser.add_argument(
        "-d",
        "--device_name",
        help="Part name if the class supports more than 1 generic",
        action="store",
        default="",
    )
    parser.add_argument(
        "-n",
        "--data_points_per_wave",
        help="Number of data points required per wave\n"
        "Default value is 100 samples per wave",
        action="store",
        default=100,
        type=int,
    )
    parser.add_argument(
        "-cl",
        "--chn_list",
        help="Channels list to stream data to\nE.g. --chn_list 0 2 3 to stream data to channels 0, 2, 3\n"
        "Default is channel 0",
        nargs="+",
        action="store",
        default=[0],
        type=int,
    )
    parser.add_argument(
        "-vl",
        "--v_lower_req",
        help="Lower end Voltage required in volts. Should be in the accepted FSR.",
        action="store",
        type=float,
    )
    parser.add_argument(
        "-vu",
        "--v_upper_req",
        help="Upper end Voltage required in volts. Should be in the accepted FSR.",
        action="store",
        type=float,
    )
    parser.add_argument(
        "-f",
        "--output_freq",
        help="Output frequency required in Hz.\nNote: The effective output frequency per "
        "channel might vary based on the device and number of active channels.\n"
        "Default will be the maximum sampling frequency supported by the app.",
        action="store",
        type=int,
    )
    parser.add_argument(
        "-c",
        "--code_sel",
        help="code data format to stream data in. \nAccepted:\n\t0 for offset binary"
        "\n\t1 for 2s-complement.\nDefault is 0 (offset binary)",
        action="store",
        default=0,
        type=int,
        choices=[0, 1],
    )
    parser.add_argument(
        "-w",
        "--wave_types",
        help="list of waveform type required. "
        "\nAccepted: \n\tsine"
        "\n\tcosine "
        "\n\ttriangular "
        "\n\tsquare "
        "\n\tpwm"
        "\nDefault is sine"
        "\nE.g. --wave_types sine square triangular ",
        nargs="+",
        action="store",
        default=["sine"],
        choices=["sine", "cosine", "triangular", "square", "pwm"],
    )
    parser.add_argument(
        "-dc",
        "--duty_cycle",
        help="duty cycle in percent for pwm wave. "
        "\nAccepted: \n\t1-99"
        "\nDefault is 30",
        action="store",
        type=int,
        default=30,
    )
    parser.add_argument(
        "-o",
        "--channel_order",
        help="order of the generated channel wise data array to be streamed."
        "\nNote: This can be useful if the application assumes the data to be in a particular order."
        "\nAccepted: \n\tasc -- default order (ascending)"
        "\n\tdesc -- (descending)",
        action="store",
        default="asc",
        choices=["asc", "desc"],
    )
    parser.add_argument(
        "-t",
        "--test_device",
        help="flag to test devices that are not part of the supported device list",
        action="store_true",
    )

    args = vars(parser.parse_args(argv))

    if args["test_device"]:
        print("Device test enabled")
    else:
        supported_devices = [
            "ad579x",
            "ad3552r",
            "ad3530r",
            "ad5754r",
            "ad9152",
            "ad9172",
        ]

        device_name = args["class"]
        if device_name not in supported_devices:
            raise Exception(
                f"The device {device_name} is not supported. Supported devices are"
                f": {','.join(supported_devices)}"
                f"\nEnable test_device (-t) flag to test devices not part of the supported devices list."
            )

    if args["data_points_per_wave"] <= 0:
        raise argparse.ArgumentTypeError("data points must be greater than 0")

    if args["output_freq"] is not None and args["output_freq"] <= 0:
        raise argparse.ArgumentTypeError(
            "output frequency required cannot be a negative number"
        )

    if args["neg_voltage_ref"] >= args["pos_voltage_ref"]:
        raise argparse.ArgumentTypeError(
            "negative reference cannot be greater than the positive reference"
        )

    if args["duty_cycle"] < 0 or args["duty_cycle"] > 100:
        raise argparse.ArgumentTypeError("Duty cycle shall be in between 0 and 100")

    app = ADIStream(
        args["class"],
        args["uri"],
        args["neg_voltage_ref"],
        args["pos_voltage_ref"],
        args["data_points_per_wave"],
        args["chn_list"],
        args["v_lower_req"],
        args["v_upper_req"],
        args["output_freq"],
        args["code_sel"],
        args["wave_types"],
        args["device_name"],
        args["duty_cycle"],
        args["channel_order"],
    )
    app.data_stream_abort = test_flag
    app.do_data_streaming()
