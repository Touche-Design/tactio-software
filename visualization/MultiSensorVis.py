import xml.etree.ElementTree as et
from PyQt5 import QtWidgets, QtCore, Qt, QtGui
import sys  # We need sys so that we can pass argv to QApplication
import os
import numpy as np
import serial
import json
import time
import PyTactio

from NumpyArrayEncoder import NumpyArrayEncoder
import SingleGrid
import ParseThread

class MultiSensorVis(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(QtWidgets.QMainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Tactio")
        position_data = et.parse('1sensor.xml').getroot()
        self.sensorCount = len(position_data)
        self.sensorIDs = [int(position_data[i].find('id').text) for i in range(self.sensorCount)]

        sensorAreaWidget = QtGui.QWidget()
        self.sensorWidgets = [SingleGrid.SensorGrid() for i in range(self.sensorCount)]
        sensorXpos = []
        sensorYpos = []
        sizes = []
        for i in range(self.sensorCount):
            self.sensorWidgets[i].setId(self.sensorIDs[i])
            self.sensorWidgets[i].sendData.connect(self.sendMessageCallback)
            self.sensorWidgets[i].setParent(sensorAreaWidget)
            sensorx = int(position_data[i].find('x_pos').text)
            sensorXpos.append(sensorx)
            sensory = int(position_data[i].find('y_pos').text)
            sensorYpos.append(sensory)
            size = 400
            try:
                size = int(position_data[i].find('size').text)
            except:
                size = 400
            sizes.append(size)
            self.sensorWidgets[i].resize(size,size)
            self.sensorWidgets[i].move(sensorx, sensory)

        # Compute Max Width
        maxsizeX = max(sensorXpos) + self.sensorWidgets[sensorXpos.index(max(sensorXpos))].width() + min(sensorXpos) 
        maxsizeY = max(sensorYpos) + self.sensorWidgets[sensorYpos.index(max(sensorYpos))].height() + min(sensorYpos) 

        sensorAreaWidget.setMinimumSize(maxsizeX, maxsizeY)
        #print(int(position_data[0].find('id').text))
        #adding buttons for recording and saving
        self.rec_btn = QtGui.QPushButton("Rec", self)
        self.rec_btn.setStyleSheet("min-height: 50px;"
                                   "max-height: 50px;"
                                   "min-width: 50px;"
                                   "max-width: 50px;"
                                   "background-color: gray;"
                                   "color: red;"
                                   "border-radius: 25px")
        self.rec_btn.clicked.connect(self.record)

        self.fileLine = QtWidgets.QLineEdit()
        self.fileLine.readOnly = True
        self.fileLine.setMaximumWidth(500)

        self.fileSelBtn = QtWidgets.QPushButton("...")
        self.fileSelBtn.clicked.connect(self.fileSelCallback)
        self.fileSelBtn.setMaximumWidth(50)

        #self.getSensorListButton = QtWidgets.QPushButton("Sensor List")
        #nesting for UI buttons
        recordButtonHbox = QtWidgets.QHBoxLayout()
        recordButtonHbox.addWidget(self.fileLine)
        #recordButtonHbox.addSpacing(10)
        recordButtonHbox.addWidget(self.fileSelBtn)
        #recordButtonHbox.addSpacing(10)
        recordButtonHbox.addWidget(self.rec_btn)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(sensorAreaWidget)

        vbox.addItem(recordButtonHbox)
        mainWidget = QtWidgets.QWidget()
        mainWidget.setLayout(vbox)
        self.setCentralWidget(mainWidget)

        #initializing recording
        self.is_recording = False
        #self.recording = np.zeros((1,4,4))
        self.recording = {id : np.empty((1,4,4)) for id in self.sensorIDs} #dictionary holding previous recordings

        # QTimer kicks off every 0.1 seconds to update the visualization
        self.vizTimer = QtCore.QTimer()
        self.vizTimer.setInterval(50) # Convert Hz to ms interval
        self.vizTimer.timeout.connect(self.timerCallback)
        self.vizTimer.start()

        #self.input_ser = serial.Serial('COM8') #Serial port for STM32
        #self.input_ser = serial.Serial('/dev/tty.usbmodem14202') #Serial port for STM32
        self.input_ser = serial.serial_for_url('/dev/ttyACM0') #Serial port for STM32
        self.input_ser.baudrate = 230400

        self.display_on = True

        self.show()

        self.processor = PyTactio.SerialProcessor(self.input_ser)

        self.threadpool = QtCore.QThreadPool()
        self.worker = ParseThread.Parser(self.processor) # Any other args, kwargs are passed to the run function
        self.worker.signals.gridData.connect(self.parseResultCallback)
        self.worker.signals.sensorList.connect(self.sensorListCallback)
        self.threadpool.start(self.worker) 

        menuBar = self.menuBar()
        toolsMenu = menuBar.addMenu("Tools")
        flash = toolsMenu.addAction("Flash LEDs")
        flash.triggered.connect(self.flashSequenceLEDs)

        heartDisable = toolsMenu.addAction("Disable Heartbeat")
        heartDisable.triggered.connect(self.disableAllHeartbeat)

        heartEnable = toolsMenu.addAction("Enable Heartbeat")
        heartEnable.triggered.connect(self.enableAllHeartbeat)

    def flashSequenceLEDs(self):
        for i in self.sensorIDs:
            self.processor.sendLEDon(i)
            time.sleep(0.2)
        time.sleep(0.5)
        for i in self.sensorIDs:
            self.processor.sendLEDoff(i)
            time.sleep(0.2)

    def disableAllHeartbeat(self):
        for i in self.sensorIDs:
            self.processor.sendHeartOff(i)

    def enableAllHeartbeat(self):
        for i in self.sensorIDs:
            self.processor.sendHeartOn(i)

    def sendMessageCallback(self, sendData):
        if(sendData[0] == PyTactio.SerialActions.LEDON):
            self.processor.sendLEDon(sendData[1])
        elif(sendData[0] == PyTactio.SerialActions.LEDOFF):
            self.processor.sendLEDoff(sendData[1])
        elif(sendData[0] == PyTactio.SerialActions.CAL_BIAS):
            self.processor.sendCalCmd(sendData[1])
        elif(sendData[0] == PyTactio.SerialActions.BIAS_EN):
            self.processor.sendBiasCalEn(sendData[1])
        elif(sendData[0] == PyTactio.SerialActions.BIAS_DIS):
            self.processor.sendBiasCalDis(sendData[1])
        elif(sendData[0] == PyTactio.SerialActions.HEART_ON):
            self.processor.sendHeartOn(sendData[1])
        elif(sendData[0] == PyTactio.SerialActions.HEART_OFF):
            self.processor.sendHeartOff(sendData[1])
    
    def sensorListCallback(self, sensorList):
        print(sensorList)

    def parseResultCallback(self, parseResult):
        self.sensorWidgets[self.sensorIDs.index(parseResult[0])].setData(parseResult[1])
        #print(parseResult[1])

    def fileSelCallback(self):
        self.display_on = False
        save_name = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', options=QtGui.QFileDialog.DontUseNativeDialog)[0]
        self.fileLine.setText(save_name)
        self.display_on = True

    #start/stop recording function
    #clear array on restart
    def record(self):
        self.is_recording = not self.is_recording
        if self.is_recording:
            self.recording = {id : np.empty((1,4,4)) for id in self.sensorIDs} #dictionary holding previous recordings
            self.rec_btn.setStyleSheet("min-height: 50px;"
                                       "max-height: 50px;"
                                       "min-width: 50px;"
                                       "max-width: 50px;"
                                       "background-color: red;"
                                       "color: black;"
                                       "border-radius: 25px")
        else:
            self.rec_btn.setStyleSheet("min-height: 50px;"
                                       "max-height: 50px;"
                                       "min-width: 50px;"
                                       "max-width: 50px;"
                                       "background-color: gray;"
                                       "color: red;"
                                       "border-radius: 25px")
            save_name = ""
            if(self.fileLine.text() == ''):
                save_name = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', options=QtGui.QFileDialog.DontUseNativeDialog)[0]
            else:
                save_name = self.fileLine.text()

            if save_name != '':
                with open(save_name, "w") as outfile:  
                    json.dump(self.recording, outfile, cls=NumpyArrayEncoder) 

    def timerCallback(self): # Kicks off when QTimer has a timeout event
        if self.is_recording:
            for id in self.sensorIDs:
                self.recording[id] = np.append(self.recording[id], \
                    np.expand_dims(self.sensorWidgets[self.sensorIDs.index(id)].data,axis=0),axis=0)

    # Add Keyboard Shortcuts
    def keyPressEvent(self, event):
        if(event.key() == QtCore.Qt.Key_Escape): #Escape automatically closes
            self.close()
    
    def killParserThread(self):
        self.worker.alive = False
        while self.threadpool.activeThreadCount() > 0:
            continue
    
    def closeEvent(self, event):
        self.killParserThread()
        event.accept()



if (__name__ == "__main__"):
    app = QtWidgets.QApplication(sys.argv)
    window = MultiSensorVis()
    # window.show()
    sys.exit(app.exec_())
