# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import argparse
from time import sleep

from adi.tmc5240 import tmc5240

FULL_TURN = 360  # degrees

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TMC5240 basic example")
    parser.add_argument(
        "--uri",
        type=str,
        default="serial:COM10,230400,8n1",
        help="IIO context URI. Use 'ip:<address>' for Ethernet"
        " or 'serial:<port>,<baud>,8n1' for USB serial.",
    )
    parser.add_argument(
        "--direction",
        type=int,
        default=-1,
        help="Motor direction: 1 for CW, -1 for CCW.",
    )
    args = parser.parse_args()

    iio_context = args.uri
    direction = args.direction

    # Motor Driver Parameters
    amax = 131072
    dmax = int(amax / 2)  # 3000
    vmax = 127438 * 2

    ################################################################################
    # Use this with MCUs running tinyiiod and make sure to use the correct com port.
    dev = tmc5240(uri=iio_context, direction=direction)

    dev.amax = amax
    dev.vmax = vmax
    dev.dmax = dmax
    usteps_per_full_step = 1 / dev.angular_position.scale

    print(
        "Current position: {:.4f}° {} microsteps".format(
            dev.angular_position.processed, dev.angular_position.raw
        )
    )
    target_angle = int(dev.angular_position.processed) + 120
    dev.angular_position.processed = target_angle
    print(
        "Target position: {:.4f}° {} microsteps".format(
            target_angle,
            target_angle
            / (dev.angular_position.scale * dev.angular_position.calibscale),
        )
    )
    sleep(2)
    print(
        "Current position: {:.4f}° {} microsteps".format(
            dev.angular_position.processed, dev.angular_position.raw
        )
    )
    move_actual = 0
    print("Set Current position to: {:.4f}°".format(move_actual))
    dev.angular_position.processed = move_actual
    sleep(2)
    print(
        "Current position: {:.4f}° {} microsteps".format(
            dev.angular_position.processed, dev.angular_position.raw
        )
    )

    target_usteps = int(dev.angular_position.raw) + 20000
    dev.angular_position.raw = target_usteps
    print(
        "Target position: {:.4f}° {} microsteps".format(
            target_usteps
            * dev.angular_position.scale
            * dev.angular_position.calibscale,
            target_usteps,
        )
    )
    sleep(2)
    print(
        "Current position: {:.4f}° {} microsteps".format(
            dev.angular_position.processed, dev.angular_position.raw
        )
    )

    target_usteps = int(dev.angular_position.raw) - 20000
    dev.angular_position.raw = target_usteps
    print(
        "Target position: {:.4f}° {} microsteps".format(
            target_usteps
            * dev.angular_position.scale
            * dev.angular_position.calibscale,
            target_usteps,
        )
    )
    sleep(2)
    print(
        "Current position: {:.4f}° {} microsteps".format(
            dev.angular_position.processed, dev.angular_position.raw
        )
    )
    del dev
