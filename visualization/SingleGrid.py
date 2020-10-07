from PyQt5 import QtWidgets, QtCore, Qt, QtGui
from pyqtgraph import PlotWidget, plot
import random
import sys  # We need sys so that we can pass argv to QApplication
import os

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


        #TODO: Implement Communication Rate Limiting

        self.setLayout(vbox)

    def setColors(self, colors):
        for i in range(len(self.gridWidgets[0])): 
            for j in range(len(self.gridWidgets)):
                self.setGridColors(self.gridWidgets[i][j], colors[i][j])

    def setGridColors(self, gridWidget, color):
        clip_color = self.clamp(0, color, 255)
        gridWidget.setColor(QtGui.QColor(0, 0, clip_color)) # Assigns corresponding value to grid widget color


    def clamp(self, minimum, x, maximum):
        return max(minimum, min(x, maximum))