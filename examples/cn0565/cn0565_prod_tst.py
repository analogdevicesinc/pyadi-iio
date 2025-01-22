# Copyright (C) 2022 Analog Devices, Inc.

# SPDX short identifier: ADIBSD

import cmath
import sys
import time
from datetime import datetime
from pprint import pprint

import openpyxl
import pandas as pd

import adi

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


def main():
    # ----------------------------------------------------------------------------------------------------
    # DEVICE SETTINGS
    # ----------------------------------------------------------------------------------------------------
    cn0565 = adi.cn0565(uri="serial:COM5,230400,8n1n")
    # reset the cross point switch

    cn0565.gpio1_toggle = True
    cn0565.excitation_amplitude = 100  # Set amplitude
    cn0565.excitation_frequency = 10000  # Hz # Set frequency between 10kHz to 80kHz
    cn0565.magnitude_mode = False
    cn0565.impedance_mode = True

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

    # Pair Count
    pair = 1

    passed = 0

    Electrode_Iter = iter(range(0, 16))
    for neg_e in Electrode_Iter:
        pos_e = next(Electrode_Iter)  # setting pos_e = Electrode 0 to neg_e
        cn0565.open_all()
        cn0565[pos_e][0] = True
        cn0565[pos_e][1] = True
        cn0565[neg_e][2] = True
        cn0565[neg_e][3] = True

        # Command CN0565 to measure impedance at specified electrodes using specified frequency
        res = cn0565.channel["voltage0"].raw

        print("Electrode " + str(neg_e) + " - Electrode " + str(pos_e))
        print(electrode_name[neg_e] + " - " + electrode_name[pos_e])
        print("Rectangular: " + str(res))
        (mag, radph) = cmath.polar(res)
        degph = radph * 180 / cmath.pi
        degphb = 360 + degph
        print(f"Polar: Magnitude:{mag} Phase(degrees): {degph} or {degphb}")

        print("Real Impedance: " + str(res.real))
        print("Imaginary Impedance: " + str(res.imag))
        # print('\n')

        # store impedance reading of each pair to array
        real_impedance.append(res.real)
        imag_impedance.append(res.imag)

        if pair == 1:
            if res.real >= 26000 and res.real <= 54000:
                print("---------------------------------------")
                print(
                    "Electrode "
                    + str(neg_e)
                    + " - Electrode "
                    + str(pos_e)
                    + " - PASSED!"
                )
                print("---------------------------------------\n")
                passed = passed + 1
            else:
                print("---------------------------------------")
                print(
                    "Electrode "
                    + str(neg_e)
                    + " - Electrode "
                    + str(pos_e)
                    + " - FAILED!"
                )
                print("---------------------------------------\n")

        elif pair == 2:
            if abs(res.imag) >= 110 and abs(res.imag) <= 230:
                print("---------------------------------------")
                print(
                    "Electrode "
                    + str(neg_e)
                    + " - Electrode "
                    + str(pos_e)
                    + " - PASSED!"
                )
                print("---------------------------------------\n")
                passed = passed + 1
            else:
                print("---------------------------------------")
                print(
                    "Electrode "
                    + str(neg_e)
                    + " - Electrode "
                    + str(pos_e)
                    + " - FAILED!"
                )
                print("---------------------------------------\n")

        elif pair == 3:
            if abs(res.imag) >= 15210 and abs(res.imag) <= 31600:
                print("---------------------------------------")
                print(
                    "Electrode "
                    + str(neg_e)
                    + " - Electrode "
                    + str(pos_e)
                    + " - PASSED!"
                )
                print("---------------------------------------\n")
                passed = passed + 1
            else:
                print("---------------------------------------")
                print(
                    "Electrode "
                    + str(neg_e)
                    + " - Electrode "
                    + str(pos_e)
                    + " - FAILED!"
                )
                print("---------------------------------------\n")

        elif pair == 4:
            if res.real >= 13000 and res.real <= 27000:
                print("---------------------------------------")
                print(
                    "Electrode "
                    + str(neg_e)
                    + " - Electrode "
                    + str(pos_e)
                    + " - PASSED!"
                )
                print("---------------------------------------\n")
                passed = passed + 1
            else:
                print("---------------------------------------")
                print(
                    "Electrode "
                    + str(neg_e)
                    + " - Electrode "
                    + str(pos_e)
                    + " - FAILED!"
                )
                print("---------------------------------------\n")

        elif pair == 5:
            if abs(res.imag) >= 517 and abs(res.imag) <= 1075:
                print("---------------------------------------")
                print(
                    "Electrode "
                    + str(neg_e)
                    + " - Electrode "
                    + str(pos_e)
                    + " - PASSED!"
                )
                print("---------------------------------------\n")
                passed = passed + 1
            else:
                print("---------------------------------------")
                print(
                    "Electrode "
                    + str(neg_e)
                    + " - Electrode "
                    + str(pos_e)
                    + " - FAILED!"
                )
                print("---------------------------------------\n")

        elif pair == 6:
            if res.real >= 6487 and res.real <= 13475:
                print("---------------------------------------")
                print(
                    "Electrode "
                    + str(neg_e)
                    + " - Electrode "
                    + str(pos_e)
                    + " - PASSED!"
                )
                print("---------------------------------------\n")
                passed = passed + 1
            else:
                print("---------------------------------------")
                print(
                    "Electrode "
                    + str(neg_e)
                    + " - Electrode "
                    + str(pos_e)
                    + " - FAILED!"
                )
                print("---------------------------------------\n")

        elif pair == 7:
            if abs(res.imag) >= 22010 and abs(res.imag) <= 45715:
                print("---------------------------------------")
                print(
                    "Electrode "
                    + str(neg_e)
                    + " - Electrode "
                    + str(pos_e)
                    + " - PASSED!"
                )
                print("---------------------------------------\n")
                passed = passed + 1
            else:
                print("---------------------------------------")
                print(
                    "Electrode "
                    + str(neg_e)
                    + " - Electrode "
                    + str(pos_e)
                    + " - FAILED!"
                )
                print("---------------------------------------\n")

        elif pair == 8:
            if abs(res.imag) >= 5170 and abs(res.imag) <= 10800:
                print("---------------------------------------")
                print(
                    "Electrode "
                    + str(neg_e)
                    + " - Electrode "
                    + str(pos_e)
                    + " - PASSED!"
                )
                print("---------------------------------------\n")
                passed = passed + 1
            else:
                print("---------------------------------------")
                print(
                    "Electrode "
                    + str(neg_e)
                    + " - Electrode "
                    + str(pos_e)
                    + " - FAILED!"
                )
                print("---------------------------------------\n")

        pair = pair + 1

    if passed == 8:
        print("-----------------------")
        print("BOARD STATUS: PASSED")
        print("-----------------------\n")
    else:
        print("-----------------------")
        print("BOARD STATUS: FAILED")
        print("-----------------------\n")


main()
