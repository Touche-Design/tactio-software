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
        mainWidget = QtWidgets.QWidget()
        mainWidget.setLayout(vbox) 
        self.setCentralWidget(mainWidget)

        # QTimer kicks off every 0.2 seconds to update the visualization
        self.vizTimer = QtCore.QTimer()
        self.vizTimer.setInterval(int(1000/5)) # Convert Hz to ms interval
        self.vizTimer.timeout.connect(self.timerCallback)
        self.vizTimer.start()

        #TODO: Implement Communication Rate Limiting

        self.input_ser = serial.Serial('/dev/ttyACM0') #Serial port for STM32
        self.input_ser.baudrate = 9600

    def timerCallback(self): # Kicks off when QTimer has a timeout event
        array = self.parseSerial() # Turns serial data into 2D array of integer values
        for i in range(len(self.gridWidgets[0])): 
            for j in range(len(self.gridWidgets)):
                self.gridWidgets[i][j].setColor(QtGui.QColor(int(array[i][j]), 100, 100)) # Assigns corresponding value to grid widget color
        
    def parseSerial(self): # Parses the input from serial port and converts to array
        if(not self.input_ser.isOpen()): # Skip and return zeros if there is nothing plugged in
            return [[0]*4]*4
        count = 0 # Indicates row
        temp_array = np.zeros((4,4))
        started = False
        while self.input_ser.in_waiting:
            inStr = self.input_ser.readline()
            inputs = inStr.decode('utf-8').split(" ")
            line_temp = [string for string in inputs if string != ""]
            if(line_temp[0] == 'S'):
                started = True
                print("Started")

            if(len(line_temp) > 1 and started):
                line_int = [int(line_temp[i]) for i in range(len(line_temp)-1)]
                print(line_int)
                if(np.shape(line_int)[0] == 4):
                    temp_array[count,:] = line_int
                    count += 1

                if(count > 3):
                    #print(temp_array)
                    return temp_array


if (__name__ == "__main__"):
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
