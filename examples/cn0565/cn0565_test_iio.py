import cmath
import csv
import sys
import time

import adi
import numpy as np
import serial.tools.list_ports
from EitSerialReaderProtocol import EIT, EIT_Interface


def main():
    # Electrodes
    # Values can be from 0 to 23
    f_plus = 0
    f_minus = 1
    s_plus = 2
    s_minus = 3

    # Testing
    ref_res = 2000

    # Measurement
    mode = "Z"

    # Frequency
    freq = 10

    # Serial Port Settings
    cmprt = list(serial.tools.list_ports.comports())
    active_port = cmprt[0]
    string_port = str(active_port)
    port = string_port.split()[0]
    print("ACTIVE PORT : " + str(port))
    baudrate = 230400
    bIIO = True

    if freq > 80 or freq < 10:
        print("Provide a frequency between 10 and 80 kHz")
        return False

    # Open CN0565
    intf = EIT_Interface(port, baudrate, bIIO)

    with open("cn0565_test.csv", "w", newline="") as csvfile:

        z_writer = csv.writer(
            csvfile, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL
        )
        good = 0

        r_array = []
        std_array = []

        for i in range(1):

            z_val = []
            Z_sum = []

            # neg_e = negative electrode
            # pos_e = positive electrode

            for neg_e in range(1, 16):

                z_sub = []
                # z_sub.append(neg_e)

                for pos_e in range(0, neg_e):
                    if pos_e == neg_e:
                        print(
                            "Forcing electrodes are shorted in the given assignments."
                        )
                        return False

                    # Command CN0565 to measure impedance at specified electrodes using specified frequency
                    res = intf.query(freq, pos_e, neg_e, neg_e, pos_e, mode)
                    z_sub.append(res.real)
                    Z_sum.append(res.real)
                    time.sleep(0.1)

                    """
                    # Check if measurement is close to reference resistance
                    if (res.real > ref_res * 1.05) or (res.real < ref_res * 0.95):
                        print("Board failed at (" + str(pos_e) + ", " + str(neg_e) + ") with " + str(res.real))
                        return False
                    else:
                        print("(" + str(pos_e) + ", " + str(neg_e) + "): " + str(res.real))
                    """

                z_writer.writerow(z_sub)
                z_val.append(z_sub)

            std = np.std(Z_sum)

            std_array.append(std)

            if std < 100:
                Trial = "Trial "
                str_i = str(i + 1)
                colon = ": "
                Passed = "Board Passed!"
                result = Trial + str_i + colon + Passed
                good = good + 1

            else:
                Trial = "Trial "
                str_i = str(i + 1)
                colon = ": "
                Passed = "Board Failed!"
                result = Trial + str_i + colon + Passed

            r_array.append(result)

    print("================================================")
    print(Passed)
    print(std)
    print("================================================")


main()
