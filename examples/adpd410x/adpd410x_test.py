# Copyright (C) 2020 Analog Devices, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     - Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     - Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.
#     - Neither the name of Analog Devices, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#     - The use of this software may or may not infringe the patent rights
#       of one or more patent holders.  This license does not release you
#       from the requirement that you obtain separate licenses from these
#       patent holders to use this software.
#     - Use of the software either in source or binary form, must be run
#       on or directly connected to an Analog Devices Inc. component.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT, MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.
#
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, INTELLECTUAL PROPERTY
# RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

try:
	import sys
	import os
	import time
	import threading
	import adi

	from serial import Serial
	from serial.tools import list_ports

	from PyQt5.QtCore import *
	from PyQt5.QtGui import QColor, QMovie, QTextDocument
	from PyQt5.QtWidgets import QPushButton, QLabel, QComboBox, QGroupBox, QTextEdit, QGridLayout, QVBoxLayout, QHBoxLayout, QMainWindow, QApplication, QWidget
	
except Exception as e:
	print(str(e))
	exit()
	
class ItemSelect(QComboBox):
	showItems = pyqtSignal()
	
	def showPopup(self):
		self.showItems.emit()
		super(ItemSelect, self).showPopup()
		
def resource_path(relative_path):
	try:
		base_path = sys._MEIPASS
	except Exception:
		base_path = os.path.abspath(".")

	return os.path.join(base_path, relative_path)

class GlobalControlWindow(QMainWindow):
	def __init__(self, screenwidth=500, screenheight=500):
		super().__init__()
		self.title = "EVAL-ADPD410X Production Test Software"
		
		self.width = int(screenwidth / 2)
		self.height = int(screenheight / 2)
		self.top = int(screenheight / 4)
		self.left = int(screenwidth / 4)
		
		self.setWindowTitle(self.title)
		self.setGeometry(self.left, self.top, self.width, self.height)
		self.setStyleSheet("background-color: #FFFFFF;")
		
		self.myAFE = None
		self.initserialResult = False
		self.delStage = 0
		
		self.adcLimit = 11000	# Raw ADC Threshold for Test Jig
		self.ledLimit = 15000	# Raw ADC Threshold for Onboard LED Test
		
		# Channel Names
		self.channelNames = [
			['LED1A' , 'PD1A'],
			['LED1B' , 'PD1B'],
			['LED2A' , 'PD2A'],
			['LED2B' , 'PD2B'],
			['LED3A' , 'PD3A'],
			['LED3B' , 'PD3B'],
			['LED4A' , 'PD4A'],
			['LED4B' , 'PD4B']]
		
		self.createUI()
		
	def createUI(self):
		self.mainContainer = QWidget()
		self.mainLayout = QGridLayout()
		
		self.grpConn = QGroupBox("Serial Connection")
		self.connLbl = QLabel("Select COM Port")
		self.connSel = ItemSelect()
		self.connSel.showItems.connect(self.showCOMPorts)
		self.showCOMPorts()
		
		self.grpConnLayout = QHBoxLayout()
		self.grpConn.setLayout(self.grpConnLayout)
		self.grpConnLayout.addWidget(self.connLbl)
		self.grpConnLayout.addWidget(self.connSel)
		
		self.noloadBtn = QPushButton("No-Load Test")
		self.noloadBtn.clicked.connect(self.noLoadTest)
		
		self.loadBtn = QPushButton("Mounted-Jig Test")
		self.loadBtn.clicked.connect(self.mountedJigTest)
		
		self.openLEDBtn = QPushButton("Open LED Test")
		self.openLEDBtn.clicked.connect(self.openLEDTest)
		
		self.coveredLEDBtn = QPushButton("Covered LED Test")
		self.coveredLEDBtn.clicked.connect(self.coveredLEDTest)
		
		self.grpRes = QGroupBox("Results")
		self.resLabel = QTextEdit()
		self.resLabel.setReadOnly(True)
		self.resDoc = QTextDocument()
		self.resLabel.setDocument(self.resDoc)
		self.grpResLayout = QVBoxLayout()
		self.grpRes.setLayout(self.grpResLayout)
		self.grpResLayout.addWidget(self.resLabel)
		
		self.ldglbl = QLabel(self.resLabel)
		self.ldglbl.resize(self.width - 50, self.height - 50)
		self.ldglbl.setAlignment(Qt.AlignCenter)
		self.ldglbl.setWindowFlag(Qt.FramelessWindowHint)
		self.ldglbl.setAttribute(Qt.WA_NoSystemBackground)
		self.ldglbl.setAttribute(Qt.WA_TranslucentBackground);
		self.ldgscr = QMovie(resource_path("loading.gif"))
		
		self.mainLayout.addWidget(self.grpConn, 1, 1)
		self.mainLayout.addWidget(self.openLEDBtn, 1, 2)
		self.mainLayout.addWidget(self.coveredLEDBtn, 1, 3)
		self.mainLayout.addWidget(self.noloadBtn, 1, 4)
		self.mainLayout.addWidget(self.loadBtn, 1, 5)
		self.mainLayout.addWidget(self.grpRes, 2, 1, 1, 5)
		
		self.mainContainer.setLayout(self.mainLayout)
		self.setCentralWidget(self.mainContainer)
		self.show()
		
	def showCOMPorts(self):
		self.connSel.clear()
	
		ports = list_ports.comports()
		for port, desc, hwid in sorted(ports):
			self.connSel.addItem(str(port))
		
	def noLoadTest(self):
		self.delStage = 0
		self.btnSetStatus(False)
	
		resTxt = '<hr><font face="Courier New">'
	
		try:
			serialuri = 'serial:' + str(self.connSel.currentText())
			resTxt += 'Connecting on ' + serialuri + '...'
			self.resDoc.setHtml(resTxt)
		except Exception as e:
			print(str(e))
			resTxt += 'Error Please restart the program</font><hr>'
			self.resDoc.setHtml(resTxt)
			return
			
		self.myAFE = None
		
		self.ldglbl.setMovie(self.ldgscr)
		self.ldgscr.start()
		
		thread = threading.Thread(target = self.openSerial, args = (serialuri, ))
		thread.start()
		
		while self.myAFE == None:
			QApplication.processEvents()
		thread.join()
		
		if self.myAFE == -1:
			resTxt += '<hr>Unable to connect to device. Please Retry!<hr>'
			self.resDoc.setHtml(resTxt)
						
			self.ldgscr.stop()
			self.ldglbl.clear()
			
			self.btnSetStatus(True)
			return
		
		self.ldgscr.stop()
		self.ldglbl.clear()

		print("Device connected")
		resTxt += '<hr>Device Connected!<hr>'
		self.resDoc.setHtml(resTxt)
		
		try:
			print("Starting Test...")
			resTxt += 'Starting No Load Test...<br><br>'
			self.resDoc.setHtml(resTxt)
			
			# Dummy read
			self.myAFE.channel[0].raw
			
			for ch in range (0,8):
				rawValue = self.myAFE.channel[ch].raw
				resTxt += self.channelNames[ch][0] + " to " + self.channelNames[ch][1] + " Raw:    <b>" + str(rawValue) + "</b>"
				if rawValue < self.adcLimit:
					resTxt += '    <font color="#00ff00">PASS</font><br>'
				else:
					resTxt += '    <font color="#ff0000">FAIL</font><br>'
				print(rawValue)
			
			self.closePyADIIIO()
			
			print("Test Complete")
			resTxt += "<br>Test Complete</font><hr>"
			self.resDoc.setHtml(resTxt)
			
		except Exception as e:
			print("Error: " + str(e))
			resTxt += "<hr>Device error! Please restart the software</font>"
			self.resDoc.setHtml(resTxt)
			
			self.closePyADIIIO()
		
		self.btnSetStatus(True)
		return
				
	def mountedJigTest(self):
		self.delStage = 0
		self.btnSetStatus(False)
	
		resTxt = '<hr><font face="Courier New">'
		try:
			serialuri = 'serial:' + str(self.connSel.currentText())
			resTxt += 'Connecting on ' + serialuri + '...'
			self.resDoc.setHtml(resTxt)
		except Exception as e:
			print(str(e))
			resTxt += 'Error Please restart the program</font><hr>'
			self.resDoc.setHtml(resTxt)
			return
			
		self.myAFE = None
		
		self.ldglbl.setMovie(self.ldgscr)
		self.ldgscr.start()
		
		thread = threading.Thread(target = self.openSerial, args = (serialuri, ))
		thread.start()
		
		while self.myAFE == None:
			QApplication.processEvents()
		thread.join()
		
		if self.myAFE == -1:
			resTxt += '<hr>Unable to connect to device. Please Retry!<hr>'
			self.resDoc.setHtml(resTxt)
						
			self.ldgscr.stop()
			self.ldglbl.clear()
			
			self.btnSetStatus(True)
			return
		
		self.ldgscr.stop()
		self.ldglbl.clear()

		print("Device connected")
		resTxt += '<hr>Device Connected!<hr>'
		self.resDoc.setHtml(resTxt)
		
		try:
			print("Starting Test...")
			resTxt += 'Starting Mounted Jig Test...<br><br>'
			self.resDoc.setHtml(resTxt)
			
			# Dummy read
			self.myAFE.channel[0].raw
			
			for ch in range (0,8):
				rawValue = self.myAFE.channel[ch].raw
				resTxt += self.channelNames[ch][0] + " to " + self.channelNames[ch][1] + " Raw:    <b>" + str(rawValue) + "</b>"
				if rawValue >= self.adcLimit:
					resTxt += '    <font color="#00ff00">PASS</font><br>'
				else:
					resTxt += '    <font color="#ff0000">FAIL</font><br>'
				print(rawValue)
			
			self.closePyADIIIO()
			
			print("Test Complete")
			resTxt += "<br>Test Complete</font><hr>"
			self.resDoc.setHtml(resTxt)
			
		except Exception as e:
			print("Error: " + str(e))
			resTxt += "<hr>Device error! Please restart the software</font>"
			self.resDoc.setHtml(resTxt)
			
			self.closePyADIIIO()
		
		self.btnSetStatus(True)
		return
		
	def openLEDTest(self):
		self.delStage = 0
		self.btnSetStatus(False)
	
		resTxt = '<hr><font face="Courier New">'
		try:
			serialuri = 'serial:' + str(self.connSel.currentText())
			resTxt += 'Connecting on ' + serialuri + '...'
			self.resDoc.setHtml(resTxt)
		except Exception as e:
			print(str(e))
			resTxt += 'Error Please restart the program</font><hr>'
			self.resDoc.setHtml(resTxt)
			return
			
		self.myAFE = None
		
		self.ldglbl.setMovie(self.ldgscr)
		self.ldgscr.start()
		
		thread = threading.Thread(target = self.openSerial, args = (serialuri, ))
		thread.start()
		
		while self.myAFE == None:
			QApplication.processEvents()
		thread.join()
		
		if self.myAFE == -1:
			resTxt += '<hr>Unable to connect to device. Please Retry!<hr>'
			self.resDoc.setHtml(resTxt)
			
			self.ldgscr.stop()
			self.ldglbl.clear()
			
			self.btnSetStatus(True)
			return
		
		self.ldgscr.stop()
		self.ldglbl.clear()

		print("Device connected")
		resTxt += '<hr>Device Connected!<hr>'
		self.resDoc.setHtml(resTxt)
		
		try:
			print("Starting Test...")
			resTxt += 'Starting Open Onboard LED Test...<br><br>'
			self.resDoc.setHtml(resTxt)
			
			# Dummy read
			self.myAFE.channel[0].raw
			
			rawValue = self.myAFE.channel[0].raw
			resTxt += "Onboard LED and PD Raw:    <b>" + str(rawValue) + "</b>"
			if rawValue < self.ledLimit:
				resTxt += '    <font color="#00ff00">PASS</font><br>'
			else:
				resTxt += '    <font color="#ff0000">FAIL</font><br>'
			print(rawValue)
			
			self.closePyADIIIO()
			
			print("Test Complete")
			resTxt += "<br>Test Complete</font><hr>"
			self.resDoc.setHtml(resTxt)
			
		except Exception as e:
			print("Error: " + str(e))
			resTxt += "<hr>Device error! Please restart the software</font>"
			self.resDoc.setHtml(resTxt)
			
			self.closePyADIIIO()
		
		self.btnSetStatus(True)
		return
		
	def coveredLEDTest(self):
		self.delStage = 0
		self.btnSetStatus(False)
	
		resTxt = '<hr><font face="Courier New">'
		try:
			serialuri = 'serial:' + str(self.connSel.currentText())
			resTxt += 'Connecting on ' + serialuri + '...'
			self.resDoc.setHtml(resTxt)
		except Exception as e:
			print(str(e))
			resTxt += 'Error Please restart the program</font><hr>'
			self.resDoc.setHtml(resTxt)
			return
			
		self.myAFE = None
		
		self.ldglbl.setMovie(self.ldgscr)
		self.ldgscr.start()
		
		thread = threading.Thread(target = self.openSerial, args = (serialuri, ))
		thread.start()
		
		while self.myAFE == None:
			QApplication.processEvents()
		thread.join()
		
		if self.myAFE == -1:
			resTxt += '<hr>Unable to connect to device. Please Retry!<hr>'
			self.resDoc.setHtml(resTxt)
						
			self.ldgscr.stop()
			self.ldglbl.clear()
			
			self.btnSetStatus(True)
			return
		
		self.ldgscr.stop()
		self.ldglbl.clear()

		print("Device connected")
		resTxt += '<hr>Device Connected!<hr>'
		self.resDoc.setHtml(resTxt)
		
		try:
			print("Starting Test...")
			resTxt += 'Starting Covered Onboard LED Test...<br><br>'
			self.resDoc.setHtml(resTxt)
			
			# Dummy read
			self.myAFE.channel[0].raw
			
			rawValue = self.myAFE.channel[0].raw
			resTxt += "Onboard LED and PD Raw:    <b>" + str(rawValue) + "</b>"
			if rawValue > self.ledLimit:
				resTxt += '    <font color="#00ff00">PASS</font><br>'
			else:
				resTxt += '    <font color="#ff0000">FAIL</font><br>'
			print(rawValue)
			
			self.closePyADIIIO()
			
			print("Test Complete")
			resTxt += "<br>Test Complete</font><hr>"
			self.resDoc.setHtml(resTxt)
			
		except Exception as e:
			print("Error: " + str(e))
			resTxt += "<hr>Device error! Please restart the software</font>"
			self.resDoc.setHtml(resTxt)
			
			self.closePyADIIIO()
		
		self.btnSetStatus(True)
		return
		
	def openSerial(self, serialuri):
		print(serialuri)
	
		timeLimit = 4
		elapsed_s = 0
	
		while True:
			if elapsed_s > timeLimit:
				self.myAFE = -1
				break
			
			try:
				self.myAFE = adi.adpd410x(uri=serialuri)
				break
				
			except Exception as e:
				print(str(e) + '\nReconnecting...\n')
				time.sleep(0.5)
				elapsed_s += 1
				
		return
		
	def btnSetStatus(self, status):
		if status == False:
			self.noloadBtn.setEnabled(False)
			self.loadBtn.setEnabled(False)
			self.openLEDBtn.setEnabled(False)
			self.coveredLEDBtn.setEnabled(False)
		else:
			self.noloadBtn.setEnabled(True)
			self.loadBtn.setEnabled(True)
			self.openLEDBtn.setEnabled(True)
			self.coveredLEDBtn.setEnabled(True)
			
	def closePyADIIIO(self):
		if self.delStage < 1:
			for i in range(0, len(self.myAFE.channel)):
				del self.myAFE.channel[0]
			self.delStage = 1
		
		if self.delStage < 2:
			del self.myAFE._rxadc
			self.delStage = 2
		
		if self.delStage < 3:
			del self.myAFE._ctx
			self.delStage = 3

def main():
	main_app = QApplication(sys.argv)
	main_screen = main_app.primaryScreen()
	main_size = main_screen.availableGeometry()

	main_window = GlobalControlWindow(screenwidth=main_size.width(), screenheight=main_size.height())

	sys.exit(main_app.exec_())

if __name__ == '__main__':
	main()