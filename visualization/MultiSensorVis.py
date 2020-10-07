import xml.etree.ElementTree as et
from PyQt5 import QtWidgets, QtCore, Qt, QtGui
import sys  # We need sys so that we can pass argv to QApplication
import os
import numpy as np
import SingleGrid
import serial

class MultiSensorVis(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(QtWidgets.QMainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Tactio")
        position_data = et.parse('2sensor.xml').getroot()
        sensorAreaWidget = QtGui.QWidget()
        self.sensor1 = SingleGrid.SensorGrid()
        self.sensor1.setParent(sensorAreaWidget)
        sensorAreaWidget.setMinimumSize(800, 800)
        print(int(position_data[0].find('id').text))
        self.sensor1.resize(100,100)
        sensor1x = int(position_data[0].find('x_pos').text)
        sensor1y = int(position_data[0].find('y_pos').text)
        self.sensor1.move(sensor1x, sensor1y)


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

        #nesting for UI buttons
        buttonHbox = QtWidgets.QHBoxLayout()
        buttonHbox.addWidget(self.rec_btn)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(sensorAreaWidget)

        vbox.addItem(buttonHbox)
        mainWidget = QtWidgets.QWidget()
        mainWidget.setLayout(vbox) 
        self.setCentralWidget(mainWidget)

        #initializing recording
        self.is_recording = False
        self.recording = np.zeros((1,4,4))

        # QTimer kicks off every 0.1 seconds to update the visualization
        self.vizTimer = QtCore.QTimer()
        self.vizTimer.setInterval(10) # Convert Hz to ms interval
        self.vizTimer.timeout.connect(self.timerCallback)
        self.vizTimer.start()

        #self.input_ser = serial.Serial('COM8') #Serial port for STM32
        self.input_ser = serial.Serial('/dev/ttyACM0') #Serial port for STM32
        self.input_ser.baudrate = 9600

        self.show()

    #start/stop recording function
    #clear array on restart
    def record(self):
        self.is_recording = not self.is_recording
        if self.is_recording:
            self.recording = np.zeros((1,4,4))
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
            save_name = QtGui.QFileDialog.getSaveFileName(self, 'Save File')[0]
            if save_name != '':
                file = open(save_name, 'w')
                for x in np.arange(1,self.recording.shape[0]):
                    np.savetxt(file, self.recording[x], delimiter=',', fmt='%d')
                    file.write('\n')
                file.close()

    def timerCallback(self): # Kicks off when QTimer has a timeout event
        array = self.parseSerial() # Turns serial data into 2D array of integer values

        # max_ind = np.argmax(array, axis=-1)
        self.sensor1.setColors(array)

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
                return temp_array
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