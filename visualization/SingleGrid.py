from PyQt5 import QtWidgets, QtCore, Qt, QtGui
from pyqtgraph import PlotWidget, plot
import random
import sys  # We need sys so that we can pass argv to QApplication
import os
from PyTactio import SerialActions

import numpy as np

'''
The GridPoint Widget represents 1 colored square in a sensor's grid
'''

class GridPoint(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(QtWidgets.QWidget, self).__init__(*args, **kwargs)
        self.setAutoFillBackground(True)
        self.value = QtWidgets.QLabel()
        self.value.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Ignored,
                                             QtGui.QSizePolicy.Ignored))
        self.value.setParent(self)
        self.value.setStyleSheet('QLabel {color: #FFFFFF;}')
        self.value.setAlignment(QtCore.Qt.AlignCenter)
        self.value.setFont(QtGui.QFont("Arial", 10))

        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor(0,0,0))
        self.setPalette(p)
        self.setValue(0)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.value)
        self.setLayout(layout)

    def setValue(self, num):
        self.value.setText(str(int(num)))
    
    def resizeEvent(self, e):
        self.value.setFont(QtGui.QFont("Arial", int(self.width()/6)))

    def setColor(self, color):
        p = self.palette()
        p.setColor(self.backgroundRole(), color)
        self.setPalette(p)

 


'''
This widget is the main component of the visualization. It has a grid of 4 x 4 grid points which change color based on input
'''

class SensorGrid(QtWidgets.QWidget):
    sendData = QtCore.pyqtSignal((tuple))
    def __init__(self,  *args, **kwargs):
        super(QtWidgets.QWidget, self).__init__(*args, **kwargs)
        # Grid Widgets stored in a member variable array
        self.gridWidgets = [[GridPoint(), GridPoint(), GridPoint(), GridPoint()],
        [GridPoint(), GridPoint(), GridPoint(), GridPoint()],
        [GridPoint(), GridPoint(), GridPoint(), GridPoint()],
        [GridPoint(), GridPoint(), GridPoint(), GridPoint()]]

        self.data = np.zeros((4,4))
        self.id = 0

        # We arrange rows using HBoxLayouts
        hboxes = [QtWidgets.QHBoxLayout(), QtWidgets.QHBoxLayout(), QtWidgets.QHBoxLayout(), QtWidgets.QHBoxLayout()]

        # And a single VBoxLayout arranges all the rows into a grid
        vbox = QtWidgets.QVBoxLayout()
        self.id_box = QtWidgets.QLabel("Sensor {}".format(self.id))
        self.id_box.setAlignment(QtCore.Qt.AlignCenter)
        vbox.addWidget(self.id_box)

        # Loop through all widgets and add them accordingly
        for i in range(len(hboxes)):
            for j in range(len(self.gridWidgets[i])):
                hboxes[i].addWidget(self.gridWidgets[i][j])
                hboxes[i].setSpacing(0) #Spacing between columns
            vbox.addItem(hboxes[i]) #Add each row to the VBoxLayout

        vbox.setSpacing(0)
        self.setLayout(vbox)
        self.setMinimumSize(200,200)

    def setId(self, id):
        self.id = id
        self.id_box.setText("Sensor {}".format(self.id))
   
    def resizeEvent(self, e):
        for i in range(len(self.gridWidgets[0])): 
            for j in range(len(self.gridWidgets)):
                self.gridWidgets[i][j].setFixedSize(self.width() / 4, self.height()/4)

    def setData(self, data, show = True):
        self.data = data
        if(show):
            self.setColors(self.data2color(data))

    def data2color(self,data): # Here we can add some sort of scaling (linear or logarithmic)
        return data*3

    def setColors(self, colors):
        for i in range(len(self.gridWidgets[0])): 
            for j in range(len(self.gridWidgets)):
                self.gridWidgets[i][j].setValue(colors[i][j])
                self.setGridColor(self.gridWidgets[i][j], colors[i][j])

    def setGridColor(self, gridWidget, color):
        clip_color = self.clamp(0, color, 255)
        gridWidget.setColor(QtGui.QColor(0, 0, clip_color)) # Assigns corresponding value to grid widget color


    def clamp(self, minimum, x, maximum):
        return max(minimum, min(x, maximum))

    def contextMenuEvent(self, event):
        contextMenu = QtWidgets.QMenu(self)
        onLEDAct = contextMenu.addAction("Turn LED On")
        offLEDAct = contextMenu.addAction("Turn LED Off")
        calMenu = QtWidgets.QMenu(self)
        calMenu.setTitle("Calibration")
        calibrateBias = calMenu.addAction("Run Bias Calibration")
        turnBiasCalOn = calMenu.addAction("Enable Bias Cal")
        turnBiasCalOff = calMenu.addAction("Disable Bias Cal")
        contextMenu.addMenu(calMenu)

        action = contextMenu.exec_(self.mapToGlobal(event.pos()))
        if(action == onLEDAct):
            self.sendData.emit((SerialActions.LEDON, self.id))
        elif(action == offLEDAct):
            self.sendData.emit((SerialActions.LEDOFF, self.id))
        elif(action == calibrateBias):
            self.sendData.emit((SerialActions.CAL_BIAS, self.id))
        elif(action == turnBiasCalOn):
            self.sendData.emit((SerialActions.BIAS_EN, self.id))
        elif(action == turnBiasCalOff):
            self.sendData.emit((SerialActions.BIAS_DIS, self.id))
