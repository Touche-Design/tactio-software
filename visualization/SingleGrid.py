from PyQt5 import QtWidgets, QtCore, Qt, QtGui
from pyqtgraph import PlotWidget, plot
import random
import sys  # We need sys so that we can pass argv to QApplication
import os

import serial
import numpy as np


class GridPoint(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super(QtWidgets.QWidget, self).__init__(*args, **kwargs)
        self.setAutoFillBackground(True)
        #self.palette.setColor(QtGui.QPalette.Window, Qt.red)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor(random.randrange(255), random.randrange(255), random.randrange(255)))
        self.setPalette(p)
        self.setMinimumHeight(80)
        self.setMinimumWidth(80)

    def setColor(self, color):
        p = self.palette()
        p.setColor(self.backgroundRole(), color)
        self.setPalette(p)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self,  *args, **kwargs):
        super(QtWidgets.QMainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Tactio 1")
        self.gridWidgets = [[GridPoint(), GridPoint(), GridPoint(), GridPoint()], 
        [GridPoint(), GridPoint(), GridPoint(), GridPoint()],
        [GridPoint(), GridPoint(), GridPoint(), GridPoint()],
        [GridPoint(), GridPoint(), GridPoint(), GridPoint()]]

        hboxes = [QtWidgets.QHBoxLayout(), QtWidgets.QHBoxLayout(), QtWidgets.QHBoxLayout(), QtWidgets.QHBoxLayout()]
        vbox = QtWidgets.QVBoxLayout()
        for i in range(len(hboxes)):
            for j in range(len(self.gridWidgets[i])):
                hboxes[i].addWidget(self.gridWidgets[i][j])
                hboxes[i].addSpacing(10)
            vbox.addItem(hboxes[i])
        mainWidget = QtWidgets.QWidget()
        mainWidget.setLayout(vbox) 
        self.setCentralWidget(mainWidget)

        self.vizTimer = QtCore.QTimer()
        self.vizTimer.setInterval(int(1000/5))
        self.vizTimer.timeout.connect(self.timerCallback)
        self.vizTimer.start()

        self.input_ser = serial.Serial('/dev/ttyACM0') #Serial port for Arduino Uno
        self.input_ser.baudrate = 9600

    def timerCallback(self):
        array = self.parseSerial()
        for i in range(len(self.gridWidgets[0])):
            for j in range(len(self.gridWidgets)):
                self.gridWidgets[i][j].setColor(QtGui.QColor(int(array[i][j])))
        
    def parseSerial(self):
        if(not self.input_ser.isOpen()):
            return 
        #print("Called")
        count = 0
        temp_array = np.zeros((4,4))
        while self.input_ser.in_waiting:
            inStr = self.input_ser.readline()
            #print(inStr)
            inputs = inStr.decode('utf-8').split(" ")
            line_temp = [string for string in inputs if string != ""]
            if(len(line_temp) > 1):
                line_int = [int(line_temp[i]) for i in range(len(line_temp)-1)]

                if(np.shape(line_int)[0] == 4):
                    temp_array[count,:] = line_int
                    count += 1

                if(count > 3):
                    #print(temp_array)
                    break
        return temp_array


       

if (__name__ == "__main__"):
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())
