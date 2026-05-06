# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import argparse

from adi.ad5706r import ad5706r


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="AD5706R Example Script")
    parser.add_argument(
        "--uri",
        type=str,
        default="serial:COM38,2304000",
        help="URI for connecting to the AD5706R device",
    )
    args = parser.parse_args()

    ad5706r_dev = ad5706r(uri=args.uri, device_name="ad5706r")

    chn = 0  # Channel number
    print("Sampling Frequency:", ad5706r_dev.sampling_frequency)

    ad5706r_dev.sampling_frequency = 400000
    print("Sampling Frequency:", ad5706r_dev.sampling_frequency)

    print("Output Bits:", ad5706r_dev.output_bits)
    print("Channel offset:", ad5706r_dev.channel[chn].offset)
    print("Channel scale:", ad5706r_dev.channel[chn].scale)

    # Address Ascension
    print("Address Ascension Test")
    ad5706r_dev.addr_ascension = "increment"
    ad5706r_dev.channel[chn].input_register_a = 0x1234
    print(
        hex(ad5706r_dev._ctrl.reg_read((0x60 + chn * 2)))
    )  # read dac input a register

    ad5706r_dev.addr_ascension = "decrement"
    print(hex(ad5706r_dev._ctrl.reg_read((0x60 + chn * 2))))

    # ASYNC LDAC
    print("ASYNC LDAC Test")
    ad5706r_dev.channel[chn].hw_func_sel = "LDAC"
    ad5706r_dev.channel[chn].ldac_trigger_ch = "None"
    print(hex(ad5706r_dev._ctrl.reg_read((0x60 + chn * 2))))
    print(
        hex(ad5706r_dev._ctrl.reg_read((0x68 + chn * 2)))
    )  # read data readback register

    # SW LDAC
    print("SW LDAC Test")
    ad5706r_dev.channel[chn].ldac_trigger_ch = "sw_ldac"
    ad5706r_dev.channel[chn].input_register_a = 0x2345
    print(hex(ad5706r_dev._ctrl.reg_read((0x60 + chn * 2))))
    print(hex(ad5706r_dev._ctrl.reg_read((0x68 + chn * 2))))
    ad5706r_dev.channel[chn].sw_ldac_tg_toggle = "toggle"  # SW LDAC update
    print(hex(ad5706r_dev._ctrl.reg_read((0x68 + chn * 2))))

    # HW LDAC
    print("HW LDAC Test")
    ad5706r_dev.channel[chn].ldac_trigger_ch = "hw_ldac"
    ad5706r_dev.channel[chn].input_register_a = 0x3456
    print(hex(ad5706r_dev._ctrl.reg_read((0x60 + chn * 2))))
    print(hex(ad5706r_dev._ctrl.reg_read((0x68 + chn * 2))))
    ad5706r_dev.hw_ldac_tg_state = "high"  # HW LDAC update
    ad5706r_dev.hw_ldac_tg_state = "low"  # Reset HW LDAC state
    print(hex(ad5706r_dev._ctrl.reg_read((0x68 + chn * 2))))

    del dev._ctx
    del dev


if __name__ == "__main__":
    main()
