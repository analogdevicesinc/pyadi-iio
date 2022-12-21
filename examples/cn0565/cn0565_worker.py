# Copyright (C) 2022 Analog Devices, Inc.

# SPDX short identifier: ADIBSD

import sys

import matplotlib.pyplot as plt
import numpy as np
import pyeit.eit.bp as bp
import pyeit.eit.greit as greit
import pyeit.eit.jac as jac
import pyeit.eit.protocol as protocol
import pyeit.mesh as mesh
import serial
import serial.threaded
from pyeit.eit.interp2d import sim2pts
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class CN0565_Worker(QThread):
    doneCompute = pyqtSignal()
    # signal for getting the electrode
    doneGetSupportedElectrodeCount = pyqtSignal(np.ndarray)
    # signal for computing

    # initialization for the QThread
    def __init__(self, parent=None, figure=None):
        super(CN0565_Worker, self).__init__(parent)
        self.exiting = False  # keeps the run running
        self.set_baseline = True
        self.pVal = 0.5
        self.lambdaVal = 0.5
        self.reconstruction = "greit"
        # declaration for interface (intf)
        self.freq = 10000
        self.el = 16
        self.h0 = 0.08
        self.force_distance = 1
        self.sense_distance = 1
        self.fixed_ref = True
        self.figure = figure
        self.intf = None
        self.value_type = "re"

        # declaration for protocol
        self.dist_exc = 1
        self.step_meas = 1
        self.parser_meas = "std"
        # plot
        self.mesh_obj = []
        self.ds = []
        self.eit = None
        self.electrode_count_available = np.ndarray([8, 16, 32])
        self.doneGetSupportedElectrodeCount.emit(self.electrode_count_available)
        print("Worker Created")

    def plot(self, figure, mesh_obj, ds):
        """ Setup display"""
        axis_size = [-1.2, 1.2, -1.2, 1.2]
        self.figure.clear()
        self.ax = figure.add_subplot()
        pts = self.mesh_obj.node
        tri = self.mesh_obj.element
        x, y = pts[:, 0], pts[:, 1]

        if self.reconstruction == "bp":
            im = self.ax.tripcolor(pts[:, 0], pts[:, 1], tri, ds)
            self.ax.set_title(r"BP")
            self.ax.axis("equal")
            self.figure.colorbar(im)

        elif self.reconstruction == "jac":
            im = self.ax.tripcolor(x, y, tri, ds, shading="flat")
            self.ax.set_title(r"JAC")
            self.ax.axis("equal")
            self.figure.colorbar(im)

        elif self.reconstruction == "greit":
            im = self.ax.imshow(np.real(ds))
            self.ax.set_title(r"GREIT")
            self.ax.axis("equal")
            self.figure.colorbar(im)

    def updatePvalue(self, p=0.5):
        self.pVal = p
        self.reSetup = True

    def updateLambdaValue(self, lamb=0.5):
        self.lambdaVal = lamb
        self.reSetup = True

    def updateReconstructionMethod(self, reconstruction="jac"):
        self.reconstruction = reconstruction
        self.reSetup = True

    def setValueType(self, value_type="re"):
        self.value_type = value_type

    def setBaseline(self):
        self.set_baseline = True

    def run(self):
        self.exiting = False
        # self.electrode_count_available = self.intf.electrode_count_available()
        # self.doneGetSupportedElectrodeCount.emit(self.electrode_count_available)

        print("Electrode count is:", self.el)
        self.intf.excitation_frequency = self.freq
        self.intf.electrode_count = self.el
        self.intf.force_distance = self.force_distance
        self.intf.sense_distance = self.sense_distance
        self.mesh_obj = mesh.create(n_el=self.el, h0=self.h0)
        protocol_obj = protocol.create(
            self.el, self.dist_exc, self.step_meas, self.parser_meas
        )

        print(
            "Mesh built: "
            + str(self.el)
            + " "
            + str(self.h0)
            + " "
            + str(self.force_distance)
            + " "
            + str(self.sense_distance)
        )
        while not self.exiting:
            voltages = self.intf.all_voltages

            if self.value_type == "re":
                current_data = voltages[:, 0]
            elif self.value_type == "im":
                current_data = voltages[:, 1]
            else:
                current_data = np.sqrt((voltages ** 2).sum(axis=1))

            if self.set_baseline:
                v0 = current_data
                self.set_baseline = False
                print("Done baseline!")
            else:
                v1 = current_data
                self.solver(v0, v1, protocol_obj)
            print("Plotting... ")

    def solver(self, v0, v1, protocol_obj):
        if self.reconstruction == "bp":
            self.eit = bp.BP(self.mesh_obj, protocol_obj)
            self.eit.setup(weight="none")
            self.ds = self.eit.solve(v1, v0, normalize=True)
            self.plot(self.figure, self.mesh_obj, self.ds)
            self.doneCompute.emit()

        elif self.reconstruction == "jac":
            self.eit = jac.JAC(self.mesh_obj, protocol_obj)
            self.eit.setup(
                p=0.5, lamb=0.01, method="kotre", perm=1, jac_normalized=True
            )
            # the normalize for BP when dist_exc>4 should always be True
            self.ds = self.eit.solve(v1, v0, normalize=True)
            self.ds = sim2pts(
                self.mesh_obj.node, self.mesh_obj.element, self.ds
            )  # changes here
            self.plot(self.figure, self.mesh_obj, self.ds)
            self.doneCompute.emit()

        elif self.reconstruction == "greit":
            self.eit = greit.GREIT(self.mesh_obj, protocol_obj)
            self.eit.setup(p=0.50, lamb=0.01, perm=1, jac_normalized=True)
            # the normalize for Greit when dist_exc>4 should always be True
            self.ds = self.eit.solve(v1, v0, normalize=True)
            x, y, self.ds = self.eit.mask_value(self.ds, mask_value=np.NAN)
            self.plot(self.figure, self.mesh_obj, self.ds)
            self.doneCompute.emit()
