# Copyright (C) 2020 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
import argparse
import csv
import logging
import pprint

import calibration_utils as cal_utils
import numpy as np

from adi.admt4000 import admt4000ard1z

FULL_TURN = 360  # degrees

# Configure logging
logging.basicConfig(level=logging.INFO)

amax = 131072
dmax = int(amax / 2)
vmax = 127438 * 2

################################################################################
def run_motor_and_capture_angles(
    cal_kit, usteps_per_sample, sampling_delay, samples_size
):
    data = []
    angles = []
    motor_angles = []

    # Move motor to starting position
    print("Moving motor to starting position...")
    cal_kit.rotate_absolute(starting_angle + starting_turn * FULL_TURN)
    fault_reg = read_faults(cal_kit.sensor)
    print("ADMT4000 Fault Register: 0x{:04X} (0b{:016b})".format(fault_reg, fault_reg))

    curr_abs_usteps = int(cal_kit.motor.angular_position.raw)
    print("Current position in microsteps: {}".format(curr_abs_usteps))
    for i in range(samples_size):
        curr_angle_raw = cal_kit.sensor.angle.raw
        curr_angle = (curr_angle_raw) * cal_kit.sensor.angle.scale
        curr_turns = cal_kit.sensor.turns.processed
        print("")
        print("-------------------------------------------")
        print("Sample #{}:".format(i))
        print("Current microsteps: {}".format(curr_abs_usteps))
        print("Turn count: {:.2f}".format(curr_turns))
        print("Angle:  {:.2f}° ({})".format(curr_angle, curr_angle_raw))
        curr_motor_angle = (
            cal_kit.motor.angular_position.raw
            % (
                360.0
                / (
                    cal_kit.motor.angular_position.scale
                    * cal_kit.motor.angular_position.calibscale
                )
            )
            * cal_kit.motor.angular_position.scale
            * cal_kit.motor.angular_position.calibscale
        )
        print("Current motor angle: {:.2f}°".format(curr_motor_angle))
        print(
            "Current Motor Abs Angle: {:.2f}°".format(
                cal_kit.motor.angular_position.processed
            )
        )
        print(
            "Current ADMT4000 Abs Angle: {:.2f}°".format(
                int(curr_turns) * 360 + curr_angle
            )
        )

        angles.append(curr_angle)
        motor_angles.append(curr_motor_angle)

        data.append((curr_angle, curr_motor_angle))
        cal_kit.rotate_relative_usteps(usteps_per_sample)
        curr_abs_usteps = int(cal_kit.motor.angular_position.raw)
    return data


def zero_correction_coefficients(cal_setup):
    logging.info("Zeroing harmonic correction coefficients...")
    cal_setup.harmonics = [(0, 0), (0, 0), (0, 0), (0, 0)]


def print_harmonic_errors(error_mag, harmonic_errors, scaled_harmonic_errors):
    print("1st harmonic")
    print("bin: 11")
    print("magnitude: {:.4f}".format(error_mag[11]))
    print("2nd harmonic")
    print("bin: 22")
    print("magnitude: {:.4f}".format(error_mag[22]))

    if not (
        error_mag[11] == max(error_mag[8:15]) and error_mag[22] == max(error_mag[19:26])
    ):
        print(f"\033[31mHarmonics might not be the localized peak!!!\033[0m")

    print("--------------------------------------------------------------")
    print("Harmonic Errors")
    pp = pprint.PrettyPrinter(indent=4)
    print("Harmonic Errors (raw):")
    pp.pprint(harmonic_errors)
    print("Scaled Harmonic Errors:")
    pp.pprint(scaled_harmonic_errors)


def read_faults(sensor):
    # Clear latched faults before reading fault register
    sensor.reg_write(0x06, 0x00)
    fault_reg = sensor.faults
    print("ADMT4000 Fault Register: 0x{:04X} (0b{:016b})".format(fault_reg, fault_reg))

    return fault_reg


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ADMT4000 Calibration example")
    parser.add_argument(
        "--uri",
        type=str,
        default="serial:COM10,230400,8n1",
        help="IIO context URI. Use 'ip:<address>' for Ethernet"
        " or 'serial:<port>,<baud>,8n1' for USB serial.",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Enable real-time plotting of angle and turns data.",
    )
    parser.add_argument(
        "--use-factory-correction",
        action="store_true",
        default=False,
        help="Use factory correction values stored in the"
        " ADMT4000 instead of calculating new ones.",
    )
    parser.add_argument(
        "--no-re-run",
        dest="no_re_run",
        action="store_true",
        default=False,
        help="The script runs the calibration routine twice"
        " by default. First when --no-calibrate is not used,"
        " and then a second time to show the effects of the"
        " calibration. Use this flag to skip the second run.",
    )
    parser.add_argument(
        "--no-calibrate",
        dest="no_calibrate",
        action="store_true",
        default=False,
        help="Skip running and applying calibration. Will only"
        " run routine once (if --no-re-run is not set) and"
        " will not apply computed correction coefficients to"
        " the device registers. This can be used to see the"
        " effects of the factory correction or to just capture"
        " data using calibration coefficients from previous"
        " runs.",
    )
    parser.add_argument(
        "--zero-correction",
        dest="zero_correction",
        action="store_false",
        default=True,
        help="Set the correction coefficients to zero before"
        " running. This can be used to reset the calibration"
        " coefficients. Calibration coefficients are retained"
        " as long as the device is not reset or power cycled.",
    )
    parser.add_argument(
        "--full-step-angle",
        type=float,
        default=0.9,
        help="Full step angle of the motor in degrees (default: 0.9).",
    )
    parser.add_argument(
        "--samples-size",
        type=int,
        default=256,
        help="Number of samples to capture during calibration."
        " Must be power of 2 (default: 256).",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=11,
        help="Number of cycles/full turns to rotate during"
        " calibration. Must be a prime number (default: 11).",
    )
    parser.add_argument(
        "--starting-turn",
        type=int,
        default=12,
        help="Starting turn number for the calibration routine (default: 12).",
    )
    parser.add_argument(
        "--starting-angle",
        type=float,
        default=0.0,
        help="Starting angle in degrees (default: 0).",
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
    enable_plot = args.plot
    use_factory_correction = args.use_factory_correction
    do_re_run = not args.no_re_run
    calibrate = not args.no_calibrate
    zero_correction = args.zero_correction
    full_step_angle = args.full_step_angle
    samples_size = args.samples_size
    turns = args.cycles
    starting_turn = args.starting_turn
    starting_angle = args.starting_angle

    if args.reversed_shaft:
        direction = 1
    else:
        direction = -1

    if args.cw_steps:
        step_direction = -1
    else:
        step_direction = 1

    cal_setup = admt4000ard1z(uri=iio_context, motor_direction=direction)

    angle_scale = cal_setup.sensor.angle.scale
    temp_scale = cal_setup.sensor.temp.scale
    temp_offset = cal_setup.sensor.temp.offset

    curr_angle_raw = cal_setup.sensor.angle.raw
    curr_angle = (curr_angle_raw) * angle_scale
    curr_temp_raw = cal_setup.sensor.temp.raw
    curr_temp = (curr_temp_raw + temp_offset) * temp_scale / 1000
    curr_turns = cal_setup.sensor.turns.processed
    print("ADMT4000 Current Readings")
    print("Turn count: {:.2f}".format(curr_turns))
    print("Angle:  {:.2f}° ({})".format(curr_angle, curr_angle_raw))
    print("Absolute Angle:  {:.2f}°".format(curr_angle + int(curr_turns) * FULL_TURN))
    print("Temperature: {:.2f}°C".format(curr_temp))

    cal_setup.motor.amax = amax
    cal_setup.motor.vmax = vmax
    cal_setup.motor.dmax = dmax

    usteps_per_full_step = 1 / cal_setup.motor.angular_position.scale
    cal_setup.motor.angular_position.calibscale = full_step_angle

    full_turn_usteps = usteps_per_full_step * FULL_TURN / full_step_angle
    print(f"Full turn microsteps: {full_turn_usteps}")
    total_steps = turns * FULL_TURN / full_step_angle
    print(f"Total steps: {total_steps}")
    total_usteps = total_steps * usteps_per_full_step
    print(f"Total microsteps: {total_usteps}")

    usteps_per_sample = step_direction * int(total_usteps / samples_size)
    print("Microsteps per sample: {}".format(usteps_per_sample))
    print(
        "Motor current position: {:.2f}° ({} usteps)".format(
            cal_setup.motor.angular_position.processed,
            cal_setup.motor.angular_position.raw,
        )
    )
    step_delay = abs(usteps_per_sample) * 4 / vmax

    print("Aligning motor and sensor measurements...")
    cal_setup.motor_sensor_alignment()
    print(
        "Motor current position: {:.2f}° ({} usteps)".format(
            cal_setup.motor.angular_position.processed,
            cal_setup.motor.angular_position.raw,
        )
    )

    # Calibration configuration
    if use_factory_correction:
        cal_setup.sensor.h8_corr_src = "factory"
    else:
        cal_setup.sensor.h8_corr_src = "user"

    # Set up harmonic correction parameters
    if calibrate or zero_correction:
        zero_correction_coefficients(cal_setup.sensor)

    calibration_results = None
    # Run calibration
    if calibrate:
        cal_setup.sensor.h8_corr_src = "user"
        data = run_motor_and_capture_angles(
            cal_setup, usteps_per_sample, step_delay, samples_size
        )
        sensor_angles, motor_angles = zip(*data)
        with open("calibration_data.csv", mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["PANG (degrees)", "Ideal Angle"])  # Header

            for row in data:
                sensor_angle, motor_angle = row
                writer.writerow([sensor_angle, motor_angle])

        primary_angles = np.array(sensor_angles)
        ref_angles = np.array(motor_angles)
        (
            cal_scaled_harmonic_errors,
            cal_harmonic_errors,
            cal_angle_error,
            cal_error_mag,
        ) = cal_utils.harmonic_calibration(primary_angles, ref_angles)
        corrected_angle_error, corrected_error_mag = cal_utils.calculate_corrections(
            cal_angle_error, cal_harmonic_errors, ref_angles
        )

        print_harmonic_errors(
            cal_error_mag, cal_harmonic_errors, cal_scaled_harmonic_errors
        )

        print("Applying correction values to ADMT4000 registers...")
        # Arrange calibration harmonic errors as list of tuples (magnitude, phase)
        harmonic_errors = [
            (cal_harmonic_errors[1]["magnitude"], cal_harmonic_errors[1]["phase"]),
            (cal_harmonic_errors[2]["magnitude"], cal_harmonic_errors[2]["phase"]),
            (cal_harmonic_errors[3]["magnitude"], cal_harmonic_errors[3]["phase"]),
            (cal_harmonic_errors[8]["magnitude"], cal_harmonic_errors[8]["phase"]),
        ]
        cal_setup.sensor.harmonics = harmonic_errors
        fault_reg = read_faults(cal_setup.sensor)
        print(
            "ADMT4000 Fault Register: 0x{:04X} (0b{:016b})".format(fault_reg, fault_reg)
        )

        if enable_plot:
            cal_utils.print_cal_plots(
                primary_angles,
                cal_angle_error,
                cal_error_mag,
                corrected_angle_error,
                corrected_error_mag,
                plot_name="Pre-Calibration",
                blocking=not do_re_run,
            )

    if do_re_run:
        data = run_motor_and_capture_angles(
            cal_setup, usteps_per_sample, step_delay, samples_size
        )
        sensor_angles, motor_angles = zip(*data)
        primary_angles = np.array(sensor_angles)
        ref_angles = np.array(motor_angles)
        (
            scaled_harmonic_errors,
            harmonic_errors,
            angle_error,
            error_mag,
        ) = cal_utils.harmonic_calibration(primary_angles, ref_angles)
        print_harmonic_errors(error_mag, harmonic_errors, scaled_harmonic_errors)
        fault_reg = read_faults(cal_setup.sensor)
        print(
            "ADMT4000 Fault Register: 0x{:04X} (0b{:016b})".format(fault_reg, fault_reg)
        )
        if enable_plot:
            cal_utils.print_cal_plots(
                primary_angles=primary_angles,
                angle_error=angle_error,
                error_mag=error_mag,
                plot_name="Post-Calibration",
                blocking=True,
                show_computed=False,
            )

    if calibrate:
        print("\n\nResults Summary from the Calibration Run:")
        print_harmonic_errors(
            cal_error_mag, cal_harmonic_errors, cal_scaled_harmonic_errors
        )
        print(
            "Calibration coefficients applied to the device"
            " registers. You can power cycle the device to"
            " reset the coefficients to factory values or"
            " run the script again with --zero-correction"
            " flag to set the coefficients to zero."
        )

del cal_setup
