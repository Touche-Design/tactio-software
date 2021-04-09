from PyQt5 import QtWidgets, QtCore, Qt, QtGui
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
        # Ignoring size policy to enforce squareness on text box in grid point
        #self.value.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Ignored, QtGui.QSizePolicy.Ignored)) # TODO: Uncomment
        self.value.setParent(self)
        self.value.setStyleSheet('QLabel {color: #FFFFFF;}')
        self.value.setAlignment(QtCore.Qt.AlignCenter)
        self.value.setFont(QtGui.QFont("Arial", 10))

        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor(0,0,0)) # Initialize to black
        self.setPalette(p)
        self.setValue(0)
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(self.value) # Placing label in a layout lets it expand to hold more digits
        self.setLayout(layout)

    '''
    Sets numerical of label
    '''
    def setValue(self, num):
        self.value.setText("{:.2f}".format(float(num)))

    '''
    Dynamic font changing based on widget size
    ''' 
    def resizeEvent(self, e):
        self.value.setFont(QtGui.QFont("Arial", int(self.width()/6)))

    '''
    Sets color to some scale of blue (0 - 255)
    '''
    def setColor(self, color):
        p = self.palette()
        p.setColor(self.backgroundRole(), color)
        self.setPalette(p)

 


'''
This widget is the main component of the visualization. It has a grid of 4 x 4 grid points which change color based on input
'''
class SensorGrid(QtWidgets.QWidget):
    sendData = QtCore.pyqtSignal((tuple)) # Define signal
    def __init__(self,  *args, **kwargs):
        super(QtWidgets.QWidget, self).__init__(*args, **kwargs)

        # Grid Widgets stored in a 2D array
        self.gridWidgets = [[GridPoint(), GridPoint(), GridPoint(), GridPoint()],
        [GridPoint(), GridPoint(), GridPoint(), GridPoint()],
        [GridPoint(), GridPoint(), GridPoint(), GridPoint()],
        [GridPoint(), GridPoint(), GridPoint(), GridPoint()]]

        # numerical data associated with each measurement
        self.data = np.zeros((4,4))
        self.id = 0 # Sensor ID

        # Arrange rows using HBoxLayouts
        hboxes = [QtWidgets.QHBoxLayout(), QtWidgets.QHBoxLayout(), QtWidgets.QHBoxLayout(), QtWidgets.QHBoxLayout()]

        # And a single VBoxLayout arranges all the rows into a grid
        vbox = QtWidgets.QVBoxLayout()
        #self.id_box = QtWidgets.QLabel("Sensor {}".format(self.id))
        #self.id_box.setAlignment(QtCore.Qt.AlignCenter)
        #vbox.addWidget(self.id_box)

        # Loop through all widgets and add them to layouts accordingly
        for i in range(len(hboxes)):
            for j in range(len(self.gridWidgets[i])):
                hboxes[i].addWidget(self.gridWidgets[i][j])
                hboxes[i].setSpacing(0) #Spacing between columns
            vbox.addItem(hboxes[i]) #Add each row to the VBoxLayout

        vbox.setSpacing(0)
        self.setLayout(vbox)

        #self.setMinimumSize(200,200) # Minimum size based on default font size

    '''
    Sets ID and text
    '''
    def setId(self, id):
        self.id = id
        #self.id_box.setText("Sensor {}".format(self.id))

    '''
    Maintains squareness of widget
    '''
    def resizeEvent(self, e):
        for i in range(len(self.gridWidgets[0])): 
            for j in range(len(self.gridWidgets)):
                self.gridWidgets[i][j].setFixedSize(self.width() / 4, self.height()/4)

    '''
    Sets data and color of grid
    '''
    def setData(self, data, show = True):
        self.data = data
        if(show):
            for i in range(len(self.gridWidgets[0])): 
                for j in range(len(self.gridWidgets)):
                    self.gridWidgets[i][j].setValue(data[i][j])
                    self.setGridColor(self.gridWidgets[i][j], self.data2color(data[i][j]))

    '''
    Used to compute scalings for colors to make the visualis look prettier
    '''
    def data2color(self,data): # Here we can add some sort of scaling (linear or logarithmic)
        return data*500

    '''
    Sets the color of a particular grid widget
    '''
    def setGridColor(self, gridWidget, color):
        clip_color = self.clamp(0, color, 255)
        gridWidget.setColor(QtGui.QColor(0, 0, clip_color)) # Assigns corresponding value to grid widget color

    '''
    Clamps a value between the minimum and maximum
    '''
    def clamp(self, minimum, x, maximum):
        return max(minimum, min(x, maximum))

    ''' 
    Handles the menu when a sensor is right-clicked on
    '''
    def contextMenuEvent(self, event):
        contextMenu = QtWidgets.QMenu(self) # Main menu to send commands to a particular sensor
        onLEDAct = contextMenu.addAction("Turn LED On")
        offLEDAct = contextMenu.addAction("Turn LED Off")
        onHeartAct = contextMenu.addAction("Enable Heartbeat")
        offHeartAct = contextMenu.addAction("Disable Heartbeat")

        calMenu = QtWidgets.QMenu(self) # Sub-menu for calibration options
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
        elif(action == onHeartAct):
            self.sendData.emit((SerialActions.HEART_ON, self.id))
        elif(action == offHeartAct):
            self.sendData.emit((SerialActions.HEART_OFF, self.id))

# This class contains 4 SensorGrids to make an 8x8 grid
class SensorQuad(QtWidgets.QWidget):
    def __init__(self,  *args, **kwargs):
        super(QtWidgets.QWidget, self).__init__(*args, **kwargs)
        self.id = 0
        self.sensors = [SensorGrid(), SensorGrid(), SensorGrid(), SensorGrid()]
        # Arrange rows using HBoxLayouts
        hboxes = [QtWidgets.QHBoxLayout(), QtWidgets.QHBoxLayout()]

        # And a single VBoxLayout arranges all the rows into a grid
        vbox = QtWidgets.QVBoxLayout()
        hboxes[0].addWidget(self.sensors[1])
        hboxes[0].addWidget(self.sensors[0])
        hboxes[0].setSpacing(0)

        hboxes[1].addWidget(self.sensors[2])
        hboxes[1].addWidget(self.sensors[3])
        hboxes[1].setSpacing(0)

        vbox.addItem(hboxes[0])
        vbox.addItem(hboxes[1])
        vbox.addStretch(1)
        vbox.setSpacing(0)
        self.setLayout(vbox)

    def setData(self, quad, data):
        self.sensors[quad].setData(data)

    def resizeEvent(self, e):
        for i in range(len(self.sensors)):
            self.sensors[i].setFixedSize(self.width() / 2, self.height() / 2)

    def setId(self, id):
        self.id = id