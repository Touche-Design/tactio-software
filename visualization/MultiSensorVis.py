import xml.etree.ElementTree as et
from PyQt5 import QtWidgets, QtCore, Qt, QtGui
import sys  # We need sys so that we can pass argv to QApplication
import os
import numpy as np
import serial
import json
import time

from NumpyArrayEncoder import NumpyArrayEncoder
import SingleGrid
import ParseThread

class MultiSensorVis(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(QtWidgets.QMainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Tactio")
        position_data = et.parse('2sensor.xml').getroot()
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
        maxsizeX = max(sensorXpos) + sizes[sensorXpos.index(max(sensorXpos))] + min(sensorXpos) 
        maxsizeY = max(sensorYpos) + sizes[sensorYpos.index(max(sensorYpos))] + min(sensorYpos) 

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

        flashLED = QtWidgets.QPushButton("Flash LEDs")
        flashLED.clicked.connect(self.flashSequenceLEDs)
        cmdButtonHbox = QtWidgets.QHBoxLayout()
        cmdButtonHbox.addWidget(flashLED)


        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(sensorAreaWidget)

        vbox.addItem(recordButtonHbox)
        vbox.addItem(cmdButtonHbox)
        mainWidget = QtWidgets.QWidget()
        mainWidget.setLayout(vbox)
        self.setCentralWidget(mainWidget)

        #initializing recording
        self.is_recording = False
        #self.recording = np.zeros((1,4,4))
        self.recording = {id : np.zeros((1,4,4)) for id in self.sensorIDs} #dictionary holding previous recordings

        # QTimer kicks off every 0.1 seconds to update the visualization
        self.vizTimer = QtCore.QTimer()
        self.vizTimer.setInterval(50) # Convert Hz to ms interval
        self.vizTimer.timeout.connect(self.timerCallback)
        self.vizTimer.start()

        #self.input_ser = serial.Serial('COM8') #Serial port for STM32
        self.input_ser = serial.Serial('/dev/ttyACM0') #Serial port for STM32
        self.input_ser.baudrate = 9600

        self.display_on = True

        self.show()

        self.threadpool = QtCore.QThreadPool()
        self.worker = ParseThread.Parser(self.input_ser) # Any other args, kwargs are passed to the run function
        self.worker.signals.gridData.connect(self.parseResultCallback)
        self.worker.signals.sensorList.connect(self.sensorListCallback)
        self.threadpool.start(self.worker) 

    def flashSequenceLEDs(self):
        for i in self.sensorIDs:
            self.sendMessageCallback(((0b10000011, i)))
            time.sleep(0.2)
        time.sleep(0.5)
        for i in self.sensorIDs:
            self.sendMessageCallback(((0b10000010, i)))
            time.sleep(0.2)


    def sendMessageCallback(self, sendData):
        self.input_ser.write(int.to_bytes(sendData[0], 1, byteorder='big'))
        self.input_ser.write(int.to_bytes(sendData[1], 1, byteorder='big'))
        self.input_ser.flush()
    
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
        #self.parseSerial()

        # out_dict = {id : self.sensorWidgets[self.sensorIDs.index(id)].data for id in self.sensorIDs}
        if self.is_recording:
            for id in self.sensorIDs:
                self.recording[id] = np.append(self.recording[id], \
                    np.expand_dims(self.sensorWidgets[self.sensorIDs.index(id)].data,axis=0),axis=0)
        # max_ind = np.argmax(array, axis=-1)

    '''
    def parseSerial(self): # Parses the input from serial port and converts to array
        if(not self.input_ser.isOpen()): # Skip and return zeros if there is nothing plugged in
            return np.zeros((4,4))
        count = 0 # Indicates row
        temp_array = np.zeros((4,4))
        started = False
        inStr = self.input_ser.readline()
        inputs = inStr.decode('utf-8').split(";")
        if(inputs[0][0] == '$'):
            started = True

        if(len(inputs) > 1 and started):
            id = int(inputs[0][1:])
            for x in inputs[1:]:
                row_split = x.split(",")
                if(row_split[0].find("$") == -1 and len(row_split) > 1):
                    row_int = [int(row_split[i]) for i in range(len(row_split))]
                    if(np.shape(row_int)[0] == 4):
                        temp_array[count,:] = row_int
                        count += 1
            if(count > 3):
                print(temp_array)
                self.sensorWidgets[self.sensorIDs.index(id)].setData(temp_array)
                # return temp_array
        else:
            return np.zeros((4,4))
    '''

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