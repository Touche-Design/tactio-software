import xml.etree.ElementTree as et
from PyQt5 import QtWidgets, QtCore, Qt, QtGui
import sys  # We need sys so that we can pass argv to QApplication
import os

import SingleGrid

class MultiSensorVis(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(QtWidgets.QMainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Tactio")
        self.position_data = et.parse('2sensor.xml').getroot()
        widget = QtGui.QWidget()
        self.sensor1 = SingleGrid.SensorGrid()
        self.sensor1.setParent(widget)
        self.setCentralWidget(widget)
        self.sensor1.resize(100,100)
        self.sensor1.move(50,50)
        self.show()

    def keyPressEvent(self, event):
        if(event.key() == QtCore.Qt.Key_Escape):
            self.close()


if (__name__ == "__main__"):
    app = QtWidgets.QApplication(sys.argv)
    window = MultiSensorVis()
    # window.show()
    sys.exit(app.exec_())