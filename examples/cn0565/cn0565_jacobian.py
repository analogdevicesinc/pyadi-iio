# Copyright (C) 2022 Analog Devices, Inc.

# SPDX short identifier: ADIBSD

from __future__ import absolute_import, division, print_function

import matplotlib.pyplot as plt
import numpy as np
import pyeit.eit.jac as jac
import pyeit.eit.protocol as protocol
import pyeit.mesh as mesh
from adi import cn0565
from pyeit.eit.fem import EITForward
from pyeit.eit.interp2d import sim2pts
from pyeit.mesh.shape import thorax
from pyeit.mesh.wrapper import PyEITAnomaly_Circle

# variable and parameter declaration
value_type = "re"  # re, im, others -> magnitude
n_el = 16  # no of electrodes
port = "COM6"
baudrate = 230400

# board initialization
eit_board = cn0565(uri=f"serial:{port},{baudrate},8n1")
eit_board.excitation_frequency = 10000
eit_board.electrode_count = n_el
eit_board.force_distance = 1
eit_board.sense_distance = 1

# mesh and protocol creation
mesh = mesh.create(n_el, h0=0.08)
protocol = protocol.create(n_el, dist_exc=1, step_meas=1, parser_meas="std")

# Read actual boundary voltages from CN0565
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

# naive inverse solver using jacobian
eit = jac.JAC(mesh, protocol)
eit.setup(p=0.5, lamb=0.01, method="kotre", perm=1, jac_normalized=True)
# the normalize for BP when dist_exc>4 should always be True
ds = eit.solve(v1, v0, normalize=True)
points = mesh.node
triangle = mesh.element
x, y = points[:, 0], points[:, 1]
ds_n = sim2pts(points, triangle, np.real(ds))

# plot
fig, ax = plt.subplots()
im = ax.tripcolor(x, y, triangle, ds_n, shading="flat")
ax1.set_title(r"Reconstituted $\Delta$ Conductivities")
ax1.axis("equal")
fig.colorbar(im, ax=ax1)
plt.show()
