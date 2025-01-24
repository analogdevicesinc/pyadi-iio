# Copyright (C) 2022 Analog Devices, Inc.

# SPDX short identifier: ADIBSD


import cmath
import sys
import time

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
    "R7_C39_C41",  # Electrode 15
]

cn0565 = adi.cn0565(uri="serial:COM7,230400,8n1n")
# reset the cross point switch

amplitude = 100
frequency = 10000

cn0565.gpio1_toggle = True
cn0565.excitation_amplitude = amplitude
cn0565.excitation_frequency = frequency
cn0565.magnitude_mode = False
cn0565.impedance_mode = True

cn0565.add(0x71)
cn0565.add(0x70)

cn0565.immediate = True

fplus = 1
splus = 4
fminus = 4
sminus = 1

if len(sys.argv) > 1:
    fplus = int(sys.argv[1])
    fminus = int(sys.argv[2])
    splus = int(sys.argv[3])
    sminus = int(sys.argv[4])

cn0565[fplus][0] = True
cn0565[splus][1] = True
cn0565[sminus][2] = True
cn0565[fminus][3] = True

print("--------------------------------------------------------------")
print("Amplitude: " + str(amplitude) + "mV")
print("Frequency: " + str(frequency) + " Hz")
print("Baud Rate: 230400")
print("--------------------------------------------------------------")
print("Electrode " + str(fplus) + " - Electrode " + str(fminus))
print(electrode_name[fplus] + " - " + electrode_name[fminus])
print("--------------------------------------------------------------")

cn0565.open_all()
cn0565[fminus][0] = True
cn0565[fminus][1] = True
cn0565[fplus][2] = True
cn0565[fplus][3] = True
res = cn0565.channel["voltage0"].raw

# print("Rectangular: " + str(res))
(mag, radph) = cmath.polar(res)
degph = radph * 180 / cmath.pi
degphb = 360 + degph
print("Rectangular: " + str(res))
print(f"Polar: Magnitude:{mag} Phase(degrees): {degph} or {degphb}")
print("Real Impedance: " + str(res.real))
print("Imaginary Impedance: " + str(res.imag))
print("--------------------------------------------------------------")
print("END")
