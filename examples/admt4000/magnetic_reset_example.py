# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import argparse
import logging
import math
from datetime import datetime
from time import sleep

import matplotlib.pyplot as plt
import numpy as np

from adi.admt4000 import admt4000ard1z

FULL_TURN = 360  # degrees

# Configure logging
logging.basicConfig(level=logging.INFO)


def get_register_readout(sensor):
    """Get ADMT4000 register readout as a dictionary."""
    reg_dict = {
        "GENERAL": {"page": 0x02, "addr": 0x10, "value": None},
        "DIGIOEN": {"page": 0x02, "addr": 0x12, "value": None},
        "UNIQID0": {"page": 0x02, "addr": 0x1E, "value": None},
        "UNIQID1": {"page": 0x02, "addr": 0x1F, "value": None},
        "UNIQID2": {"page": 0x02, "addr": 0x20, "value": None},
        "UNIQID3": {"page": 0x02, "addr": 0x21, "value": None},
    }

    for reg, reg_entry in reg_dict.items():
        sensor.reg_write(0x01, reg_entry["page"] & 0x001F)
        reg_value = sensor.reg_read(reg_entry["addr"])
        reg_dict[reg]["value"] = f"0x{reg_value:04X}"

    sensor.reg_write(0x01, 0x00)

    return reg_dict


def log_test_result_to_file(filename, mode, tag, result):
    """Log test result to a CSV file."""
    with open(filename, mode) as f:
        f.write(f"{tag}, {result}\n")


def log_turns_result_to_file(
    filename,
    mode,
    step=None,
    turn_direction="CCW",
    expected_turn_count=None,
    admt4000_turn_count=None,
    admt4000_angle=None,
    admt4000_abs_angle=None,
    motor_abs_angle=None,
    fault=None,
):
    """Log test result to a CSV file."""
    if mode == "w":
        with open(filename, mode) as f:
            f.write(
                "Step, Direction, Expected Turn Count,"
                " ADMT4000 Turn Count, ADMT4000 Angle (°),"
                " ADMT4000 Abs Angle (°),"
                " Motor ABSANGLE (°), Fault (0x)\n"
            )
    else:
        with open(filename, mode) as f:
            f.write(
                f"{step}, {turn_direction},"
                f" {expected_turn_count},"
                f" {admt4000_turn_count},"
                f" {admt4000_angle},"
                f" {admt4000_abs_angle},"
                f" {motor_abs_angle},"
                f" {fault:04x}\n"
            )


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
        fault_reg = read_faults(sensor)
        print("Current ADMT4000 Absolute Angle:  {:.2f}°".format(curr_abs_angle))
        print("ADMT4000 Turn count: {:.2f}".format(curr_turns))
        print("ADMT4000 Angle: {:.2f}°".format(curr_angle))
        print(
            "ADMT4000 Fault Register: 0x{:04X} (0b{:016b})".format(fault_reg, fault_reg)
        )


def read_faults(sensor):
    # Clear latched faults before reading fault register
    sensor.reg_write(0x06, 0x00)
    fault_reg = sensor.faults
    print("ADMT4000 Fault Register: 0x{:04X} (0b{:016b})".format(fault_reg, fault_reg))
    return fault_reg


# Data storage for plotting
angles_list = []
turns_list = []
absolute_angles_list = []
fault_list = []


def update_plot(fig, ax1, ax2, ax3, data_tuple, status=None):
    """
    Update data to plot and update visualization.

    Args:
        data_tuple: Tuple of (turns, angle, absolute_angle, fault)
    """
    turns_list, angles_list, absolute_angles_list, fault_list = data_tuple

    # Determine colors based on fault status
    colors_turns = ["red" if f != 0 else "blue" for f in fault_list]
    colors_angles = ["red" if f != 0 else "green" for f in fault_list]
    colors_abs_angles = ["red" if f != 0 else "green" for f in fault_list]
    # Update turn count plot
    ax1.clear()
    ax1.scatter(range(len(turns_list)), turns_list, c=colors_turns, marker=".")
    ax1.set_xlabel("Sample Number")
    ax1.set_ylabel("Turn Count")
    ax1.set_title("Turn Count (Red = Fault)")
    ax1.grid(True)

    # Update angle plot
    ax2.clear()
    ax2.scatter(range(len(angles_list)), angles_list, c=colors_angles, marker="o")
    ax2.set_xlabel("Sample Number")
    ax2.set_ylabel("Angle (degrees)")
    ax2.set_title("Angle (Red = Fault)")
    ax2.grid(True)

    ax3.clear()
    ax3.scatter(
        range(len(absolute_angles_list)),
        absolute_angles_list,
        c=colors_abs_angles,
        marker=".",
    )
    ax3.set_xlabel("Sample Number")
    ax3.set_ylabel("Absolute Angle (degrees)")
    ax3.set_title("Absolute Angle (Red = Fault)")
    ax3.grid(True)

    if status is not None:
        color = "green" if status == "PASSED" else "red"
        # Clear any previous status text and add new one in dedicated area
        if hasattr(fig, "status_text"):
            fig.status_text.remove()
        fig.status_text = fig.text(
            0.5,
            0.9,
            status,
            ha="center",
            fontsize=22,
            color=color,
            weight="bold",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
        )
        plt.subplots_adjust(top=0.92, bottom=0.08)

    plt.tight_layout()
    fig.canvas.draw()
    fig.canvas.flush_events()


################################################################################
if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="ADMT4000 Magnetic Reset Example")
    parser.add_argument(
        "--uri",
        type=str,
        default="serial:COM10,230400,8n1",
        help="IIO context URI. Use 'ip:<address>' for"
        " Ethernet or 'serial:<port>,<baud>,8n1'"
        " for USB serial.",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Enable real-time plotting of angle and turns data.",
    )
    parser.add_argument(
        "--no-run-sweep",
        action="store_false",
        dest="run_sweep",
        help="Skip verification sweep",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        default=False,
        help="Enable interactive prompts (default: False)",
    )
    parser.add_argument(
        "--dc-dc-charge-time",
        type=int,
        default=300,
        help="DC-DC charge time in ms (default: 300)",
    )
    parser.add_argument(
        "--reset-duration",
        type=int,
        default=1,
        help="Reset pulse duration in ms (default: 1)",
    )
    parser.add_argument(
        "--keep-dc-dc-enabled",
        action="store_false",
        dest="disable_dc_dc_after_reset",
        default=True,
        help="Keep DC-DC enabled after reset (default: False)",
    )
    parser.add_argument(
        "--starting-turn",
        type=int,
        default=35,
        help="Starting turn count (default: 35)",
    )
    parser.add_argument(
        "--log",
        action="store_true",
        default=False,
        help="Enable logging to file (default: False)",
    )
    parser.add_argument(
        "--reversed-shaft",
        dest="reversed_shaft",
        action="store_true",
        default=False,
        help="Motor rotation direction will be reversed if this flag is set.",
    )
    parser.add_argument(
        "--full-step-angle",
        type=float,
        default=0.9,
        help="Full step angle of the motor in degrees (default: 0.9).",
    )

    args = parser.parse_args()

    # Set up ADMT4000 using parsed arguments
    iio_context = args.uri
    run_sweep = args.run_sweep
    enable_plot = args.plot
    interactive = args.interactive
    dc_dc_charge_time_ms = args.dc_dc_charge_time
    reset_pulse_time_ms = args.reset_duration
    disable_dc_dc_after_reset = args.disable_dc_dc_after_reset
    reset_turn = args.starting_turn
    log_to_file = args.log

    # Motor Driver Parameters
    if args.reversed_shaft:
        direction = 1
    else:
        direction = -1

    full_step_angle = args.full_step_angle

    reset_angle = 315.00  # degrees.
    amax = 131072
    dmax = int(amax / 2)  # 3000
    vmax = 127438 * 2

    starting_turn = reset_turn
    starting_angle = reset_angle

    test_pass = False
    faults_detected = 0

    fault_count = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    if log_to_file:
        log_filename = f"magnetic_reset"
        date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        csv_filename = f"{log_filename}_{date}.csv"
        print(f"Results will be saved to: {csv_filename}")

    dev = admt4000ard1z(
        uri=iio_context,
        motor_direction=direction,
        disable_dc_dc_after_reset=disable_dc_dc_after_reset,
        dc_dc_charge_time_ms=dc_dc_charge_time_ms,
        reset_pulse_time_ms=reset_pulse_time_ms,
    )
    dev.motor.amax = amax
    dev.motor.vmax = vmax
    dev.motor.dmax = dmax
    usteps_per_full_step = 1 / dev.motor.angular_position.scale

    try:
        board_id = dev.ctx._attrs["hw_mezzanine"]
    except KeyError:
        board_id = "EVAL-ADTM4000ARD1Z"

    if log_to_file:
        log_test_result_to_file(csv_filename, "w", "BOARD ID", board_id)

    cnv_page = dev.sensor.reg_read(0x01)
    dev.sensor.reg_write(0x01, (cnv_page & 0x001F) | 0x02)
    gen_reg = dev.sensor.reg_read(0x10)
    print("ADMT4000 GENERAL Register: 0x{:04X}".format(gen_reg))
    dev.sensor.reg_write(0x01, cnv_page)

    print_current_position(motor=dev.motor, sensor=dev.sensor)

    dev.motor_sensor_alignment()
    print_current_position(motor=dev.motor, sensor=dev.sensor)

    print("\nRotating to turn = {} and angle = 315°...".format(starting_turn))
    dev.rotate_absolute(starting_angle + starting_turn * FULL_TURN)
    print_current_position(motor=dev.motor, sensor=dev.sensor)

    # Enable pulse generator DC-DC converter

    # Data storage
    angles_list = []
    turns_list = []
    absolute_angles_list = []
    fault_list = []

    # Create figure for live plotting
    # Initialize plot
    if enable_plot:
        plt.ion()
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8))
        plt.show(block=False)
    test_pass = False
    update_plot(
        fig, ax1, ax2, ax3, (turns_list, angles_list, absolute_angles_list, fault_list)
    )

    if interactive:
        user_input = (
            input("\nDo you want to proceed with the magnetic reset? (Y/n): ")
            .strip()
            .lower()
        )
        if user_input not in ["y", "Y", ""]:
            print("Magnetic reset cancelled by user.")
            del dev
            exit(0)
    pre_reset_turn_count = dev.sensor.turns.processed
    pre_reset_angle = dev.sensor.angle.processed

    dev.magnetic_reset()

    sleep(2)  # Allow time for reset to complete and values to stabilize
    post_reset_turn_count = dev.sensor.turns.processed
    post_reset_angle = dev.sensor.angle.processed

    post_reset_turn_count = dev.sensor.turns.processed
    post_reset_angle = dev.sensor.angle.processed
    print_current_position(motor=dev.motor, sensor=dev.sensor)
    dev.motor_sensor_alignment()
    print_current_position(motor=dev.motor, sensor=dev.sensor)

    if run_sweep:
        if interactive:
            user_input = (
                input("\nDo you want to proceed with the sweep? (Y/n): ")
                .strip()
                .lower()
            )
            if user_input not in ["y", "Y", ""]:
                print("Sweep cancelled by user.")
                del dev
                exit(0)

        # Verification: Rotate in quarter-turn increments and plot data
        print("\n\nStarting verification sweep...")

        # Calculate steps
        quarter_turns = {"CCW": [], "CW": []}
        dev.motor_sensor_alignment()
        if log_to_file:
            sweep_filename = f"{log_filename}_sweep_{date}.csv"
            log_turns_result_to_file(sweep_filename, "w")
        for step_direction, sweep in [(-1, (45, 0)), (1, (0, 45))]:
            step_direction_str = "CCW" if step_direction == -1 else "CW"
            print(
                f"\n\nStarting verification sweep in {step_direction_str} direction..."
            )
            # start_angle = dev.angle.processed + int(dev.turns.processed) * FULL_TURN
            start_angle = sweep[0] * FULL_TURN + 45.0
            print(
                f"Initial angle for this sweep:"
                f" {start_angle:.2f}° starting"
                f" at turn {sweep[0]:.2f}"
            )

            print(f"start angle: {start_angle}")
            quarter_turn = step_direction * FULL_TURN / 4  # 90 degrees

            print_current_position(motor=dev.motor, sensor=dev.sensor)
            dev.rotate_absolute(start_angle)
            print_current_position(motor=dev.motor, sensor=dev.sensor)
            new_angle = start_angle
            num_steps = (sweep[0] - sweep[1]) * 4
            num_steps = abs(num_steps)
            if interactive:
                input(
                    f"\nPress Enter to start"
                    f" {step_direction_str} sweep of"
                    f" {num_steps} quarter turns..."
                )
            for i in range(num_steps + 1):
                print(f"\nStep {i}/{num_steps}:")
                sleep(0.1)  # Allow time for settling
                # Read ADMT4000 data
                curr_angle = dev.sensor.angle.processed
                curr_turns = dev.sensor.turns.processed
                motor_angle = dev.motor.angular_position.processed
                # curr_abs_angle = (int(curr_turns) * FULL_TURN
                #     + (curr_angle - (360 if curr_turns < 0 else 0)))  # noqa: E501
                curr_abs_angle = math.floor(curr_turns) * FULL_TURN + curr_angle
                fault_reg = read_faults(dev.sensor)
                if fault_reg != 0:
                    for bit in range(16):
                        if fault_reg & (1 << bit):
                            fault_count[bit] += 1
                    print("  Warning: Fault detected after rotation!")
                log_str = (
                    f"Step {i}"
                    f"(expected turn/absangle:"
                    f" {new_angle/360}/{new_angle}):"
                    f" ADMT4000 - Turns: {curr_turns:.2f},"
                    f" Angle: {curr_angle:.2f}°,"
                    f" Absolute: {curr_abs_angle:.2f}°,"
                    f" Motor Angle: {motor_angle:.2f}°,"
                    f" Fault: 0x{fault_reg:04X}"
                    f" (0b{fault_reg:016b})"
                )
                print(log_str)
                if log_to_file:
                    log_turns_result_to_file(
                        sweep_filename,
                        "a",
                        i,
                        step_direction_str,
                        new_angle / 360,
                        curr_turns,
                        curr_angle,
                        curr_abs_angle,
                        motor_angle,
                        fault_reg,
                    )

                quarter_turns[step_direction_str].append(int(curr_turns * 4))

                turns_list.append(curr_turns)
                angles_list.append(curr_angle)
                absolute_angles_list.append(curr_abs_angle)
                fault_list.append(fault_reg)
                if enable_plot:
                    update_plot(
                        fig,
                        ax1,
                        ax2,
                        ax3,
                        (turns_list, angles_list, absolute_angles_list, fault_list),
                    )

                print(f"Rotating by {quarter_turn:.2f}°...")
                new_angle += quarter_turn
                # dev.rotate_absolute(new_angle)
                dev.rotate_relative(quarter_turn)

        print("\nVerification sweep complete!")
        if any(count > 0 for count in fault_count):
            print("\n*** ERROR: Faults detected during verification! ***")
            print("Fault breakdown by bit:")
            for bit, count in enumerate(fault_count):
                if count > 0:
                    print(f"  Bit {bit}: {count} occurrences")
        qturn_ccw_start = quarter_turns["CCW"][0]
        qturn_cw_start = quarter_turns["CW"][0]
        for i in range(len(quarter_turns["CCW"])):
            expected_qturn = qturn_ccw_start - i
            actual_qturn = quarter_turns["CCW"][i]
            if expected_qturn != actual_qturn:
                print(
                    f"*** ERROR: Mismatch in CCW"
                    f" quarter-turns at step {i}:"
                    f" expected {expected_qturn},"
                    f" got {actual_qturn} ***"
                )
                test_pass = False
            else:
                test_pass = True
        if log_to_file:
            log_test_result_to_file(csv_filename, "a", "CCW TURNS TEST", test_pass)
            log_test_result_to_file(
                csv_filename,
                "a",
                "CCW TURNS DATA",
                " ".join(map(str, quarter_turns["CCW"])),
            )
        for i in range(len(quarter_turns["CW"])):
            expected_qturn = qturn_cw_start + i
            actual_qturn = quarter_turns["CW"][i]
            if expected_qturn != actual_qturn:
                print(
                    f"*** ERROR: Mismatch in CW"
                    f" quarter-turns at step {i+1}:"
                    f" expected {expected_qturn},"
                    f" got {actual_qturn} ***"
                )
                test_pass = False
            else:
                test_pass = test_pass and True
        if log_to_file:
            log_test_result_to_file(csv_filename, "a", "CW TURNS TEST", test_pass)
            log_test_result_to_file(
                csv_filename,
                "a",
                "CW TURNS DATA",
                " ".join(map(str, quarter_turns["CW"])),
            )

            for reg, reg_entry in get_register_readout(dev.sensor).items():
                log_test_result_to_file(csv_filename, "a", reg, reg_entry["value"])

        print(get_register_readout(dev.sensor))

        update_plot(
            fig,
            ax1,
            ax2,
            ax3,
            (turns_list, angles_list, absolute_angles_list, fault_list),
            status="PASSED" if test_pass else "FAILED",
        )
        if enable_plot:
            plt.ioff()  # Disable interactive mode
            plt.show()  # Keep final plot open
    del dev
