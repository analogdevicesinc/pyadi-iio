# File: CN0548_simple_plot.py
# Description: CN0548 data logging and real-time plot
# Author: Harvey De Chavez (harveyjohn.dechavez@analog.com)
#
# Copyright 2022(c) Analog Devices, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#  - Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  - Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  - Neither the name of Analog Devices, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#  - The use of this software may or may not infringe the patent rights
#    of one or more patent holders.  This license does not release you
#    from the requirement that you obtain separate licenses from these
#    patent holders to use this software.
#  - Use of the software either in source or binary form, must be run
#    on or directly connected to an Analog Devices Inc. component.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT,
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, INTELLECTUAL PROPERTY RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import time
import turtle
from datetime import datetime
from typing import List

import adi
import click
import matplotlib.animation as animation
import matplotlib.pyplot as plt

unit = 24
x_init = -4 * unit
y_init = 6 * unit
style = ("Arial", 10)
style2 = ("Arial", 20, "bold")


def draw_rec(x, y, x_len, y_len, fill):  # for easier drawing of jumper map
    turtle.setpos(x, y)
    turtle.down()
    if fill == 1:
        turtle.begin_fill()
    for i in range(4):
        if i % 2 == 0:
            turtle.forward(x_len)
        if i % 2 == 1:
            turtle.forward(y_len)
        turtle.right(90)
    if fill == 1:
        turtle.end_fill()
    turtle.up()


def draw_jumpers():  # drawing the jumpers
    jumper = ["P1", "P3", "P10", "P8", "P9", "P11", "P13", "P14", "P12", "P7"]
    turtle.hideturtle()
    turtle.speed(0)
    turtle.up()

    turtle.setpos(0, 210)
    turtle.write("CN0548 Jumper Configuration", font=style2, align="center")

    for j in range(6):
        draw_rec(
            x_init + int(j / 3) * (6 * unit),
            y_init - (j % 3) * (4 * unit),
            2 * unit,
            3 * unit,
            0,
        )

        for k in range(6):
            draw_rec(
                x_init + int(j / 3) * (6 * unit) + 0.25 * unit + int(k / 3) * unit,
                y_init - (j % 3) * (4 * unit) - 0.25 * unit - (k % 3) * unit,
                0.5 * unit,
                0.5 * unit,
                0,
            )

        if int(j / 3) == 0:
            turtle.setpos(
                x_init + int(j / 3) * (6 * unit) + (3 * unit),
                y_init - (j % 3) * (4 * unit) - 1.875 * unit,
            )
        else:
            turtle.setpos(
                x_init + int(j / 3) * (6 * unit) - (1 * unit),
                y_init - (j % 3) * (4 * unit) - 1.875 * unit,
            )
        turtle.write(jumper[j], font=style, align="center")

    for j in range(2):
        draw_rec(x_init + unit + j * 5 * unit, y_init - 12 * unit, unit, 3 * unit, 0)

        for k in range(3):
            draw_rec(
                x_init + unit + j * 5 * unit + 0.25 * unit,
                y_init - 12 * unit - 0.25 * unit - k * unit,
                0.5 * unit,
                0.5 * unit,
                0,
            )

        turtle.setpos(
            x_init + unit + j * 5 * unit + (-3 * j + 2) * unit,
            y_init - 12 * unit - 1.875 * unit,
        )
        turtle.write(jumper[j + 6], font=style, align="center")

    for j in range(2):
        draw_rec(
            x_init - 3 * unit + j * 11 * unit, y_init - 13 * unit, 3 * unit, unit, 0
        )

        for k in range(3):
            draw_rec(
                x_init - 3 * unit + j * 11 * unit + 0.25 * unit + k * unit,
                y_init - 13 * unit - 0.25 * unit,
                0.5 * unit,
                0.5 * unit,
                0,
            )

        turtle.setpos(x_init - 1.5 * unit + j * 11 * unit, y_init - 13 * unit)
        turtle.write(jumper[j + 8], font=style, align="center")


def gain_config(jumper):  # draws the jumper locations for the desired gain
    # P1
    if jumper[0] == 1:
        draw_rec(x_init + 4, y_init - 4 - unit, 40, 16, 1)
    elif jumper[0] == 2:
        draw_rec(x_init + 4, y_init - 4, 40, 16, 1)
    else:
        draw_rec(x_init + 4 + unit, y_init - 4, 16, 40, 1)
    # P3
    if jumper[1] == 1:
        draw_rec(x_init + 4, y_init - 4 - 5 * unit, 40, 16, 1)
    elif jumper[1] == 2:
        draw_rec(x_init + 4, y_init - 4 - 4 * unit, 40, 16, 1)
    else:
        draw_rec(x_init + 4 + unit, y_init - 4 - 4 * unit, 16, 40, 1)
    # P10
    if jumper[2] == 1:
        draw_rec(x_init + 4, y_init - 4 - 9 * unit, 40, 16, 1)
    elif jumper[2] == 2:
        draw_rec(x_init + 4, y_init - 4 - 8 * unit, 40, 16, 1)
    else:
        draw_rec(x_init + 4 + unit, y_init - 4 - 8 * unit, 16, 40, 1)
    # P8
    if jumper[3] == 1:
        draw_rec(x_init + 4 + 6 * unit, y_init - 4 - 1 * unit, 40, 16, 1)
    elif jumper[3] == 2:
        draw_rec(x_init + 4 + 6 * unit, y_init - 4 - 2 * unit, 40, 16, 1)
    else:
        draw_rec(x_init + 4 + 6 * unit, y_init - 4, 16, 40, 1)
    # P9
    if jumper[4] == 1:
        draw_rec(x_init + 4 + 6 * unit, y_init - 4 - 5 * unit, 40, 16, 1)
    elif jumper[4] == 2:
        draw_rec(x_init + 4 + 6 * unit, y_init - 4 - 6 * unit, 40, 16, 1)
    else:
        draw_rec(x_init + 4 + 6 * unit, y_init - 4 - 4 * unit, 16, 40, 1)
    # P11
    if jumper[5] == 1:
        draw_rec(x_init + 4 + 6 * unit, y_init - 4 - 9 * unit, 40, 16, 1)
    elif jumper[5] == 2:
        draw_rec(x_init + 4 + 6 * unit, y_init - 4 - 10 * unit, 40, 16, 1)
    else:
        draw_rec(x_init + 4 + 6 * unit, y_init - 4 - 8 * unit, 16, 40, 1)


def jumper_uni():  # jumper config for unipolar-unidirectional
    draw_rec(x_init + 4 + unit, y_init - 4 - 12 * unit, 16, 40, 1)
    draw_rec(x_init + 4 - 3 * unit, y_init - 4 - 13 * unit, 40, 16, 1)
    draw_rec(x_init + 4 + 6 * unit, y_init - 4 - 12 * unit, 16, 40, 1)
    draw_rec(x_init + 4 + 9 * unit, y_init - 4 - 13 * unit, 40, 16, 1)


def jumper_bi():  # jumper config for bipolar-bidirectional
    draw_rec(x_init + 4 + unit, y_init - 4 - 13 * unit, 16, 40, 1)
    draw_rec(x_init + 4 - 2 * unit, y_init - 4 - 13 * unit, 40, 16, 1)
    draw_rec(x_init + 4 + 6 * unit, y_init - 4 - 13 * unit, 16, 40, 1)
    draw_rec(x_init + 4 + 8 * unit, y_init - 4 - 13 * unit, 40, 16, 1)


def isint(
    x, lower, upper
):  # determine whether number is an integer within the range [lower,upper]
    try:
        val = int(x)
        if upper == "x":
            if val >= lower:
                return 0
            else:
                return 1
        else:
            if val >= lower and val <= upper:
                return 0
            else:
                return 1
    except:
        return 2


def input_int(
    text, lower, upper
):  # determine whether input is an integer within the range [lower,upper]
    while True:
        x = input(text)
        if isint(x, lower, upper) == 0:
            user_input = int(x)
            break
        elif isint(x, lower, upper) == 1:
            print("Please input a value within the given option range")
        else:
            print(
                "Invalid response, the system is expecting an integer value within the range of options"
            )
    return user_input


def compute_bounds(data):  # compute the lower and upper limits to be used for plotting
    span = max(data) - min(data)
    if span != 0:
        lower = min(data) - span / 16
        upper = max(data) + span / 16
    else:
        lower = min(data) - 0.001
        upper = max(data) + 0.001
    bounds = [lower, upper]
    return bounds


def compute_voltage(
    code, v_max, input_type
):  # convert raw adc code to voltage reading in volts
    v_ref = 4.096
    bits_16 = 65536
    bits_15 = 32768
    v_gain = {1: 4, 2: 5, 3: 20 / 3, 4: 10, 5: 20}

    if input_type == 1:
        voltage = round((code / bits_16) * v_ref * v_gain[v_max], 7)
    else:
        voltage = round((code / bits_15 - 1) * v_ref * v_gain[v_max], 7)

    return voltage


def compute_current(
    code, input_type
):  # convert raw adc code to current reading in amperes
    v_ref = 4.096
    bits_16 = 65536
    bits_15 = 32768
    i_gain = 5

    if input_type == 1:
        current = round((code / bits_16) * v_ref * i_gain, 7)
    else:
        current = round((code / bits_15 - 1) * v_ref * i_gain, 7)

    return current


# ----- Program starts here -----
click.clear()
print(
    " ------------------------------------------------------------------\n| EVAL-CN0548-ARDZ: Isolated High Current and High Voltage Sensing |\n ------------------------------------------------------------------\n\nGeneral Reminder:"
)
print(
    "\n  > Disconnect any input until the board is properly configured.\n\n  > Note the node polarities when using the unipolar and unidirectional modes.\n\n  > Do not use the board for inputs that exceed the set configuration.\n\n  > Disconnect any input attached to the board when changing jumper configurations.\n"
)
input("\t\t\t\t\t\tPress the 'enter' key to proceed")
click.clear()
print("Starting program...")


new_session = 0
rec_value = []
new_record = ["Session Record:"]
line_count = 0
error = 0
retry = 0
v_rating = {
    11: "16V",
    12: "20V",
    13: "27V",
    14: "40V",
    15: "80V",
    21: "+/-8V",
    22: "+/-10V",
    23: "+/-13.5V",
    24: "+/-20V",
    25: "+/-40V",
}
c_rating = {1: "14A", 2: "+/-10A"}
jumper = {
    1: [3, 3, 1, 3, 3, 2],
    2: [3, 1, 3, 3, 2, 3],
    3: [2, 3, 1, 1, 3, 2],
    4: [1, 3, 3, 2, 3, 3],
    5: [3, 2, 1, 3, 1, 2],
}
global ad7799

# ----- Check session record -----

try:
    record = open("session_record.txt", "r")
    for line in record:
        line_count = line_count + 1
    record.close()

    if line_count < 9:
        print(
            "Some contents of the session record file seem to have been removed.\nStarting new session..."
        )
        new_session = 1
    else:
        line_count = 0
        record = open("session_record.txt", "r")
        for line in record:
            part = line.split("-")
            rec_value.append(part[0].strip())
            line_count = line_count + 1
            if line_count == 10:
                break

        error = (
            error
            + isint(rec_value[1], 1, 2)
            + isint(rec_value[2], 1, 5)
            + isint(rec_value[3], 1, 5)
            + isint(rec_value[4], 1, 2)
            + +isint(rec_value[5], 1, 2)
        )
        if error == 0 and rec_value[5] == "1":
            error = error + isint(rec_value[6], 1, 2)
            if error == 0 and rec_value[6] == "2":
                error = error + isint(rec_value[7], 5, "x")
        if error > 0:
            new_session = 1
except:
    print("No session record found. Starting new session...")
    new_session = 1

# ----- Session Record Detected -----

if new_session == 0:
    print("\nSession record detected.\n")
    print(
        "Maximum rating: "
        + v_rating[10 * int(rec_value[1]) + int(rec_value[2])]
        + " , "
        + c_rating[int(rec_value[1])]
    )
    if rec_value[3] == "1":
        print("Data sampling rate: " + rec_value[3] + " sample per second")
    else:
        print("Data sampling rate: " + rec_value[3] + " samples per second")
    if rec_value[4] == "1":
        print("Data logging enabled")
    else:
        print("Data logging disabled")
    if rec_value[5] == "1":
        if rec_value[6] == "1":
            print("Plot enabled in tracking mode")
        else:
            print(
                "Plot enabled in non-tracking mode, latest "
                + rec_value[7]
                + " samples are displayed"
            )
    else:
        print("Plot disabled")
    print("Serial port: " + rec_value[8])

    print("\nUse same setting as previous session? (1 or 2)\n\t(1) Yes\n\t(2) No")
    response = input_int(">> ", 1, 2)
    click.clear()
    if response == 1:
        new_session = 0
        input_type = int(rec_value[1])
        v_max = int(rec_value[2])
        fs = int(rec_value[3])
        log = int(rec_value[4])
        en = int(rec_value[5])
        if en == 1:
            mode = int(rec_value[6])
            if mode == 2:
                samples = int(rec_value[7])

    elif response == 2:
        new_session = 1
elif error > 0:
    print(
        "Some contents of the session record file seem to have been modified and might cause program error.\nStarting new session..."
    )

# ----- New Session -----

if new_session == 1:

    print(
        "\nA jumper map graphic will be generated upon answering the succeeding prompts. This will help you setup the jumper configuration of the CN0548 board.\n\n"
    )
    print(
        "----- Setting the board input mode -----\n\n-Step 1 of 2: Type of measurement-\n\n(1) Unipolar-Unidirectional: The board expects non-negative voltage readings allowing it to measure a wider range of positive voltages. Input current is also expected to flow from the positive terminal to the negative terminal. This mode provides readings at a slightly higher resolution.\n\n     Input Rating: 0 to Vmax and 0 to 14A\n     Hex file to upload: ADuCM3029_demo_cn0548_demo_unipolar.hex\n\n(2) Bipolar-Bidirectional: This mode effectively splits the voltage range into positive and negative levels allowing positive and negative readings for both the voltage and current measurements. ADC resolution is lower by 1 bit compared to the previous mode.\n\n     Input Rating: -Vmax/2 to Vmax/2 and -10A to 10A\n     Hex file to upload: ADuCM3029_demo_cn0548_demo_bipolar.hex\n"
    )
    input_type = input_int("Type of measurement (1 or 2): ", 1, 2)
    new_record.append(
        str(input_type) + " - Unipolar-Unidirectional | Bipolar-Bidirectional"
    )

    print(
        "\n\n-Step 2 of 2: Voltage Range-\n\nThe maximum voltage range is 80V but the board can be configured to a more refined voltage range in order to produce higher resolution readings. Select your desired Vmax:\n\n\t(1) 16V\n\t(2) 20V\n\t(3) 27V\n\t(4) 40V\n\t(5) 80V\n"
    )
    v_max = input_int("Range (1 to 5): ", 1, 5)
    new_record.append(str(v_max) + " - 16V | 20V | 27V | 40V | 80V")

    print("\nCreating jumper map... This will take a few seconds.")
    draw_jumpers()
    gain_config(jumper[v_max])
    print(
        "You may close the jumper map window if you have configured the board jumpers"
    )
    if input_type == 1:
        jumper_uni()
        v_text = (
            "   Voltage measurement: Unipolar  (Effective Range: 0 to "
            + v_rating[10 * input_type + v_max]
            + ")\nCurrent measurement: Unidirectional (Effective range: 0 to 14A)"
        )
    else:
        jumper_bi()
        v_text = (
            "   Voltage measurement: Bipolar  (Effective Range: "
            + v_rating[10 * input_type + v_max]
            + ")\nCurrent measurement: Bidirectional (Effective range: -10A to 10A)"
        )

    turtle.setpos(0, 180)
    turtle.write(v_text, font=("Arial", 10, "bold"), align="center")
    turtle.setpos(0, -250)
    turtle.write(
        "You may close this window if you have configured the board jumpers",
        font=("Arial", 10, "bold"),
        align="center",
    )
    turtle.done()
    input("Press 'enter' key to begin configuring software parameters")

    click.clear()
    fs = input_int(
        "\n---Software Configuration---\n\nSampling Rate: The rate at which data is collected from the board - affected by your machine specs.\nSamples per second (1-5): ",
        1,
        5,
    )
    new_record.append(str(fs) + " - samples per second (1-5)")

    log = input_int(
        "\nData Logging: Records all your measurements in a csv file.\nEnable data logging?\n\t(1) Yes\n\t(2) No\n>> ",
        1,
        2,
    )
    new_record.append(str(log) + " - Data logging enabled | Data logging disabled")

    en = input_int(
        "\nPlot Window: A real-time plot of the board's IV readings.\nNote: Sampling rate can be affected if plot is enabled\n\nEnable plot?\n\t(1) Yes\n\t(2) No\n>> ",
        1,
        2,
    )
    new_record.append(str(en) + " - Plot enabled | Plot disabled")

# ----- File Creation for Data Logging -----

if log == 1:
    dt_now = datetime.now()
    dt_format = dt_now.strftime("%d-%m-%Y_%H-%M")
    filename = "CN0548_" + dt_format + ".csv"
    output = open(filename, "w")
    output.write("Voltage Reading (V),Current Reading (A)\n")
    output.close()

if en == 1:
    if new_session == 1:
        mode = input_int(
            "\nPlot Mode:\n (1) Tracking: All data points will be displayesd in the plot\n (2) Non-tracking: Only the recent x samples will be displayed\n\n>> ",
            1,
            2,
        )
    new_record.append(str(mode) + " - Tracking | Non-tracking")

    if mode == 1:
        new_record.append("x - samples to retain")
    if mode == 2:
        if new_session == 1:
            samples = input_int(
                "\nInput number of samples to retain within the plot (>=5).\nSamples to retain: ",
                5,
                "x",
            )
        new_record.append(str(samples) + " - samples to retain (>=5)")

    fig, ax1 = plt.subplots()  # Create figure for plotting
    ax2 = ax1.twinx()  # Same y-axis
    xs: List[float] = []
    ys: List[float] = []
    if mode == 2:
        for i in range(samples):
            xs.append(0)
            ys.append(0)

    def animate(i, volt, curr):  # function for animation
        v_reading = compute_voltage(
            ad7799.channel[2].value, v_max, input_type
        )  # get new voltage reading
        i_reading = compute_current(
            ad7799.channel[0].value, input_type
        )  # get new current reading
        volt.append(v_reading)
        curr.append(i_reading)
        print(
            "Voltage reading: "
            + str(v_reading)
            + "\t\t\t"
            + "Current reading: "
            + str(i_reading)
        )
        if log == 1:
            try:
                output = open(filename, "a")
                output.write(str(v_reading) + "," + str(i_reading) + "\n")
                output.close()
            except:
                print(
                    "Data point not logged, consider lowering your sample rate to match your machine specs."
                )
        if mode == 2:  # number of recent samples to be retained
            volt = volt[-samples:]
            curr = curr[-samples:]

        ax1.clear()  # Plot config
        bounds = compute_bounds(volt)
        ax1.set_ylim([bounds[0], bounds[1]])
        color = "tab:orange"
        ax1.plot(volt, label="Voltage Reading", linewidth=2.0, color=color)
        if mode == 1:
            ax1.set_xlabel("Latest " + str(len(volt)) + " samples", labelpad=10)
        else:
            ax1.set_xlabel("Latest " + str(samples) + " samples", labelpad=10)
        ax1.set_ylabel("Volts (V)", color=color)
        ax1.tick_params(
            axis="x", which="both", bottom=True, top=False, labelbottom=False
        )
        ax1.legend(bbox_to_anchor=[0.1, -0.1], ncol=2, loc="upper left", frameon=False)

        ax2.clear()
        bounds = compute_bounds(curr)
        ax2.set_ylim([bounds[0], bounds[1]])
        color = "tab:blue"
        ax2.plot(curr, label="Current Reading", linewidth=2.0, color=color)
        ax2.set_ylabel("Amperes (A)", color=color)
        ax2.tick_params(
            axis="x", which="both", bottom=True, top=False, labelbottom=False
        )
        ax2.legend(bbox_to_anchor=[0.9, -0.1], ncol=2, loc="upper right", frameon=False)
        if log == 1:
            ax2.text(
                0,
                -0.4,
                "Note: Data logging is enabled",
                size="small",
                transform=ax2.transAxes,
            )
        else:
            ax2.text(
                0,
                -0.4,
                "Note: Data logging is disabled",
                size="small",
                transform=ax2.transAxes,
            )
        title_text = (
            "CN0548 Maximum Rating: "
            + v_rating[10 * input_type + v_max]
            + " , "
            + c_rating[input_type]
        )
        plt.title(title_text, fontweight="bold")
        plt.subplots_adjust(bottom=0.30)


else:
    new_record.append("x - Tracking | Non-tracking")
    new_record.append("x - samples to retain")

if new_session == 1:
    print("\n-Connection setup-\n")
while True:
    if new_session == 1 or retry == 5:
        port = input(
            "Input Serial line (e.g. if ADICUP3029 is connected to COM7, input 'COM7' )\nSerial line: "
        )
    else:
        port = rec_value[8]
        retry = retry + 1
    try:
        context = "serial:" + port + ",115200"
        ad7799 = adi.ad7799(uri=context)
        input("\nCN0548 board detected.\nPress 'enter' key to start board operation\n")
        break
    except:
        print("Port not found\n")
new_record.append(port + " - machine-defined")
print("Voltage readings are in volts (V) while current readings are in amperes (A).")

# ---- Record session config -----

if new_session == 1:
    record = open("session_record.txt", "w")
    for i in range(9):
        record.write(str(new_record[i]))
        if i != 8:
            record.write("\n")
    record.close()

if en == 1:
    ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys), interval=(1000 / fs))
    plt.show()
    if log == 1:
        print("Data points successfully logged.\n")


else:
    while True:
        v_reading = compute_voltage(
            ad7799.channel[2].value, v_max, input_type
        )  # get new voltage reading
        i_reading = compute_current(
            ad7799.channel[0].value, input_type
        )  # get new current reading
        print(
            "Voltage reading: "
            + str(v_reading)
            + "\t\t\t"
            + "Current reading: "
            + str(i_reading)
        )
        time.sleep(1 / fs)
        if log == 1:
            try:
                output = open(filename, "a")
                output.write(str(v_reading) + "," + str(i_reading) + "\n")
                output.close()
            except:
                print(
                    "Data point not logged, consider lowering your sample rate to match your machine specs."
                )

for i in range(3):
    del ad7799.channel[0]
del ad7799._rxadc
del ad7799._ctx
