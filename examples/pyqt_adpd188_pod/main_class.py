import os
import sys
import threading
from queue import Full, Queue

import mainwindow
import pyqtgraph as pg
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QObject, QThread, pyqtSignal

import adi


class ack_thread(QThread):
    def __init__(self, device, parent=None, run_source=False):
        QThread.__init__(self, parent)
        self.device = device
        self.run_source = run_source

    @property
    def sfile(self):
        return self._sfile

    @sfile.setter
    def sfile(self, value):
        self._sfile = value

    @property
    def queue(self):
        return self._queue

    @queue.setter
    def queue(self, value):
        self._queue = value

    def run(self):
        print("Thread running")
        while threading.main_thread().is_alive():
            if not self.run_source:
                continue
            data = self.device.rx()
            try:
                self.queue.put_nowait(data)
            except Full:
                print("Warning queue full!!")
                continue
            self.data_rdy.emit()
            if not self.run_source:
                self.device.rx_destroy_buffer()

    data_rdy = pyqtSignal(name="data_rdy")


class adpd188_8pod_gui(mainwindow.Ui_MainWindow):
    adpd_pod_tab = []
    caturing = 0
    queue = []
    add_comment = [False, False, False, False]
    save_file = []
    thread_q = []
    plot_tab = []
    run_source = False
    colors = [
        pg.mkPen(color=(255, 0, 0)),
        pg.mkPen(color=(0, 255, 0)),
        pg.mkPen(color=(0, 0, 255)),
        pg.mkPen(color=(255, 0, 255)),
        pg.mkPen(color=(255, 255, 0)),
        pg.mkPen(color=(0, 255, 255)),
        pg.mkPen(color=(255, 255, 255)),
        pg.mkPen(color=(0, 128, 255)),
        pg.mkPen(color=(128, 0, 255)),
        pg.mkPen(color=(0, 255, 128)),
        pg.mkPen(color=(128, 255, 0)),
        pg.mkPen(color=(255, 128, 0)),
        pg.mkPen(color=(255, 0, 128)),
        pg.mkPen(color=(255, 255, 128)),
        pg.mkPen(color=(255, 128, 255)),
        pg.mkPen(color=(128, 255, 255)),
    ]

    def plot_data(self):
        data_tab = []
        for idx, pod in enumerate(self.adpd_pod_tab):
            data_tab.append(self.queue[idx].get(block=True, timeout=2))

        if not self.run_source:
            return
        for idx, data in enumerate(data_tab):
            t_data = zip(*data)
            for dim in t_data:
                data_str = " ".join(map(str, dim))
                self.save_file[idx].write(data_str)
                if idx == 0:
                    self.file_view.insertPlainText(data_str)
                if self.add_comment[idx]:
                    self.add_comment[idx] = False
                    self.save_file[idx].write(" - " + self.lnEditComment.text())
                    if idx == 0:
                        self.file_view.insertPlainText(
                            " - " + self.lnEditComment.text()
                        )
                self.save_file[idx].write("\n")
                if idx == 0:
                    self.file_view.insertPlainText("\n")
            self.save_file[idx].flush()
            os.fsync(self.save_file[idx].fileno())

            sample = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]

            self.plot_tab[idx].clear()
            for i, dim in enumerate(data):
                if i == 16:
                    continue
                self.plot_tab[idx].plot(sample, dim, pen=self.colors[i])

    def try_connect_pi1(self):
        try:
            self.adpd_pod_tab[0] = adi.adpd188(uri="ip:" + self.lnEditRPI1.text())
            self.thread_q[0] = ack_thread(device=self.adpd_pod_tab[0])
            self.queue[0] = Queue(maxsize=20)
        except:
            self.adpd_pod_tab.append(adi.adpd188(uri="ip:" + self.lnEditRPI1.text()))
            self.thread_q.append(ack_thread(device=self.adpd_pod_tab[0]))
            self.queue.append(Queue(maxsize=20))
        self.thread_q[0].queue = self.queue[0]
        self.ln_rd_status.setText("Connected to " + self.lnEditRPI1.text())
        self.connect_led1.setStyleSheet("background-color: green")
        self.adpd_pod_tab[0]._ctrl.context.set_timeout(0)
        self.adpd_pod_tab[0].rx_enabled_channels = [
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16
        ]
        self.adpd_pod_tab[0]._rx_data_type = ["<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<i8"]
        self.thread_q[0].data_rdy.connect(self.plot_data)
        self.thread_q[0].start()

    def try_connect_pi2(self):
        try:
            self.adpd_pod_tab[1] = adi.adpd188(uri="ip:" + self.lnEditRPI2.text())
            self.thread_q[1] = ack_thread(device=self.adpd_pod_tab[1])
            self.queue[1] = Queue(maxsize=20)
        except:
            self.adpd_pod_tab.append(adi.adpd188(uri="ip:" + self.lnEditRPI2.text()))
            self.thread_q.append(ack_thread(device=self.adpd_pod_tab[1]))
            self.queue.append(Queue(maxsize=20))
        self.thread_q[1].queue = self.queue[1]
        self.ln_rd_status.setText("Connected to " + self.lnEditRPI2.text())
        self.connect_led2.setStyleSheet("background-color: green")
        self.adpd_pod_tab[1]._ctrl.context.set_timeout(0)
        self.adpd_pod_tab[1].rx_enabled_channels = [
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16
        ]
        self.adpd_pod_tab[1]._rx_data_type = ["<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<i8"]
        self.thread_q[1].start()

    def try_connect_pi3(self):
        try:
            self.adpd_pod_tab[2] = adi.adpd188(uri="ip:" + self.lnEditRPI3.text())
            self.thread_q[2] = ack_thread(device=self.adpd_pod_tab[2])
            self.queue[2] = Queue(maxsize=20)
        except:
            self.adpd_pod_tab.append(adi.adpd188(uri="ip:" + self.lnEditRPI3.text()))
            self.thread_q.append(ack_thread(device=self.adpd_pod_tab[2]))
            self.queue.append(Queue(maxsize=20))
        self.thread_q[2].queue = self.queue[2]
        self.ln_rd_status.setText("Connected to " + self.lnEditRPI3.text())
        self.connect_led3.setStyleSheet("background-color: green")
        self.adpd_pod_tab[2]._ctrl.context.set_timeout(0)
        self.adpd_pod_tab[2].rx_enabled_channels = [
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16
        ]
        self.adpd_pod_tab[2]._rx_data_type = ["<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<i8"]
        self.thread_q[2].start()

    def try_connect_pi4(self):
        try:
            self.adpd_pod_tab[3] = adi.adpd188(uri="ip:" + self.lnEditRPI4.text())
            self.thread_q[3] = ack_thread(device=self.adpd_pod_tab[3])
            self.queue[3] = Queue(maxsize=20)
        except:
            self.adpd_pod_tab.append(adi.adpd188(uri="ip:" + self.lnEditRPI4.text()))
            self.thread_q.append(ack_thread(device=self.adpd_pod_tab[3]))
            self.queue.append(Queue(maxsize=20))
        self.thread_q[3].queue = self.queue[3]
        self.ln_rd_status.setText("Connected to " + self.lnEditRPI4.text())
        self.connect_led4.setStyleSheet("background-color: green")
        self.adpd_pod_tab[3]._ctrl.context.set_timeout(0)
        self.adpd_pod_tab[3].rx_enabled_channels = [
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
            15,
            16
        ]
        self.adpd_pod_tab[3]._rx_data_type = ["<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<u4","<i8"]
        self.thread_q[3].start()

    def insert_comment(self):
        self.add_comment = [True, True, True, True]
        self.ln_rd_status.setText("Comment added: " + self.lnEditComment.text())

    def close_save_file(self):
        for thr in self.thread_q:
            thr.run_source = False
        self.run_source = False

        for fl in self.save_file:
            fl.close()
        self.ln_rd_status.setText("Data files closed.")

    def open_save_file(self):
        for pod in self.adpd_pod_tab:
            fname = (
                "pod"
                + str(self.adpd_pod_tab.index(pod))
                + "_"
                + self.test_name.text()
                + "_"
                + self.lnEditFileName.text()
                + ".csv"
            )
            idx = self.adpd_pod_tab.index(pod)
            try:
                self.save_file[idx] = open(fname, "a")
            except:
                self.save_file.append(open(fname, "a"))
            self.thread_q[idx].sfile = self.save_file[idx]
            self.save_file[idx].write("Dev0Bl Dev0IR Dev1Bl Dev1IR Dev2Bl Dev2IR Dev3Bl Dev3IR Dev4Bl Dev4IR Dev5Bl Dev5IR Dev6Bl Dev6IR Dev7Bl Dev7IR timestamp\n")
        self.ln_rd_status.setText("Open {} files".format(len(self.adpd_pod_tab)))

    def start_saving_data(self):
        for thr in self.thread_q:
            thr.run_source = True
        self.run_source = True

    def save_efuse(self, index):
        reg_name = [
            "Module ID",
            "LED1 Gain Coeff",
            "LED3 Gain Coeff",
            "LED1 Int Coeff",
            "LED3 Int Coeff",
            "ECC",
        ]
        tname = "pod" + str(index) + "_" + self.test_name.text() + "_efuse.txt"
        efuse_file = open(tname, "w")
        efuse_file.flush()
        self.adpd_pod_tab[index].mode = "PROGRAM"
        for dut in range(0, 8):
            self.adpd_pod_tab[index]._rxadc.reg_write((dut << 8) + 0x5F, 0x1)
            self.adpd_pod_tab[index]._rxadc.reg_write((dut << 8) + 0x57, 0x7)
            i = 0
            efuse_file.write("DUT " + str(dut) + ":\n")
            for reg in range(0x70, 0x7F):
                if (reg > 0x74) and (reg != 0x7E):
                    continue
                addr = (dut << 8) + reg
                efuse_file.write("  " + reg_name[i] + "=")
                i += 1
                efuse_file.write(
                    str(hex(self.adpd_pod_tab[index]._rxadc.reg_read(addr)))
                )
                efuse_file.write("\n")
            efuse_file.flush()
            self.adpd_pod_tab[index]._rxadc.reg_write((dut << 8) | 0x57, 0x0)
            self.adpd_pod_tab[index]._rxadc.reg_write((dut << 8) | 0x5F, 0x0)
        self.adpd_pod_tab[index].mode = "STANDBY"
        efuse_file.close()
        self.ln_rd_status.setText(tname)

    def save_efuse_all(self):
        for pod in self.adpd_pod_tab:
            self.save_efuse(self.adpd_pod_tab.index(pod))

    def save_registers(self, index):
        tname = "pod" + str(index) + "_" + self.test_name.text() + "_regs.txt"
        efuse_file = open(tname, "w")
        efuse_file.flush()
        for dut in range(0, 8):
            efuse_file.write("DUT " + str(dut) + ":\n")
            for reg in range(0, 0x7F):
                addr = (dut << 16) + reg
                efuse_file.write("  reg" + str(hex(reg)) + "=")
                efuse_file.write(
                    str(hex(self.adpd_pod_tab[index]._rxadc.reg_read(addr)))
                )
                efuse_file.write("\n")
            efuse_file.flush()
        efuse_file.close()
        self.ln_rd_status.setText("Registers written in file " + tname)

    def save_registers_all(self):
        for pod in self.adpd_pod_tab:
            self.save_registers(self.adpd_pod_tab.index(pod))

    def change_odr(self):
        for pod in self.adpd_pod_tab:
            pod.sample_rate = int(self.ln_odr_hz.text())
        txt = "Data rate changed to {}"
        self.ln_rd_status.setText(txt.format(self.ln_odr_hz.text()))

    def setup(self):
        self.lnEditRPI1.returnPressed.connect(self.try_connect_pi1)
        self.lnEditRPI2.returnPressed.connect(self.try_connect_pi2)
        self.lnEditRPI3.returnPressed.connect(self.try_connect_pi3)
        self.lnEditRPI4.returnPressed.connect(self.try_connect_pi4)

        self.lnEditComment.returnPressed.connect(self.insert_comment)

        self.btnStop.clicked.connect(self.close_save_file)

        self.btnStart.clicked.connect(self.open_save_file)
        self.btnStart.clicked.connect(self.start_saving_data)
        self.connect_all.clicked.connect(self.try_connect_pi1)
        self.connect_all.clicked.connect(self.try_connect_pi2)
        self.connect_all.clicked.connect(self.try_connect_pi3)
        self.connect_all.clicked.connect(self.try_connect_pi4)

        self.connect_led1.setStyleSheet("background-color: red")
        self.connect_led2.setStyleSheet("background-color: red")
        self.connect_led3.setStyleSheet("background-color: red")
        self.connect_led4.setStyleSheet("background-color: red")

        self.btnReadEFuses.clicked.connect(self.save_efuse_all)
        self.btnReadRegisters.clicked.connect(self.save_registers_all)
        self.ln_odr_hz.returnPressed.connect(self.change_odr)

        self.lblDataRecording.adjustSize()
        self.lblInsertComment.adjustSize()
        self.plot_tab.append(self.widgetPlotContainer)
        self.plot_tab.append(self.plot_2)
        self.plot_tab.append(self.plot_3)
        self.plot_tab.append(self.plot_4)


if __name__ == "__main__":

    # build the application and the window
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    gui = adpd188_8pod_gui()

    # setup the ui in the window
    gui.setupUi(MainWindow)
    gui.setup()

    # show the window
    MainWindow.show()
    sys.exit(app.exec_())
