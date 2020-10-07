from PyQt5 import QtWidgets, QtCore, Qt, QtGui
from pyqtgraph import PlotWidget, plot
import random
import sys  # We need sys so that we can pass argv to QApplication
import os

import serial
import numpy as np

'''
The GridPoint Widget represents 1 colored square in a sensor's grid
'''

class GridPoint(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(QtWidgets.QWidget, self).__init__(*args, **kwargs)
        self.setAutoFillBackground(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor(random.randrange(255), random.randrange(255), random.randrange(255)))
        self.setPalette(p)
        self.setMinimumHeight(80)
        self.setMinimumWidth(80)

    def setColor(self, color):
        p = self.palette()
        p.setColor(self.backgroundRole(), color)
        self.setPalette(p)

'''
This widget is the main window of the visualization. It has a grid of 4 x 4 grid points which change color based on input
'''

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self,  *args, **kwargs):
        super(QtWidgets.QMainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Tactio")
        # Grid Widgets stored in a member variable array
        self.gridWidgets = [[GridPoint(), GridPoint(), GridPoint(), GridPoint()],
        [GridPoint(), GridPoint(), GridPoint(), GridPoint()],
        [GridPoint(), GridPoint(), GridPoint(), GridPoint()],
        [GridPoint(), GridPoint(), GridPoint(), GridPoint()]]

        # We arrange rows using HBoxLayouts
        hboxes = [QtWidgets.QHBoxLayout(), QtWidgets.QHBoxLayout(), QtWidgets.QHBoxLayout(), QtWidgets.QHBoxLayout()]

        # And a single VBoxLayout arranges all the rows into a grid
        vbox = QtWidgets.QVBoxLayout()

        # Loop through all widgets and add them accordingly
        for i in range(len(hboxes)):
            for j in range(len(self.gridWidgets[i])):
                hboxes[i].addWidget(self.gridWidgets[i][j])
                hboxes[i].addSpacing(10) #Spacing between columns
            vbox.addItem(hboxes[i]) #Add each row to the VBoxLayout

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
        #self.save_btn = QtGui.QPushButton("Save to File", self)
        #self.save_btn.setStyleSheet("min-width: 80px;"
        #                            "max-width: 80px")
        #self.save_btn.clicked.connect(self.file_save)

        #nesting for UI buttons
        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(self.rec_btn)
        #hbox.addSpacing(10)
        #hbox.addWidget(self.save_btn)
        vbox.addItem(hbox)
        mainWidget = QtWidgets.QWidget()
        mainWidget.setLayout(vbox) 
        self.setCentralWidget(mainWidget)

        # QTimer kicks off every 0.2 seconds to update the visualization
        self.vizTimer = QtCore.QTimer()
        self.vizTimer.setInterval(10) # Convert Hz to ms interval
        self.vizTimer.timeout.connect(self.timerCallback)
        self.vizTimer.start()

        #TODO: Implement Communication Rate Limiting

        self.input_ser = serial.Serial('COM3') #Serial port for STM32
        #self.input_ser = serial.Serial('/dev/ttyACM0') #Serial port for STM32
        self.input_ser.baudrate = 9600

        #initializing recording
        self.is_recording = False
        self.recording = np.zeros((1,4,4))


    def timerCallback(self): # Kicks off when QTimer has a timeout event
        array = self.parseSerial() # Turns serial data into 2D array of integer values
        #print(array)
        if self.is_recording:
            self.recording = np.append(self.recording,np.expand_dims(array,axis=0),axis=0)
        max_ind = np.argmax(array, axis=-1)
        for i in range(len(self.gridWidgets[0])): 
            for j in range(len(self.gridWidgets)):
                color = self.clamp(0, array[i][j], 255)
                self.gridWidgets[i][j].setColor(QtGui.QColor(0, 0, color)) # Assigns corresponding value to grid widget color
        '''
        for i in range(len(self.gridWidgets[0])): 
            for j in range(len(self.gridWidgets)):
                self.gridWidgets[i][j].setColor(QtGui.QColor(0, 0, 0)) # Assigns corresponding value to grid widget color

        self.gridWidgets[max_ind[0]][max_ind[1]].setColor(QtGui.QColor(0, 0, int(array[max_ind[0]][max_ind[1]]))) # Assigns corresponding value to grid widget color
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
            #print(id)
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

    def clamp(self, minimum, x, maximum):
        return max(minimum, min(x, maximum))

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

    #saving files function
    #def file_save(self):
    #    if self.recording.ndim > 2:
    #        name = QtGui.QFileDialog.getSaveFileName(self, 'Save File')
    #        file = open(name[0], 'w')
    #        for x in np.arange(1,self.recording.shape[0]):
    #            np.savetxt(file, self.recording[x], delimiter=',', fmt='%d')
    #            file.write('\n')
    #        file.close()
    #    else:
    #        error_window = QtWidgets.QMessageBox()
    #        error_window.setIcon(QtWidgets.QMessageBox.Critical)
    #        error_window.setText("Recording is Empty!")
    #        error_window.setWindowTitle("Error")
    #        error_window.exec_()

        


if (__name__ == "__main__"):
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
