import xml.etree.ElementTree as et
from PyQt5 import QtWidgets, QtCore, Qt, QtGui
import sys  # We need sys so that we can pass argv to QApplication
import os
import numpy as np
import serial
import json
import time
import PyTactio

from NumpyArrayEncoder import NumpyArrayEncoder
import SingleGrid
import ParseThread


'''
This class implements the main widget of the GUI
'''

class MultiSensorVis(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(QtWidgets.QMainWindow, self).__init__(*args, **kwargs)
        self.setWindowTitle("Tactio")

        '''
        Reads in XML data to define sensor locations
        '''
        position_data = et.parse('configs/1sensor.xml').getroot()
        self.sensorCount = len(position_data)
        self.sensorIDs = [int(position_data[i].find('id').text) for i in range(self.sensorCount)]

        '''
        Reads in XML data for parameters of model
        '''
        self.model_params = et.parse('model.xml').getroot()
        self.model_ids = [int(self.model_params[i].find('id').text) for i in range(len(self.model_params))]


        #Blank widget to act as parent for all sensor widgets
        sensorAreaWidget = QtGui.QWidget()

        self.sensorWidgets = [SingleGrid.SensorGrid() for i in range(self.sensorCount)]

        # Sets parameters of screen based on XML document
        sensorXpos = []
        sensorYpos = []
        sizes = []
        for i in range(self.sensorCount):
            self.sensorWidgets[i].setId(self.sensorIDs[i])
            self.sensorWidgets[i].sendData.connect(self.sendMessageCallback)
            self.sensorWidgets[i].setParent(sensorAreaWidget)
            sensorx = int(position_data[i].find('x_pos').text)
            sensorXpos.append(sensorx)
            sensory = int(position_data[i].find('y_pos').text)
            sensorYpos.append(sensory)
            size = 400
            try:
                # Size pulled from XML document
                size = int(position_data[i].find('size').text)
            except: # If size is unspecified
                size = 400
            sizes.append(size)
            self.sensorWidgets[i].resize(size,size)
            self.sensorWidgets[i].move(sensorx, sensory)

        # Compute Max Width and height of sensor area widget based on locations of farthest sensor widget
        maxsizeX = max(sensorXpos) + self.sensorWidgets[sensorXpos.index(max(sensorXpos))].width() + min(sensorXpos) 
        maxsizeY = max(sensorYpos) + self.sensorWidgets[sensorYpos.index(max(sensorYpos))].height() + min(sensorYpos) 
        sensorAreaWidget.setMinimumSize(maxsizeX, maxsizeY)

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

        # Line edit for selected recording file
        self.fileLine = QtWidgets.QLineEdit()
        self.fileLine.readOnly = True
        self.fileLine.setMaximumWidth(500)

        # Button to activate file dialogue box
        self.fileSelBtn = QtWidgets.QPushButton("...")
        self.fileSelBtn.clicked.connect(self.fileSelCallback)
        self.fileSelBtn.setMaximumWidth(50)

        # hbox holds all 3 buttons in a row
        recordButtonHbox = QtWidgets.QHBoxLayout()
        recordButtonHbox.addWidget(self.fileLine)
        recordButtonHbox.addWidget(self.fileSelBtn)
        recordButtonHbox.addWidget(self.rec_btn)

        # Vbox holds all widgets
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(sensorAreaWidget)
        vbox.addItem(recordButtonHbox)
        mainWidget = QtWidgets.QWidget()
        mainWidget.setLayout(vbox)
        self.setCentralWidget(mainWidget)

        # Initializing recording
        self.is_recording = False
        self.recording = {id : np.empty((1,4,4)) for id in self.sensorIDs} # Dictionary holding previous recordings

        # QTimer kicks off every 50ms to record the latest information (if available)
        self.vizTimer = QtCore.QTimer()
        self.vizTimer.setInterval(50) # Convert Hz to ms interval
        self.vizTimer.timeout.connect(self.timerCallback)
        self.vizTimer.start()

        #self.input_ser = serial.Serial('COM8') #Serial port for MBED Windows
        self.input_ser = serial.Serial('/dev/tty.usbmodem14202') #Serial port for MBED MacOS
        #self.input_ser = serial.Serial('/dev/ttyACM0') #Serial port for MBED Linux
        self.input_ser.baudrate = 230400
        self.show()

        # Input Processor is instance of PyTactio library
        self.processor = PyTactio.SerialProcessor(self.input_ser)

        # Threadpool used to run Parse Thread asynchronously
        self.threadpool = QtCore.QThreadPool()
        self.worker = ParseThread.Parser(self.processor) 
        self.worker.signals.gridData.connect(self.parseResultCallback) # Signal triggers callback to redraw sensor
        self.worker.signals.sensorList.connect(self.sensorListCallback) # Signal triggers callback to print data
        self.threadpool.start(self.worker) 
        
        self.calibrationOn=False # False = Raw value, True = Calibrated value

        # Top menu bar
        menuBar = self.menuBar()
        toolsMenu = menuBar.addMenu("Tools")
        flash = toolsMenu.addAction("Flash LEDs")
        flash.triggered.connect(self.flashSequenceLEDs) # Flash LEDs 

        heartDisable = toolsMenu.addAction("Disable Heartbeat")
        heartDisable.triggered.connect(self.disableAllHeartbeat) # Disables heartbeat on sensors

        heartEnable = toolsMenu.addAction("Enable Heartbeat")
        heartEnable.triggered.connect(self.enableAllHeartbeat) # Enables heartbeat on sensors

        calMenu = menuBar.addMenu("Calibration")
        calDisable = calMenu.addAction("Show Calibrated")
        calDisable.triggered.connect(self.enableCal) # Disables calibration on display

        calEnable = calMenu.addAction("Show Raw")
        calEnable.triggered.connect(self.disableCal) # Enables heartbeat on sensors


    '''
    Turns all LEDs on (one at a time), then turns all off
    Starts at the first one in the chain (defined in the XML)
    '''
    def flashSequenceLEDs(self):
        for i in self.sensorIDs:
            self.processor.sendLEDon(i)
            time.sleep(0.2)
        time.sleep(0.5)
        for i in self.sensorIDs:
            self.processor.sendLEDoff(i)
            time.sleep(0.2)

    '''
    Disables all sensor heartbeats
    '''
    def disableAllHeartbeat(self):
        for i in self.sensorIDs:
            self.processor.sendHeartOff(i)
            time.sleep(0.01)

    '''
    Enables all sensor heartbeats
    '''
    def enableAllHeartbeat(self):
        for i in self.sensorIDs:
            self.processor.sendHeartOn(i)
            time.sleep(0.01)

    def enableCal(self):
        self.calibrationOn = True

    def disableCal(self):
        self.calibrationOn = False
    '''
    Sends corresponding command using PyTactio based on message passed from ParseThread
    Separates PyTactio from QT code
    '''
    def sendMessageCallback(self, sendData):
        if(sendData[0] == PyTactio.SerialActions.LEDON):
            self.processor.sendLEDon(sendData[1])
        elif(sendData[0] == PyTactio.SerialActions.LEDOFF):
            self.processor.sendLEDoff(sendData[1])
        elif(sendData[0] == PyTactio.SerialActions.CAL_BIAS):
            self.processor.sendCalCmd(sendData[1])
        elif(sendData[0] == PyTactio.SerialActions.BIAS_EN):
            self.processor.sendBiasCalEn(sendData[1])
        elif(sendData[0] == PyTactio.SerialActions.BIAS_DIS):
            self.processor.sendBiasCalDis(sendData[1])
        elif(sendData[0] == PyTactio.SerialActions.HEART_ON):
            self.processor.sendHeartOn(sendData[1])
        elif(sendData[0] == PyTactio.SerialActions.HEART_OFF):
            self.processor.sendHeartOff(sendData[1])
    
    def sensorListCallback(self, sensorList):
        print(sensorList)

    def calModel(self, voltage, sensorID):
        if(self.calibrationOn):
            # Formula goes here
            input_voltage = 3300
            r2 = 390
            conductance = voltage/(r2*input_voltage  - r2 * voltage)
            model = self.model_params[self.model_ids.index(sensorID)]
            m = float(model.find('slope').text)
            b = float(model.find('offset').text)
            return m*conductance + b
        else:
            return voltage

    # Updates sensor data when callback is triggered
    def parseResultCallback(self, parseResult):
        sensorID = parseResult[0]
        voltage = parseResult[1]
        if(self.calibrationOn):
            self.sensorWidgets[self.sensorIDs.index(sensorID)].setData(1000*self.calModel(voltage, sensorID))
        else:
            self.sensorWidgets[self.sensorIDs.index(sensorID)].setData(self.calModel(voltage, sensorID))

    # Updates selected file for recording
    def fileSelCallback(self):
        save_name = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', options=QtGui.QFileDialog.DontUseNativeDialog)[0]
        self.fileLine.setText(save_name)

    #start/stop recording function
    #clear array on restart
    def record(self):
        self.is_recording = not self.is_recording # Keeps track of two states for button (red or gray)
        if self.is_recording:
            self.recording = {id : np.empty((1,4,4)) for id in self.sensorIDs} # resets dictionary holding previous recordings
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
            save_name = ""
            if(self.fileLine.text() == ''):
                # If the file name hasn't previously been inserted in the line edit box, prompt user
                save_name = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', options=QtGui.QFileDialog.DontUseNativeDialog)[0]
            else:
                # If the file name has been specified in the line edit box, use that
                save_name = self.fileLine.text()
            
            '''
            Since there's no serializable method for Numpy Arrays, we define a custom encoder to convert
            Numpy Arrays to a serial representation (nested python arrays)
            '''
            if save_name != '':
                with open(save_name, "w") as outfile:  
                    json.dump(self.recording, outfile, cls=NumpyArrayEncoder) 

    # Kicks off when QTimer has a timeout event
    def timerCallback(self): 
        if self.is_recording:
            for id in self.sensorIDs:
                self.recording[id] = np.append(self.recording[id], \
                    np.expand_dims(self.sensorWidgets[self.sensorIDs.index(id)].data,axis=0),axis=0)

    # Add Keyboard Shortcuts
    def keyPressEvent(self, event):
        if(event.key() == QtCore.Qt.Key_Escape): #Escape automatically closes
            self.close()

    # Sends a signal to wait for Parse Thread to end
    def killParserThread(self):
        self.worker.alive = False
        while self.threadpool.activeThreadCount() > 0:
            continue
    
    # intercepts all kill events to wait for threads to safely close
    def closeEvent(self, event):
        self.killParserThread()
        event.accept()



if (__name__ == "__main__"):
    app = QtWidgets.QApplication(sys.argv)
    window = MultiSensorVis()
    # window.show()
    sys.exit(app.exec_())
