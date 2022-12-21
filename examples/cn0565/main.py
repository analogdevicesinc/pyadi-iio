from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import sys
import os
import os.path
import realtimeEITUI
import argparse

from EitSerialReaderProtocol import EIT, EIT_Interface
import serial
import serial.tools.list_ports
from commWorker import EITWorker


__tool_name__   = "Realtime Electrical Impedance Tomography"
__banner__   = "by Kister Jimenez and Mark Ramos"
__version__ = "0.0.1.0"
__release_date_ = "27-Sep-2018"

from types import MethodType

def rebinder(f):
    if not isinstance(f,MethodType):
        raise TypeError("rebinder was intended for rebinding methods")
    def wrapper(*args,**kw):
        return f(*args,**kw)
    return wrapper

class RealtimeEIT(QtWidgets.QMainWindow, realtimeEITUI.Ui_MainWindow):
    def __init__(self, port, baudrate, iio, el, parent=None):
        super(RealtimeEIT,self).__init__(parent)
        self.port = port
        self.baudrate = baudrate
        self.iio = iio
        self.intf = None
        self.setupUi(self)
        self.setFixedSize(self.size())
        sizeX = 3.7 #1151/96
        sizeY = 1.9  #401/96
        size = (sizeX,sizeY)
        self.figure = Figure(size)
        self.canvas = FigureCanvas(self.figure) 
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.vLayout_plot.addWidget(self.toolbar)
        self.vLayout_plot.addWidget(self.canvas)
        self.sldr_freq.valueChanged.connect(self.freqValueChanged)
        self.sldr_p.valueChanged.connect(self.pValueChanged)
        self.sldr_lambda.valueChanged.connect(self.lambdaValueChanged)
        self.btn_refresh_comm.clicked.connect(self.update_cmb_comm_select)
        self.btn_baseline.clicked.connect(self.setBaseline)
        self.btn_connect.clicked.connect(self.comm_connect)
        self.rbtn_real.toggled.connect(lambda:self.btnState(self.rbtn_real))
        self.rbtn_imaginary.toggled.connect(lambda:self.btnState(self.rbtn_imaginary))
        self.rbtn_magnitude.toggled.connect(lambda:self.btnState(self.rbtn_magnitude))
        self.rbtn_bp.toggled.connect(lambda:self.btnState(self.rbtn_bp))
        self.rbtn_jac.toggled.connect(lambda:self.btnState(self.rbtn_jac))
        self.rbtn_greit.toggled.connect(lambda:self.btnState(self.rbtn_greit))
        self.update_cmb_comm_select()
        self.eit_worker = EITWorker(figure = self.figure)
        self.eit_worker.doneCompute.connect(self.updatePlot)
        self.eit_worker.doneGetSupportedElectrodeCount.connect(self.updateElectrodeCount)
        self.eit_worker.buildMesh(el=el,h0=0.06,dist=1,step=1)
        self.freqValueChanged()
        self.pValueChanged()
        self.lambdaValueChanged()
        self.rbtn_bp.toggle()
        self.rbtn_real.toggle()

        index = self.cmb_supported_electrode_count_select.findText(str(el), QtCore.Qt.MatchFixedString)
        if index >= 0:
            self.cmb_supported_electrode_count_select.setCurrentIndex(index)
        #self.cmb_comm_select.showPopup = rebinder(self.showPopup)
        #self.cmb_comm_select.view().pressed.connect(self.update_cmb_comm_select)
        #self.solve()

    def comm_connect(self):
        """
        """
        if self.btn_connect.text() == "Connect":
            self.btn_connect.setText("Disconnect")
            self.port = self.cmb_comm_select.currentData().strip()
            try:
                print(f"Serial: {self.port} baudrate: {self.baudrate}")
                self.intf = EIT_Interface(self.port, self.baudrate, self.iio)
                self.eit_worker.intf=self.intf
                self.eit_worker.start()
            except Exception as e:
                print(f"Serial Connection Error! {e}")
                self.btn_connect.setText("Connect")
                self.intf.close()
        else:
            #TODO: stop hardware first
            self.btn_connect.setText("Connect")
            self.eit_worker.exiting=True
            self.intf.close()

    def btnState(self,btn):
        if btn.isChecked():
            print(btn.text() + "is chosen")
            if btn.text()=='Real':
                self.eit_worker.setValueType("re")
            if btn.text()=="Imaginary":
                self.eit_worker.setValueType("im")
            if btn.text()=="Magnitude":
                self.eit_worker.setValueType("mag")
            if btn.text()=="BP":
                self.eit_worker.updateReconstructionMethod("bp")
            if btn.text()=="JAC":
                self.eit_worker.updateReconstructionMethod("jac")
            if btn.text()=="GREIT":
                self.eit_worker.updateReconstructionMethod("greit")

    def setBaseline(self):
        self.eit_worker.setBaseline()

    def updatePlot(self):
        self.canvas.draw()

    def updateElectrodeCount(self, supported_electrode_count):
        """
        TODO: Update the Electrode counts supported
        """
        self.cmb_supported_electrode_count_select.clear()
        for electrode_count in supported_electrode_count:
            self.cmb_supported_electrode_count_select.addItem(str(electrode_count))

    def freqValueChanged(self):
        self.freqVal = int(self.sldr_freq.value())
        self.sbox_freq.setProperty("value",self.freqVal)
        self.eit_worker.freq=self.freqVal

    def update_cmb_comm_select(self):
        self.cmb_comm_select.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.cmb_comm_select.addItem(port.device+ ": " +port.description, port.device)

    def pValueChanged(self):
        self.pVal=int(self.sldr_p.value())/100.0
        self.sbox_p.setProperty("value",self.pVal)
        self.eit_worker.updatePvalue(p=self.pVal)

    def lambdaValueChanged(self):
        self.lambdaVal=int(self.sldr_lambda.value())/100.0
        self.sbox_lambda.setProperty("value",self.lambdaVal)
        self.eit_worker.updateLambdaValue(lamb=self.lambdaVal)

    def baselineDragEnterEvent(self, event):
        event.accept()

    def inputDragEnterEvent(self, event):
        event.accept()
        
    
        
def main(argv):
    ap = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)

    ap.add_argument("-b", "--baudrate",
                    action="store",
                    nargs="?",
                    help="Serial port baudrate.",
                    default=230400)

    ap.add_argument("-e", "--el",
                    action="store",
                    nargs="?",
                    help="Number of electrodes.",
                    default=16)

    ap.add_argument("-i", "--iio",
                    action="store_true",
                    help="Use libiio instead of custom serial protocol.",
                    default=False)
    args = ap.parse_args()

    el = int(args.el)
    if el not in [8,16,32]:
        el=16
    app=QtWidgets.QApplication(sys.argv)
    form = RealtimeEIT(None, args.baudrate, args.iio, el)
    form.show()
    sys.exit(app.exec())
    

if __name__=='__main__':
    main(sys.argv[1:])