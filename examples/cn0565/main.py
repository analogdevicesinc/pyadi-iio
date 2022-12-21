# Copyright (C) 2022 Analog Devices, Inc.

# SPDX short identifier: ADIBSD

import argparse
import os
import os.path
import sys
from types import MethodType

import adi
import realtimeEITUI
import serial
import serial.tools.list_ports
from cn0565_worker import CN0565_Worker
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from PyQt5 import QtCore, QtGui, QtWidgets

__tool_name__ = "Real Time Electrical Impedance Tomography"
__banner__ = "Analog Devices"
__version__ = "0.0.2.0"
__release_date__ = "Oct-2023"


def rebinder(f):
    if not isinstance(f, MethodType):
        raise TypeError("rebinder was intended for rebinding methods")

    def wrapper(*args, **kw):
        return f(*args, **kw)

    return wrapper


class RealtimeEIT(QtWidgets.QMainWindow, realtimeEITUI.Ui_MainWindow):
    def __init__(self, port, baudrate, iio, el, parent=None):
        super(RealtimeEIT, self).__init__(parent)
        self.port = port
        self.baudrate = baudrate
        self.iio = iio
        self.intf = None
        self.setupUi(self)
        self.setFixedSize(self.size())
        sizeX = 3.7  # 1151/96
        sizeY = 1.9  # 401/96
        size = (sizeX, sizeY)
        self.figure = Figure(size)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.vLayout_plot.addWidget(self.toolbar)
        self.vLayout_plot.addWidget(self.canvas)
        self.connected = False

        # functionality
        self.sldr_freq.valueChanged.connect(self.freqValueChanged)
        self.sldr_p.valueChanged.connect(self.pValueChanged)
        self.sldr_lambda.valueChanged.connect(self.lambdaValueChanged)
        self.btn_refresh_comm.clicked.connect(self.update_cmb_comm_select)
        self.btn_baseline.clicked.connect(self.setBaseline)
        self.btn_connect.clicked.connect(self.comm_connect)
        self.rbtn_real.toggled.connect(lambda: self.btnState(self.rbtn_real))
        self.rbtn_imaginary.toggled.connect(lambda: self.btnState(self.rbtn_imaginary))
        self.rbtn_magnitude.toggled.connect(lambda: self.btnState(self.rbtn_magnitude))
        self.rbtn_bp.toggled.connect(lambda: self.btnState(self.rbtn_bp))
        self.rbtn_jac.toggled.connect(lambda: self.btnState(self.rbtn_jac))
        self.rbtn_greit.toggled.connect(lambda: self.btnState(self.rbtn_greit))

        # workers
        self.worker = CN0565_Worker(figure=self.figure)
        self.worker.doneCompute.connect(self.updatePlot)
        self.worker.doneGetSupportedElectrodeCount.connect(self.updateElectrodeCount)

        # function declaration
        self.freqValueChanged()
        self.pValueChanged()
        self.lambdaValueChanged()
        self.rbtn_bp.toggle()
        self.rbtn_real.toggle()
        self.update_cmb_comm_select()

        self.updateElectrodeCount(el)

        index = self.cmb_supported_electrode_count_select.findText(
            str(el), QtCore.Qt.MatchFixedString
        )
        if index >= 0:
            self.cmb_supported_electrode_count_select.setCurrentIndex(index)

    def updatePlot(self):
        self.canvas.draw()

    def comm_connect(self):
        if self.btn_connect.text() == "Connect":
            self.btn_connect.setText("Disconnect")
            self.port = self.cmb_comm_select.currentData().strip()
            if self.connected == True:
                self.worker.intf = self.intf
                self.worker.start()
            else:
                try:
                    print(f"Serial: {self.port} baudrate: {self.baudrate}")
                    self.intf = adi.cn0565(
                        uri=f"serial:{self.port},{self.baudrate},8n1"
                    )
                    self.worker.intf = self.intf
                    self.worker.start()
                except Exception as e:
                    print(f"Serial Connection Error! {e}")
                    self.btn_connect.setText("Connect")
                    del self.intf
                self.connected = True

        else:
            # TODO: stop hardware first
            self.btn_connect.setText("Connect")
            print("Disconnected!")
            print("Ready for another run...")
            self.worker.exiting = True
            self.worker.quit()

    def btnState(self, btn):
        if btn.isChecked():
            print(btn.text() + " is chosen")
            if btn.text() == "Real":
                self.worker.setValueType("re")
            if btn.text() == "Imaginary":
                self.worker.setValueType("im")
            if btn.text() == "Magnitude":
                self.worker.setValueType("mag")
            if btn.text() == "BP":
                self.worker.updateReconstructionMethod("bp")
            if btn.text() == "JAC":
                self.worker.updateReconstructionMethod("jac")
            if btn.text() == "GREIT":
                self.worker.updateReconstructionMethod("greit")

    def setBaseline(self):
        self.worker.setBaseline()

    def updatePlot(self):
        self.canvas.draw()

    def updateElectrodeCount(self, supported_electrode_count):
        """
        TODO: Update the Electrode counts supported
        """
        self.cmb_supported_electrode_count_select.clear()

        if isinstance(supported_electrode_count, int):
            supported_electrode_count = [supported_electrode_count]

        for electrode_count in supported_electrode_count:
            self.cmb_supported_electrode_count_select.addItem(str(electrode_count))

    def freqValueChanged(self):
        self.freqVal = int(self.sldr_freq.value())
        self.sbox_freq.setProperty("value", self.freqVal)
        self.worker.freq = self.freqVal

    def update_cmb_comm_select(self):
        self.cmb_comm_select.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.cmb_comm_select.addItem(
                port.device + ": " + port.description, port.device
            )

    def pValueChanged(self):
        self.pVal = int(self.sldr_p.value()) / 100.0
        self.sbox_p.setProperty("value", self.pVal)
        self.worker.updatePvalue(p=self.pVal)

    def lambdaValueChanged(self):
        self.lambdaVal = int(self.sldr_lambda.value()) / 100.0
        self.sbox_lambda.setProperty("value", self.lambdaVal)
        self.worker.updateLambdaValue(lamb=self.lambdaVal)

    def baselineDragEnterEvent(self, event):
        event.accept()

    def inputDragEnterEvent(self, event):
        event.accept()


def main(argv):
    ap = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    ap.add_argument(
        "-b",
        "--baudrate",
        action="store",
        nargs="?",
        help="Serial port baudrate.",
        default=230400,
    )

    ap.add_argument(
        "-e",
        "--el",
        action="store",
        nargs="?",
        help="Number of electrodes.",
        default=16,
    )

    ap.add_argument(
        "-i",
        "--iio",
        action="store_true",
        help="Use libiio instead of custom serial protocol.",
        default=False,
    )
    args = ap.parse_args()

    el = int(args.el)
    if el not in [8, 16, 32]:
        el = 16
    app = QtWidgets.QApplication(sys.argv)
    form = RealtimeEIT(None, args.baudrate, args.iio, el)
    form.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main(sys.argv[1:])
