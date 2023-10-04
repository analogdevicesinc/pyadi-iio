# Copyright (C) 2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import math as m


def save_for_pscope(
    out_path, num_bits, is_bipolar, num_samples, dc_num, ltc_num, *data
):
    num_channels = len(data)
    if num_channels < 0 or num_channels > 16:
        raise ValueError("pass in a list for each channel (between 1 and 16)")

    full_scale = 1 << num_bits
    if is_bipolar:
        min_val = -full_scale // 2
        max_val = full_scale // 2
    else:
        min_val = 0
        max_val = full_scale

    with open(out_path, "w") as out_file:
        out_file.write("Version,115\n")
        out_file.write(
            "Retainers,0,{0:d},{1:d},1024,0,{2:0.15f},1,1\n".format(
                num_channels, num_samples, 0.0
            )
        )
        out_file.write("Placement,44,0,1,-1,-1,-1,-1,10,10,1031,734\n")
        out_file.write("DemoID," + dc_num + "," + ltc_num + ",0\n")
        for i in range(num_channels):
            out_file.write(
                "RawData,{0:d},{1:d},{2:d},{3:d},{4:d},{5:0.15f},{3:e},{4:e}\n".format(
                    i + 1, int(num_samples), int(num_bits), min_val, max_val, 1.0
                )
            )
        for samp in range(num_samples):
            out_file.write(str(data[0][samp]))
            for ch in range(1, num_channels):
                out_file.write(", ," + str(data[ch][samp]))
            out_file.write("\n")
        out_file.write("End\n")


if __name__ == "__main__":
    num_bits = 16
    num_samples = 65536
    channel_1 = [int(8192 * m.cos(0.12 * d)) for d in range(num_samples)]
    channel_2 = [int(8192 * m.cos(0.034 * d)) for d in range(num_samples)]

    save_for_pscope(
        "test.adc",
        num_bits,
        True,
        num_samples,
        "DC9876A-A",
        "LTC9999",
        channel_1,
        channel_2,
    )
