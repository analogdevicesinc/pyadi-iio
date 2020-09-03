import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
from scipy.fftpack import fft
from scipy import signal

import sys
import time
import adi
from PyQt5 import QtGui
from queue import Queue 
from queue import Full
import threading

class ADIPlotter(object):
    def __init__(self):

        self.q = Queue(maxsize=20)
        self.stream = adi.Pluto()
        self.stream.sample_rate = 10000000
        self.stream.dds_single_tone(3000000, 0.9)
        self.stream.rx_buffer_size = 2**12
        self.stream.rx_enabled_channels = [0]
        
        pg.setConfigOptions(antialias=True)
        self.traces = dict()
        self.app = QtGui.QApplication(sys.argv)
        self.win = pg.GraphicsWindow(title='Spectrum Analyzer')
        self.win.setWindowTitle('Spectrum Analyzer')
        self.win.setGeometry(5, 115, 1910, 1070)

        wf_xaxis = pg.AxisItem(orientation='bottom')
        wf_xaxis.setLabel(units='Seconds')

        wf_ylabels = [(-2*11, '-2047'), (0, '0'), (2**11, '2047')]
        wf_yaxis = pg.AxisItem(orientation='left')
        wf_yaxis.setTicks([wf_ylabels])

        sp_xaxis = pg.AxisItem(orientation='bottom')
        sp_xaxis.setLabel(units='Hz')

        self.waveform = self.win.addPlot(
            title='WAVEFORM', row=1, col=1, axisItems={'bottom': wf_xaxis},
        )
        self.spectrum = self.win.addPlot(
            title='SPECTRUM', row=2, col=1, axisItems={'bottom': sp_xaxis},
        )
        self.waveform.showGrid(x=True, y=True)
        self.spectrum.showGrid(x=True, y=True)

        # waveform and spectrum x points
        self.x = np.arange(0, self.stream.rx_buffer_size)/self.stream.sample_rate
        self.f = np.linspace(-1*self.stream.sample_rate/2, self.stream.sample_rate / 2, self.stream.rx_buffer_size)

        self.counter = 0
        self.min = -100
        self.window = signal.kaiser(self.stream.rx_buffer_size, beta=38)

        self.run_source = True
        self.thread = threading.Thread(target=self.source)
        self.thread.start()

    def source(self):
        print("Thread running")
        while self.run_source:
            data = self.stream.rx()
            try:
                self.q.put(data,block=False,timeout=4)
            except Full:
                if not self.run_source:
                    return
                    #raise

    def start(self):
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QtGui.QApplication.instance().exec_()

    def set_plotdata(self, name, data_x, data_y):
        if name in self.traces:
            self.traces[name].setData(data_x, data_y)
        else:
            if name == 'waveform':
                self.traces[name] = self.waveform.plot(pen='c', width=3)
                self.waveform.setYRange(-2**11-200, 2**11+200, padding=0)
                self.waveform.setXRange(0, self.stream.rx_buffer_size/self.stream.sample_rate, padding=0.005)
            if name == 'spectrum':
                self.traces[name] = self.spectrum.plot(pen='m', width=3)
                self.spectrum.setLogMode(x=False, y=False)
                self.spectrum.setYRange(self.min, 5, padding=0)
                self.spectrum.setXRange(
                    -1*self.stream.sample_rate/2, self.stream.sample_rate / 2, padding=0.005)

    def update(self):
        while not self.q.empty():
            wf_data = self.q.get()
            self.set_plotdata(name='waveform', data_x=self.x, data_y=np.real(wf_data),)
            sp_data = np.fft.fft(wf_data)
            sp_data = np.abs(np.fft.fftshift(sp_data)) / self.stream.rx_buffer_size
            sp_data = 20*np.log10(sp_data / (2**11))
            self.set_plotdata(name='spectrum', data_x=self.f, data_y=sp_data)

    def animation(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(1)
        self.start()
        self.run_source = False


if __name__ == '__main__':

    app = ADIPlotter()
    app.animation()
    app.thread.join()
