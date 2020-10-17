import adi
import matplotlib.pyplot as plt
import numpy as np

uri = "ip:analog"
captures = 100
samples_per_capture = 2**12
fan_mode = 1

xl = adi.adxl1002(uri)
xl.rx_buffer_size = samples_per_capture

for i in range(captures):
    data = xl.rx()
    all_data = data if i==0 else np.vstack((all_data,data))
    # Plot
    plt.clf()
    plt.plot(data)
    plt.show(block=False)
    plt.pause(0.1)


np.savetxt("mode{}.csv".format(fan_mode), all_data, delimiter="\t")