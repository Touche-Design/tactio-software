import xml.etree.ElementTree as et
from PyQt5 import QtWidgets, QtCore, Qt, QtGui
import sys  # We need sys so that we can pass argv to QApplication
import os
import numpy as np

import SingleGrid

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


    # Add Keyboard Shortcuts
    def keyPressEvent(self, event):
        if(event.key() == QtCore.Qt.Key_Escape): #Escape automatically closes
            self.close()


if (__name__ == "__main__"):
    app = QtWidgets.QApplication(sys.argv)
    window = MultiSensorVis()
    # window.show()
    sys.exit(app.exec_())