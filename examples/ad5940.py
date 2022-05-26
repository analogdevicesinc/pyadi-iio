import sys
import time

import adi

afe = adi.ad5940(uri="serial:/dev/ttyACM0,230400,8n1n")
# reset the cross point switch
afe.gpio1_toggle = True
afe.excitation_amplitude = 300
afe.excitation_frequency = 80000
afe.magnitude_mode = False
afe.impedance_mode = True

cps = adi.adg2128(uri="serial:/dev/ttyACM0,230400,8n1n")
cps.add(0x71)
cps.add(0x70)

fplus = 1
splus = 4
fminus = 4
sminus = 1

if len(sys.argv) > 1:
    fplus = int(sys.argv[1])
    fminus = int(sys.argv[2])
    splus = int(sys.argv[3])
    sminus = int(sys.argv[4])

cps[fplus][0] = True
cps[splus][1] = True
cps[sminus][2] = True
cps[fminus][3] = True

print(afe.channel["voltage0"].raw)
