import numpy as np
import matplotlib.pyplot as plt
import mbx_functions as mbx



# Define sweep parameters
mechanicalsweepWidth = np.arange(-80, 85, 5)
elecsteerangleazim = np.arange(-20, 21, 10)
elecsteerangleelev = np.arange(-20, 21, 10)
freq = 10e9  # Frequency in Hz

BAUDRATE                    = 57600                     # for windows and Linux set to 1000000 for MacOS change BAUDRATE to 57600 and set the motor baudrate accordingly
DEVICENAME                  = "/dev/ttyUSB0"

mbx.connect(DEVICENAME, BAUDRATE)
mbx.gotoZERO()

GIMBAL_H = mbx.H
GIMBAL_V = mbx.V

gimbal_motor = GIMBAL_H

sweepangles = np.arange(-90, 91, 1)
mbx.move(gimbal_motor, 1 )

gimbal_positions = np.arange(0, 81, 1)  # Define gimbal positions from -90 to 90 degrees
mbx.move(gimbal_motor,-40)

steer_data = []

for i in range(len(gimbal_positions)):
    mbx.move(gimbal_motor,1)
    # ## Take data capture
    steer_data[i] = np.transpose(np.array(data_capture(conv)))

mbx.gotoZERO() 


