from EitSerialReaderProtocol import EIT, EIT_Interface
import sys
import os
import os.path
import getopt
import cmath
import argparse
import textwrap
import adi

def main():
    f_plus=0
    f_minus=1
    s_plus=2
    s_minus=3
    mode='V'
    freq=10
    sercom=None

    ap = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    ap.add_argument("-p", "--port",
                    action="store",
                    nargs="?",
                    help="Serial port device.",
                    default=None)

    ap.add_argument("-b", "--baudrate",
                    action="store",
                    nargs="?",
                    help="Serial port baudrate.",
                    default=230400)

    ap.add_argument("-f", "--frequency",
                    action="store",
                    nargs="?",
                    help="Excitation Frequency in KHz.",
                    default=10)

    ap.add_argument("-z", "--impedance",
                    action="store_true",
                    help="Read impedance instead of voltage.",
                    default=False)

    ap.add_argument("-i", "--iio",
                    action="store_true",
                    help="Use libiio instead of custom serial protocol.",
                    default=False)

    ap.add_argument("-r", "--rectangular",
                    action="store_true",
                    help=textwrap.dedent('''\
                    Show readings in rectangular form.
                    If not used, measurements will be in polar form
                    '''),
                    default=False)
    ap.add_argument("-v", "--verbose",
                    action="store_true",
                    help=textwrap.dedent('''\
                    Show measurements in polar form
                    '''),
                    default=False)

    ap.add_argument("-e", "--electrodes",
                    action="store",
                    nargs=4,
                    metavar=('F+', 'F-', 'S+', 'S-'),
                    dest='electrodes',
                    help=textwrap.dedent('''\
                    Selected electrodes for the measurement:
                    Example: -e 0 3 1 2
                    This sets the following:
                        F+ to electrode 0
                        F- to electrode 3
                        S+ to electrode 1
                        S- to electrode 2
                    '''),
                    default=False)

    args = ap.parse_args()
    
    electrodes = list(map(int, args.electrodes))
    for el in electrodes:
        if el>=16 or el<0:
            print("Invalid electrode assignment.")
            return False
    if not (len(electrodes)==4):
        print("Invalid number of electrode assignments.")
        return False
    
    f_plus,f_minus,s_plus,s_minus = electrodes
    if f_plus==f_minus:
        print("Forcing electrodes are shorted in the given assignments.")
        return False
    
    freq = int(args.frequency)
    if freq > 80 or freq < 10:
        print("Provide a frequency between 10 and 80 kHz")
        return False
    
    if args.impedance:
        mode='Z'
    else:
        mode='V'

    intf = EIT_Interface(args.port, args.baudrate, args.iio)
    res= intf.query(freq, f_plus, f_minus, s_plus, s_minus, mode)
    print("Rectangular: " + str(res))
    (mag,radph)=cmath.polar(res)
    degph = radph*180/cmath.pi
    degphb = 360+degph
    print(f"Polar: Magnitude:{mag} Phase(degrees): {degph} or {degphb}")

if __name__=='__main__':
    main()