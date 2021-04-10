import numpy as np
from enum import Enum, auto

'''
Contains a set of enums representing possible actions over
the serial port. These can be used to pass messages between
PyTactio and other processes
'''
class SerialActions(Enum):
    LEDON = auto()
    LEDOFF = auto()
    CAL_BIAS = auto()
    BIAS_EN = auto()
    BIAS_DIS = auto()
    HEART_ON = auto()
    HEART_OFF = auto()

'''
Contains a set of error codes
'''
class SerialStatus(Enum):
    PORT_EMPTY = -2
    PORT_CLOSED = -1
    NET_ADDRS = 1
    DATA = 0
    ERROR = -1

'''
This class wraps a serial port. Function calls send the appropriate
codes over the serial port to the Tactio sensor chain
'''
class SerialProcessor:
    def __init__(self, port):
        self.input_ser = port
        # Internal variables hold the states of the calibrations
        self.biasCal = False
        self.slopeCal = False
        self.interCal = False

    '''
    Commands sensor at id to turn on the LED
    '''
    def sendLEDon(self, id):
        self.input_ser.write(int.to_bytes(0b10000011, 1, byteorder='big'))
        self.input_ser.write(int.to_bytes(id, 1, byteorder='big'))
        self.input_ser.flush()

    '''
    Commands sensor at id to turn off the LED
    '''
    def sendLEDoff(self, id):
        self.input_ser.write(int.to_bytes(0b10000010, 1, byteorder='big'))
        self.input_ser.write(int.to_bytes(id, 1, byteorder='big'))
        self.input_ser.flush()

    '''
    Commands sensor at id to calibrate itself
    '''
    def sendCalCmd(self, id):
        self.input_ser.write(int.to_bytes(0b10001000, 1, byteorder='big'))
        self.input_ser.write(int.to_bytes(id, 1, byteorder='big')) 
        self.input_ser.flush()

    '''
    Enables pre-stored bias calibration on sensor at id
    '''
    def sendBiasCalEn(self, id):
        self.biasCal = True
        self.input_ser.write(int.to_bytes(0b10001110, 1, byteorder='big'))
        self.input_ser.write(int.to_bytes(id, 1, byteorder='big')) 
        biasCalCmd = 0b00000000 | (self.biasCal << 2)  | (self.interCal << 1) | self.slopeCal
        self.input_ser.write(int.to_bytes(biasCalCmd, 1, byteorder='big'))
        self.input_ser.flush()

    '''
    Disables pre-stored bias calibration on sensor at id
    '''
    def sendBiasCalDis(self, id):
        self.biasCal = False
        self.input_ser.write(int.to_bytes(0b10001110, 1, byteorder='big'))
        self.input_ser.write(int.to_bytes(id, 1, byteorder='big')) 
        biasCalCmd = 0b00000000 | (self.biasCal << 2)  | (self.interCal << 1) | self.slopeCal
        self.input_ser.write(int.to_bytes(biasCalCmd, 1, byteorder='big'))
        self.input_ser.flush()
    
    '''
    Enables heartbeat indicator on sensor at id
    '''
    def sendHeartOn(self, id):
        self.input_ser.write(int.to_bytes(0b10010001, 1, byteorder='big'))
        self.input_ser.write(int.to_bytes(id, 1, byteorder='big')) 
        self.input_ser.flush()

    '''
    Disables heartbeat indicator on sensor at id
    '''
    def sendHeartOff(self, id):
        self.input_ser.write(int.to_bytes(0b10010000, 1, byteorder='big'))
        self.input_ser.write(int.to_bytes(id, 1, byteorder='big')) 
        self.input_ser.flush()

    '''
    Parses the input from serial port and returns as tuple of the format
    (DATA, STATUS)
    Data could be the addresses from the "get all addresses" message or the 
    sensor data sent by the Tactio chain
    '''
    def parseSerial(self): 
        if not self.input_ser.in_waiting > 0:
            return (), SerialStatus.PORT_EMPTY
        else:
            if(not self.input_ser.isOpen()): # Skip and return zeros if there is nothing plugged in
                return (), SerialStatus.PORT_CLOSED
            else:
                byte = None
                # Wait until 0xFF is read
                while(not byte == 255):
                    byte = int.from_bytes(self.input_ser.read(), byteorder='big')
                # Read in command byte
                byte = int.from_bytes(self.input_ser.read(), byteorder='big')
                # 0x50 corresponds to all known addresses
                if(byte == 0x50):
                    length = int.from_bytes(self.input_ser.read(), byteorder='big')
                    addrs = length * [None]
                    for i in range(length):
                        addrs[i] = int.from_bytes(self.input_ser.read(), byteorder='big')
                    return addrs, SerialStatus.NET_ADDRS
                # 0b0100 corresponds to column data
                elif(byte&0xF0 == 0b01000000):
                    valid = byte&0x0F
                    addr = int.from_bytes(self.input_ser.read(), byteorder='big')
                    quad = addr & 3
                    addr = (addr & 0b11111100) >> 2
                    data = np.zeros((4,4))
                    # For each column
                    for i in range(4):
                        # For each row
                        for j in range(4):
                            data[j,i] = int.from_bytes(self.input_ser.read() + self.input_ser.read(), byteorder='big') & 0xFFF
                    return (addr, quad, data), SerialStatus.DATA
                else:
                    # In case neither applies here
                    return (byte), SerialStatus.ERROR
