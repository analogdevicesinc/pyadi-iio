from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from EITPlot import EITPlot
from EitSerialReaderProtocol import EIT
import serial
import serial.threaded
import sys
import numpy as np

class EITWorker(QThread):
    doneCompute = pyqtSignal()
    doneGetSupportedElectrodeCount = pyqtSignal(np.ndarray)
    def __init__(self, parent=None, figure=None):
        super(EITWorker,self).__init__(parent)
        self.exiting = False
        self.set_baseline = True
        self.eitPlot = EITPlot()
        self.pVal = 0.5
        self.lambdaVal = 0.5
        self.reconstruction = "greit"
        self.freq = 10
        self.el=8
        self.h0=0.08
        self.electrode_count = 8
        self.force_distance = 4
        self.sense_distance = 4
        self.fixed_ref = False
        self.figure = figure
        self.intf = None
        self.value_type="re"
        self.supported_electrode_count=np.ndarray([8,16,32])
        self.doneGetSupportedElectrodeCount.emit(self.supported_electrode_count)
        print("Worker Created")

    def buildMesh(self,el=8,h0=0.08,dist=1,step=1):
        self.el=el
        self.h0=h0
        self.force_distance=dist
        self.sense_distance=step
        self.rebuildMesh=True
        self.reSetup = True

    def updatePvalue(self,p=0.5):
        self.pVal=p
        self.reSetup=True

    def updateLambdaValue(self,lamb=0.5):
        self.lambdaVal=lamb
        self.reSetup=True

    def updateReconstructionMethod(self,reconstruction="jac"):
        self.reconstruction=reconstruction
        self.reSetup=True

    def setup(self, p=0.5,lamb=0.5,reconstruction="jac"):
        self.pVal=p
        self.lambdaVal=lamb
        self.reconstruction=reconstruction
        self.reSetup=True

    def setValueType(self,value_type="re"):
        self.value_type=value_type

    def solve(self,current):
        self.eitPlot.setCurrentData(current)
        self.eitPlot.compute(self.figure)

    def setBaseline(self):
        self.set_baseline=True
        
    def run(self):
        # import pydevd; pydevd.settrace(suspend=False)
        self.exiting=False
        self.stopping=False
        self.supported_electrode_count = self.intf.get_board_supported_electrode_count()
        self.doneGetSupportedElectrodeCount.emit(self.supported_electrode_count)
        self.intf.set_eit_mode(freq=self.freq,
                                electrode_count=self.el,
                                force_distance=self.force_distance,
                                sense_distance=self.sense_distance,
                                fixed_ref=self.fixed_ref)  
        while not self.exiting:
            if (self.rebuildMesh):
                self.eitPlot.buildMesh(el=self.el,h0=self.h0,
                                        dist=self.force_distance,
                                        step=self.sense_distance)
                self.intf.set_eit_mode(freq=self.freq,
                                        electrode_count=self.el,
                                        force_distance=self.force_distance,
                                        sense_distance=self.sense_distance,
                                        fixed_ref=self.fixed_ref) 
                print("Mesh built: "
                    + str(self.el) +" "
                    + str(self.h0) +" "
                    + str(self.force_distance) +" "
                    + str(self.sense_distance))
                self.rebuildMesh=False
            if (self.reSetup):
                self.eitPlot.setup(p=self.pVal,lamb=self.lambdaVal,
                                    reconstruction=self.reconstruction)
                self.reSetup=False
                print("EIT setup done: " + self.reconstruction)
            current_data=self.intf.get_boundary_voltage()
            if current_data is not None:
                if self.value_type=="re":
                    current_data=current_data[:,0]
                elif self.value_type=="im":
                    current_data=current_data[:,1]
                else:
                    current_data=np.sqrt((current_data**2).sum(axis=1))

                print("Data received Size: "+str(current_data.shape)) 
                if (self.set_baseline):
                    """
                    The received data will be stored as baseline data
                    """
                    self.eitPlot.setBaseline(current_data)
                    self.set_baseline = False
                    print("done baseline!")
                else:
                    """
                    The received data will be used for computing the image
                    """
                    self.solve(current = current_data)
                    print("done solving!")
                    self.doneCompute.emit()

        self.intf.stop_eit()
        self.intf.stop()
            
