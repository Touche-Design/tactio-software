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

class MultiSensorVis(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(QtWidgets.QMainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Tactio")
        position_data = et.parse('2sensor.xml').getroot()
        self.sensorCount = len(position_data)
        self.sensorIDs = [int(position_data[i].find('id').text) for i in range(self.sensorCount)]
        print(self.sensorIDs)

        sensorAreaWidget = QtGui.QWidget()
        self.sensorWidgets = [SingleGrid.SensorGrid() for i in range(self.sensorCount)]
        for i in range(self.sensorCount):
            self.sensorWidgets[i].setParent(sensorAreaWidget)
            self.sensorWidgets[i].resize(300,300)
            sensorx = int(position_data[i].find('x_pos').text)
            sensory = int(position_data[i].find('y_pos').text)
            self.sensorWidgets[i].move(sensorx, sensory)

        sensorAreaWidget.setMinimumSize(800, 800)
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


        #nesting for UI buttons
        buttonHbox = QtWidgets.QHBoxLayout()
        buttonHbox.addWidget(self.fileLine)
        #buttonHbox.addSpacing(10)
        buttonHbox.addWidget(self.fileSelBtn)
        #buttonHbox.addSpacing(10)
        buttonHbox.addWidget(self.rec_btn)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(sensorAreaWidget)

        vbox.addItem(buttonHbox)
        mainWidget = QtWidgets.QWidget()
        mainWidget.setLayout(vbox) 
        self.setCentralWidget(mainWidget)

        #initializing recording
        self.is_recording = False
        #self.recording = np.zeros((1,4,4))
        self.recording = {id : np.zeros((1,4,4)) for id in self.sensorIDs} #dictionary holding previous recordings

        # QTimer kicks off every 0.1 seconds to update the visualization
        self.vizTimer = QtCore.QTimer()
        self.vizTimer.setInterval(10) # Convert Hz to ms interval
        self.vizTimer.timeout.connect(self.timerCallback)
        self.vizTimer.start()

        #self.input_ser = serial.Serial('COM8') #Serial port for STM32
        self.input_ser = serial.Serial('/dev/ttyACM0') #Serial port for STM32
        self.input_ser.baudrate = 9600

        self.display_on = True

        self.show()

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
            self.recording = {id : np.zeros((1,4,4)) for id in self.sensorIDs} #dictionary holding previous recordings
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
            print(self.fileLine.text())
            if(self.fileLine.text() == ''):
                save_name = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', options=QtGui.QFileDialog.DontUseNativeDialog)[0]
            else:
                save_name = self.fileLine.text()

            if save_name != '':
                with open(save_name, "w") as outfile:  
                    json.dump(self.recording, outfile, cls=NumpyArrayEncoder) 

    def timerCallback(self): # Kicks off when QTimer has a timeout event
        self.parseSerial()

        # out_dict = {id : self.sensorWidgets[self.sensorIDs.index(id)].data for id in self.sensorIDs}
        if self.is_recording:
            for id in self.sensorIDs:
                self.recording[id] = np.append(self.recording[id], \
                    np.expand_dims(self.sensorWidgets[self.sensorIDs.index(id)].data,axis=0),axis=0)
        # max_ind = np.argmax(array, axis=-1)

    def parseSerial(self): # Parses the input from serial port and converts to array
        if(not self.input_ser.isOpen()): # Skip and return zeros if there is nothing plugged in
            return np.zeros((4,4))
        count = 0 # Indicates row
        temp_array = np.zeros((4,4))
        started = False
        inStr = self.input_ser.readline()
        print(inStr)
        inputs = inStr.decode('utf-8').split(";")
        if(inputs[0][0] == '$'):
            started = True

        if(len(inputs) > 1 and started):
            id = int(inputs[0][1:])
            print(id)
            for x in inputs[1:]:
                row_split = x.split(",")
                if(row_split[0].find("$") == -1 and len(row_split) > 1):
                    row_int = [int(row_split[i]) for i in range(len(row_split))]
                    if(np.shape(row_int)[0] == 4):
                        temp_array[count,:] = row_int
                        count += 1
            if(count > 3):
                # print(temp_array)
                self.sensorWidgets[self.sensorIDs.index(id)].setData(temp_array)
                # return temp_array
        else:
            return np.zeros((4,4))


    # Add Keyboard Shortcuts
    def keyPressEvent(self, event):
        if(event.key() == QtCore.Qt.Key_Escape): #Escape automatically closes
            self.close()


if (__name__ == "__main__"):
    app = QtWidgets.QApplication(sys.argv)
    window = MultiSensorVis()
    # window.show()
    sys.exit(app.exec_())