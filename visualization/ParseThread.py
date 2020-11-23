from PyQt5 import QtWidgets, QtCore, Qt, QtGui
import numpy as np
import serial
import traceback
import sys
from PyTactio import SerialProcessor, SerialStatus

'''
Defines the signals available from a running worker thread.

Supported signals are:

finished - No data

error - `tuple` (exctype, value, traceback.format_exc() )

gridData - tuple of numpy grid and sensor ID

sensorList - list of all available sensors

'''
class WorkerSignals(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(tuple)
    gridData = QtCore.pyqtSignal(tuple)
    sensorList = QtCore.pyqtSignal(list)


'''
Parser thread

Inherits from QRunnable to handler worker thread setup, signals and wrap-up.
Calls the parsing function from PyTactio and uses the result to trigger
callbacks in the main thread
'''
class Parser(QtCore.QRunnable):

    def __init__(self, inputProcessor):
        super(Parser, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.signals = WorkerSignals()
        self.alive = True
        self.parser = inputProcessor

    @QtCore.pyqtSlot()
    def run(self):
        while self.alive: # This is set to false by the main window, which causes this thread to close safely
            try:
                result, msg = self.parser.parseSerial() # Runs the parser method
            except:
                traceback.print_exc() # Emits a failure signal
                exctype, value = sys.exc_info()[:2]
            else:
                if(msg == SerialStatus.DATA) : # Emits the grid data signal
                    self.signals.gridData.emit(result)
                elif(msg == SerialStatus.NET_ADDRS): # Emits the list of addresses signal
                    self.signals.sensorList.emit(result)
