import adi

# cross point switch
cps = adi.adg2128(uri="serial:/dev/ttyACM0,230400,8n1")

# add two adg2128 cross point switches by their i2c addresses
cps.add(0x71)  # add first device, x0...x11 <---> y0...y7
cps.add(0x70)  # add another device in common Y connection x0...x23 <---> y0...y7

# open all switches
cps.open_all()

# set all x1 switches (y0...y7) with a list
cps[1] = [True, False, True, False, True, False, True, False]

# set (x23, y7) switch individually
cps[23][7] = True

# close (x5,y0) (x5,y1) (x5,y2) (x5,y3) switches together
cps.immediate = False
cps[5][0] = True
cps[5][1] = True
cps[5][2] = True
cps.immediate = True
cps[5][3] = True  # close switches together when (x5, y3) is closed

print(cps)
