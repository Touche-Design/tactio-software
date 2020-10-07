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

class SensorGrid(QtWidgets.QWidget):
    def __init__(self,  *args, **kwargs):
        super(QtWidgets.QWidget, self).__init__(*args, **kwargs)
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

        # QTimer kicks off every 0.2 seconds to update the visualization
        self.vizTimer = QtCore.QTimer()
        self.vizTimer.setInterval(10) # Convert Hz to ms interval
        self.vizTimer.timeout.connect(self.timerCallback)
        self.vizTimer.start()

        #TODO: Implement Communication Rate Limiting

        #self.input_ser = serial.Serial('COM8') #Serial port for STM32
        self.input_ser = serial.Serial('/dev/ttyACM0') #Serial port for STM32
        self.input_ser.baudrate = 115200
        self.setLayout(vbox)

    def setGridColors(self, gridWidget, color):
        clip_color = self.clamp(0, color, 255)
        gridWidget.setColor(QtGui.QColor(0, 0, clip_color)) # Assigns corresponding value to grid widget color

    def timerCallback(self): # Kicks off when QTimer has a timeout event
        array = self.parseSerial() # Turns serial data into 2D array of integer values

        # max_ind = np.argmax(array, axis=-1)
        for i in range(len(self.gridWidgets[0])): 
            for j in range(len(self.gridWidgets)):
                self.setGridColors(self.gridWidgets[i][j], array[i][j])

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
            id = int(inputs[0][2:-1])
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

    def clamp(self, minimum, x, maximum):
        return max(minimum, min(x, maximum))