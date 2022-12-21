# Copyright (C) 2022 Analog Devices, Inc.

# SPDX short identifier: ADIBSD

from __future__ import absolute_import, division, print_function

import matplotlib.pyplot as plt
import numpy as np
import pyeit.eit.bp as bp
import pyeit.eit.greit as greit
import pyeit.eit.jac as jac
import pyeit.eit.protocol as protocol
import pyeit.mesh as mesh
from adi import cn0565
from pyeit.eit.fem import EITForward
from pyeit.eit.interp2d import sim2pts
from pyeit.mesh.shape import thorax
from pyeit.mesh.wrapper import PyEITAnomaly_Circle

print(" 1. build mesh, protocol and setup board ")
value_type = "re"  # re, im, others -> magnitude
n_el = 16  # no of electrodes
mesh_obj = mesh.create(n_el, h0=0.08)
port = "COM7"
baudrate = 230400

protocol_obj = protocol.create(n_el, dist_exc=1, step_meas=1, parser_meas="std")

eit_board = cn0565(uri=f"serial:{port},{baudrate},8n1")
eit_board.excitation_frequency = 10000
eit_board.electrode_count = n_el
eit_board.force_distance = 1
eit_board.sense_distance = 1

print("2. Read actual boundary voltages from CN0565 ")
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

# 3.1 naive inverse solver using back-projection
eit = bp.BP(mesh_obj, protocol_obj)
eit.setup(weight="none")
# the normalize for BP when dist_exc>4 should always be True
ds = 192.0 * eit.solve(v1, v0, normalize=True)

# extract node, element, alpha
pts = mesh_obj.node
tri = mesh_obj.element
x, y = pts[:, 0], pts[:, 1]

# draw
fig, axes = plt.subplots(3, 1, constrained_layout=True, figsize=(6, 12))
# reconstructed
ax = axes[0]
im = ax.tripcolor(pts[:, 0], pts[:, 1], tri, ds)
ax.set_title(r"Object Impedance using Back Projection")
ax.axis("equal")
fig.colorbar(im, ax=ax)

# 3.2 JAC solver
# Note: if the jac and the real-problem are generated using the same mesh,
# then, data normalization in solve are not needed.
# However, when you generate jac from a known mesh, but in real-problem
# (mostly) the shape and the electrode positions are not exactly the same
# as in mesh generating the jac, then data must be normalized.
eit = jac.JAC(mesh_obj, protocol_obj)
eit.setup(p=0.5, lamb=0.01, method="kotre", perm=1, jac_normalized=True)
ds = eit.solve(v1, v0, normalize=True)
ds_n = sim2pts(pts, tri, np.real(ds))

ax1 = axes[1]
ax1.set_title(r"Object Impedance using Gauss-Newton solver (JAC)")
im = ax1.tripcolor(x, y, tri, ds_n, shading="flat")
ax1.axis("equal")
fig.colorbar(im, ax=ax1)

# 3.3 Construct using GREIT """
eit = greit.GREIT(mesh_obj, protocol_obj)
eit.setup(p=0.50, lamb=0.01, perm=1, jac_normalized=True)
ds = eit.solve(v1, v0, normalize=True)
x, y, ds = eit.mask_value(ds, mask_value=np.NAN)

ax2 = axes[2]
ax2.set_title(r"Object Impedance using 2D GREIT")
im = ax2.imshow(np.real(ds), interpolation="none", cmap=plt.cm.viridis)
fig.colorbar(im, ax=ax2)
ax2.axis("equal")
plt.show()
