import matplotlib.pyplot as plt
from adi import ad4630
import numpy as np

adc = ad4630(uri="ip:192.168.0.130")
adc.rx_buffer_size = 500
adc.sample_rate = 2000000

try:
        adc.sample_averaging = 16
except:
        print("Sample average not supported in this mode")

data = adc.rx()

for ch in range(0, len(data)):
        x = np.arange(0,len(data[ch])) 
        plt.figure(adc._ctrl._channels[ch]._name)
        plt.plot(x,data[ch]) 
plt.show()
