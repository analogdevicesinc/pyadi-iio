from time import sleep
import matplotlib.pyplot as plt
from adi import ad463x
import numpy as np

adc = ad463x(uri="ip:192.168.0.59")
for config in adc._device_config:
        print(config)
        
num_samples = 16000
adc._ctx.set_timeout(10000)
adc.rx_buffer_size = num_samples
adc.sample_rate = 2000000
adc.operating_mode = "normal_operating_mode"
adc.channels[0].hardwaregain = 1
adc.channels[0].offset = 0
if (len(adc.channels) > 1):
        adc.channels[1].offset = -800000
        adc.channels[1].hardwaregain = 0.25
try:
        adc.sample_averaging = 2
except:
        print("Sample average not supported in this mode")

plt.figure(f'{adc.name}[{config}]')
while(1):
        adc.rx()
        plt.clf()
        for idx, channel in enumerate(adc.channels):
                differential = [sample.voltage for sample in channel.data]             
                w = np.fft.fft(differential)
                freqs = np.fft.fftfreq(len(w))
                tone = abs(freqs[np.argmax(np.abs(w))] * adc.sample_rate)
                plt.plot(np.arange(0,num_samples) , differential, label=f"voltage{idx} FFT:{(int)(tone)} Hz")
                if (adc.has_common_voltage):
                        common_mode = [sample.common_mode_voltage for sample in channel.data]
                        plt.plot(np.arange(0,num_samples) , common_mode, label=f"common voltage{idx}")
        plt.subplots_adjust(bottom=0.2)
        plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), fancybox=True, shadow=True, ncol=4)
        
        plt.pause(0.25)
plt.show()
