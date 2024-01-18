import time

import adi
import matplotlib.pyplot as plt
from scipy import signal

dev = adi.ad9081("ip:10.44.3.92", disable_jesd_control=False)

# Configure properties
print("--Setting up chip")

dev._ctx.set_timeout(90000)

fig = plt.figure()

eye_data_per_lane = dev._jesd.get_eye_data()
num_lanes = len(eye_data_per_lane.keys())

for lane in eye_data_per_lane:

    x = eye_data_per_lane[lane]["x"]
    y1 = eye_data_per_lane[lane]["y1"]
    y2 = eye_data_per_lane[lane]["y2"]

    plt.subplot(int(num_lanes / 2), 2, int(lane) + 1)
    plt.scatter(x, y1, marker="+", color="blue")
    plt.scatter(x, y2, marker="+", color="red")
    plt.xlim(eye_data_per_lane[lane]["graph_helpers"]["xlim"])
    plt.xlabel(eye_data_per_lane[lane]["graph_helpers"]["xlabel"])
    plt.ylabel(eye_data_per_lane[lane]["graph_helpers"]["ylabel"])
    plt.rcParams["axes.titley"] = 1.0  # y is in axes-relative coordinates.
    plt.rcParams["axes.titlepad"] = -14  # pad is in points...
    plt.title(f" Lane {lane}", loc="left", fontweight="bold")
    fig.suptitle(
        f"JESD204 MxFE 2D Eye Scan ({eye_data_per_lane[lane]['mode']}) Rate {eye_data_per_lane[lane]['graph_helpers']['rate_gbps']} Gbps"
    )
    plt.axvline(0, color="black")  # vertical
    plt.axhline(0, color="black")  # horizontal

plt.show()
