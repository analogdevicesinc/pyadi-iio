import time

import adi
import matplotlib.pyplot as plt
from scipy import signal
import numpy as np

devices = ["axi-ad9084-rx-hpc", "axi-ad9084-rx1", "axi-ad9084-rx2", "axi-ad9084-rx3"]

for device_name in devices:
    dev = adi.ad9084("ip:10.44.3.77", device=device_name, disable_jesd_control=False)

    # Configure properties
    print("--Setting up chip")

    dev._ctx.set_timeout(90000)

    fig = plt.figure(figsize=(19.20,10.80))


    eye_data_per_lane = dev._jesd.get_eye_data(lanes=[7, 11, 19, 23])

    num_lanes = len(eye_data_per_lane.keys())

    for i, lane in enumerate(eye_data_per_lane):

        x = eye_data_per_lane[lane]["x"]
        y1 = eye_data_per_lane[lane]["y1"]
        y2 = eye_data_per_lane[lane]["y2"]

        ax1 = plt.subplot(int(num_lanes / 2), 2, int(i) + 1)
        plt.scatter(x, y1, marker="+", color="blue")
        plt.scatter(x, y2, marker="+", color="red")
        plt.xlim(eye_data_per_lane[lane]["graph_helpers"]["xlim"])
        plt.xlabel(eye_data_per_lane[lane]["graph_helpers"]["xlabel"])
        plt.ylabel(eye_data_per_lane[lane]["graph_helpers"]["ylabel"])
        plt.rcParams["axes.titley"] = 1.0  # y is in axes-relative coordinates.
        plt.rcParams["axes.titlepad"] = -14  # pad is in points...
        plt.title(f" Lane {lane}", loc="left", fontweight="bold")
        fig.suptitle(
            f"JESD204 Apollo 2D Eye Scan device:{device_name} Rate {eye_data_per_lane[lane]['graph_helpers']['rate_gbps']} Gbps"
        )
        plt.axvline(0, color="black")  # vertical
        plt.axhline(0, color="black")  # horizontal
        plt.grid(True)
        # Add secondary x-axis
        x_norm = [round(n * 0.1, 2) for n in range(11)]
        x.sort()
        x = np.linspace(min(x), max(x), 11)

        ax2 = ax1.twiny()
        ax2.set_xlim(ax1.get_xlim())
        ax2.set_xticks(x)
        ax2.set_xticklabels(x_norm)
        ax2.set_xlabel("Unit Interval (UI)")

    print('saving:' + device_name + '.png\n')
    plt.savefig(device_name + '.png', dpi=600)
    plt.show(block=False)
    plt.pause(0.1)

