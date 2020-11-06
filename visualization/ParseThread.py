from PyQt5 import QtWidgets, QtCore, Qt, QtGui
import numpy as np
import serial
import traceback
import sys

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
    result = QtCore.pyqtSignal(tuple)
    progress = QtCore.pyqtSignal(int)


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


    def parseSerial(self): # Parses the input from serial port and converts to array
        if(not self.input_ser.isOpen()): # Skip and return zeros if there is nothing plugged in
            return (0,np.zeros((4,4)))
        count = 0 # Indicates row
        temp_array = np.zeros((4,4))
        started = False
        inStr = self.input_ser.readline()
        inputs = inStr.decode('utf-8').split(";")
        if(inputs[0][0] == '$'):
            started = True

        if(len(inputs) > 1 and started):
            id = int(inputs[0][1:])
            for x in inputs[1:]:
                row_split = x.split(",")
                if(row_split[0].find("$") == -1 and len(row_split) > 1):
                    row_int = [int(row_split[i]) for i in range(len(row_split))]
                    if(np.shape(row_int)[0] == 4):
                        temp_array[count,:] = row_int
                        count += 1
            if(count > 3):
                print(temp_array)
                #self.sensorWidgets[self.sensorIDs.index(id)].setData(temp_array)
                return (id, temp_array)
        else:
            return (0,np.zeros((4,4)))
    def printSerial(self):
        input = self.input_ser.readline()
        print(input)
        return (69, input)

    @QtCore.pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        print(self.input_ser.inWaiting())
        while self.alive:
            if(self.input_ser.inWaiting()):
                try:
                    result = self.parseSerial()
                except:
                    traceback.print_exc()
                    exctype, value = sys.exc_info()[:2]
                else:
                    self.signals.result.emit(result)  # Return the result of the processing