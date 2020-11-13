from PyQt5 import QtWidgets, QtCore, Qt, QtGui
import numpy as np
import serial
import traceback
import sys
from SerialProcessor import SerialProcessor

class WorkerSignals(QtCore.QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data
    
    error
        `tuple` (exctype, value, traceback.format_exc() )
    
    result
        `object` data returned from processing, anything

    progress
        `int` indicating % progress 

    '''
    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(tuple)
    gridData = QtCore.pyqtSignal(tuple)
    sensorList = QtCore.pyqtSignal(list)


class Parser(QtCore.QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and 
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, port):
        super(Parser, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.input_ser = port
        self.signals = WorkerSignals()
        self.alive = True
        self.parser = SerialProcessor(self.input_ser)


    def printSerial(self):
        input = self.input_ser.readline()
        print(input)
        return (69, input)

    @QtCore.pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        while self.alive:
            try:
                result, msg = self.parser.parseSerial()
            except:
                traceback.print_exc()
                exctype, value = sys.exc_info()[:2]
            else:
                if(msg == 0) :
                    self.signals.gridData.emit(result)  # Return the result of the processing
                elif(msg == 1):
                    self.signals.sensorList.emit(result)
