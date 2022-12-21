# Copyright (C) 2022 Analog Devices, Inc.

# SPDX short identifier: ADIBSD

from __future__ import absolute_import, division, print_function

import matplotlib.pyplot as plt
import numpy as np
import pyeit.eit.bp as bp
import pyeit.eit.protocol as protocol
import pyeit.mesh as mesh
from adi import cn0565
from pyeit.eit.fem import EITForward
from pyeit.mesh.shape import thorax
from pyeit.mesh.wrapper import PyEITAnomaly_Circle

# variable/board declaration
value_type = "re"  # re, im, others -> magnitude
n_el = 16  # no of electrodes
port = "COM6"
baudrate = 230400

# mesh and protocol creation
mesh = mesh.create(n_el, h0=0.08)
protocol = protocol.create(n_el, dist_exc=1, step_meas=1, parser_meas="std")

# board initialization
eit_board = cn0565(uri=f"serial:{port},{baudrate},8n1")
eit_board.excitation_frequency = 10000
eit_board.electrode_count = n_el
eit_board.force_distance = 1
eit_board.sense_distance = 1

# boundary voltage reading
voltages = eit_board.all_voltages
if value_type == "re":
    current_data = voltages[:, 0]
elif value_type == "im":
    current_data = voltages[:, 1]
else:
    current_data = np.sqrt((voltages ** 2).sum(axis=1))

# Resistor array board is fixed. Use this to get absolute impedance
v0 = np.full_like(current_data, 1)
v1 = current_data


eit = bp.BP(mesh, protocol)
eit.setup(weight="none")
ds = 192.0 * eit.solve(v1, v0, normalize=True)
points = mesh.node
triangle = mesh.element

# Plot
fig, ax = plt.subplots()
im = ax.tripcolor(points[:, 0], points[:, 1], triangle, ds)
ax.set_title(r"Impedance Measurement Using Back Projection")
ax.axis("equal")
fig.colorbar(im, ax=ax)
plt.show()
