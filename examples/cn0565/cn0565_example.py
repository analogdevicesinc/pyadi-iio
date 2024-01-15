# Copyright (C) 2022 Analog Devices, Inc.

# SPDX short identifier: ADIBSD

import cmath
import sys
import time
from datetime import datetime
from math import sqrt

import adi
import openpyxl
import pandas as pd

# Electrode Names Dictionary
electrode_name = [
    "R26_C56_C57",  # Electrode 0
    "R24_C54_C56",  # Electrode 1
    "R22_C52_C54",  # Electrode 2
    "R18_C50_C52",  # Electrode 3
    "R16_C48_C50",  # Electrode 4
    "R14_C46_C48",  # Electrode 5
    "R12_C44_C46",  # Electrode 6
    "R10_C42_C44",  # Electrode 7
    "R8_C40_C42",  # Electrode 8
    "R9_C38_C40",  # Electrode 9
    "R4_C36_C38",  # Electrode 10
    "R2_C29_C36",  # Electrode 11
    "R1_C29_C33",  # Electrode 12
    "R3_C33_C37",  # Electrode 13
    "R5_C37_C39",  # Electrode 14
    "R7_C39_C41",
]  # Electrode 15

# Function to export impedance measurements in excel file
def create_file(freq, frequency, amplitude, baudrate, real_impedance, imag_impedance):
    create = ""
    while create != "Y" or create != "N":
        create = input(
            "Would you like to generate a csv file? [Y/N] "
        )  # ask user input

        if create == "Y":
            First_E = []  # 1st of Electrode pair array
            Sec_E = []  # 2nd of Electrode pair array

            Fpos = []  # Position of Positive Forcing Lead
            Fneg = []  # Position of Negative Forcing Lead
            Spos = []  # Position of Positive Sensing Lead
            Sneg = []  # Position of Negative Sensing Lead

            item_num = []
            item = 0

            for neg_e in range(1, 16):
                for pos_e in range(0, neg_e):
                    #############################################################
                    # For generation of excel file containing impedance readings
                    # Array storing assignment:
                    First_E.append("E" + str(pos_e))
                    First_E.append(electrode_name[pos_e])
                    Sec_E.append("E" + str(neg_e))
                    Sec_E.append(electrode_name[neg_e])
                    Fpos.append(pos_e)
                    Fpos.append("")
                    Fneg.append(neg_e)
                    Fneg.append("")
                    Spos.append(neg_e)
                    Spos.append("")
                    Sneg.append(pos_e)
                    Sneg.append("")
                    item = item + 1
                    item_num.append(item)
                    item_num.append("")

                results = []
                results.append("")
                results.append("Amplitude")
                results.append(str(amplitude) + " mV")
                results.append("Frequency")
                results.append(str(frequency) + " Hz")
                results.append("Baud Rate")
                results.append(str(baudrate))

            for q in range(0, 233):
                results.append("")

            electrode_data = {
                "1st Electrode": First_E,
                "2nd Electrode": Sec_E,
                "F+": Fpos,
                "F-": Fneg,
                "S+": Spos,
                "S-": Sneg,
                "Real 1": array(real_impedance),
                "Imaginary 1": array(imag_impedance),
                "Results": results,
            }

            DF = pd.DataFrame.from_dict(electrode_data).set_index([item_num])

            file_name = "cn0565_example_data.csv"
            DF.to_csv(file_name)
            print("File created! Filename: " + file_name)
            print("End!")
            break

        elif create == "N":
            print("End!")
            break
        else:
            print("Invalid input.")


def array(x):  # Function to convert array size to maximum size of data frame

    total_pairs = len(x)
    new_array = []

    for a in range(0, total_pairs):
        new_array.append(x[a])
        new_array.append("")
    return new_array


def main():
    # ----------------------------------------------------------------------------------------------------
    # DEVICE SETTINGS
    # ----------------------------------------------------------------------------------------------------
    cn0565 = adi.cn0565(uri="serial:COM7,230400,8n1n")
    # reset the cross point switch

    amplitude = 100
    frequency = 10000
    baudrate = 230400

    cn0565.gpio1_toggle = True
    cn0565.excitation_amplitude = amplitude  # Set amplitude
    cn0565.excitation_frequency = frequency  # Hz # Set frequency between 10kHz to 80kHz
    cn0565.magnitude_mode = False
    cn0565.impedance_mode = True

    print("--------------------------------------------------------------")
    print("Amplitude: " + str(amplitude) + "mV")
    print("Frequency: " + str(frequency) + " Hz")
    print("Baud Rate: " + str(baudrate))
    print("--------------------------------------------------------------\n")

    cn0565.immediate = True

    cn0565.add(0x71)
    cn0565.add(0x70)

    fplus = 1
    splus = 4
    fminus = 4
    sminus = 1

    cn0565[fplus][0] = True
    cn0565[splus][1] = True
    cn0565[sminus][2] = True
    cn0565[fminus][3] = True

    # Array for Real & Imaginary values per iteration
    real_impedance = []
    imag_impedance = []

    for neg_e in range(1, 16):  # setting neg_e = Electrode 1 to Electrode 15

        for pos_e in range(0, neg_e):  # setting pos_e = Electrode 0 to neg_e

            if pos_e == neg_e:
                print("Forcing electrodes are shorted in the given assignments.")
                return False

            cn0565.open_all()
            cn0565[pos_e][0] = True
            cn0565[pos_e][1] = True
            cn0565[neg_e][2] = True
            cn0565[neg_e][3] = True

            # Command CN0565 to measure impedance at specified electrodes using specified frequency
            res = cn0565.channel["voltage0"].raw

            print("--------------------------------------------------------------")
            print("Electrode " + str(neg_e) + " - Electrode " + str(pos_e))
            print(electrode_name[neg_e] + " - " + electrode_name[pos_e])
            print("--------------------------------------------------------------")
            print("Rectangular: " + str(res))
            (mag, radph) = cmath.polar(res)
            degph = radph * 180 / cmath.pi
            degphb = 360 + degph
            print(f"Polar: Magnitude:{mag} Phase(degrees): {degph} or {degphb}")

            print("Real Impedance: " + str(res.real))
            print("Imaginary Impedance: " + str(res.imag))
            print("--------------------------------------------------------------")
            print("\n")

            # store impedance reading of each pair to array
            real_impedance.append(res.real)
            imag_impedance.append(res.imag)

    """
    # average of real impedance values
    ave_real = sum(real_impedance)/len(real_impedance)

    print('===========================================================')
    print("*** Real values average: " + str(ave_real))
    print('-----------------------------------------------------------')

    # average of imaginary impedance values
    ave_imag = sum(imag_impedance)/len(imag_impedance)

    print("*** Imaginary values average: " + str(ave_imag))
    print('===========================================================')

    Vmag = sqrt((ave_imag**2) + (ave_real**2))
    print("*** |Impedance|: " + str(Vmag))
    print('===========================================================\n')
    print("END")
    """

    # function to ask user if excel file containing impedance data is to be generated
    create_file(
        cn0565.excitation_frequency,
        frequency,
        amplitude,
        baudrate,
        real_impedance,
        imag_impedance,
    )


main()
