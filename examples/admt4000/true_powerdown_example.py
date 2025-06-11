# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import argparse
from time import sleep

from adi.admt4000 import admt4000ard1z

FULL_TURN = 360  # degrees


def print_current_position(motor, sensor):
    print("\n--- Current Position ---")
    if motor is not None:
        print(
            "Current Motor Absolute Angle: {:.2f}° ({} microsteps)".format(
                motor.angular_position.processed, motor.angular_position.raw
            )
        )
    if sensor is not None:
        curr_angle = sensor.angle.processed
        curr_turns = sensor.turns.processed
        curr_abs_angle = curr_angle + int(curr_turns) * FULL_TURN
        print("Current ADMT4000 Absolute Angle:  {:.2f}°".format(curr_abs_angle))
        print("ADMT4000 Turn count: {}".format(curr_turns))
        print("ADMT4000 Turn count (raw): {}".format(curr_turns * sensor.turns.scale))
        print("ADMT4000 Angle: {}°".format(curr_angle))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ADMT4000 true power-down example")
    parser.add_argument(
        "--uri",
        type=str,
        default="serial:COM10,230400,8n1",
        help="IIO context URI. Use 'ip:<address>' for Ethernet"
        " or 'serial:<port>,<baud>,8n1' for USB serial.",
    )

    parser.add_argument(
        "--reversed-shaft",
        dest="reversed_shaft",
        action="store_true",
        default=False,
        help="Motor rotation direction will be reversed if this flag is set.",
    )

    parser.add_argument(
        "--cw-steps",
        dest="cw_steps",
        action="store_true",
        default=False,
        help="Turns direction will be clockwise if present"
        " (i.e. decreasing ADMT4000 angles/turns)."
        " Default is counter-clockwise.",
    )

    args = parser.parse_args()

    iio_context = args.uri

    if args.reversed_shaft:
        direction = 1
    else:
        direction = -1

    if args.cw_steps:
        step_direction = -1
    else:
        step_direction = 1

    # Motor Driver Parameters
    amax = 131072
    dmax = int(amax / 2)  # 3000
    vmax = 127438 * 2

    starting_turn = 12
    starting_angle = 0  # degrees
    target_starting_angle = starting_angle + starting_turn * FULL_TURN
    target_displacement = 1090  # degrees

    ################################################################################
    # Use this with MCUs running tinyiiod and make sure to use the correct com port.
    dev = admt4000ard1z(uri=iio_context, motor_direction=direction)
    dev.motor.amax = amax
    dev.motor.vmax = vmax
    dev.motor.dmax = dmax
    usteps_per_full_step = 1 / dev.motor.angular_position.scale
    dev.motor_sensor_alignment()
    print("Homing to a known position...")
    dev.rotate_absolute(target_starting_angle)
    print_current_position(motor=dev.motor, sensor=dev.sensor)

    print(
        "\n\nMoving Motor by Angle while ADMT4000 is powered ON: {:.2f}°".format(
            target_displacement
        )
    )
    dev.rotate_relative(step_direction * target_displacement)
    print_current_position(motor=dev.motor, sensor=dev.sensor)

    print("ADMT4000 Power OFF")
    dev.power_enable = 0

    print(
        "\n\nMoving Motor by Angle while powered down: {:.2f}°".format(
            target_displacement
        )
    )
    dev.rotate_relative(step_direction * target_displacement)
    print_current_position(motor=dev.motor, sensor=None)

    print("ADMT4000 Power ON")
    dev.power_enable = 1
    sleep(2)
    dev.sensor.reinitialize()
    print_current_position(motor=dev.motor, sensor=dev.sensor)

    del dev
