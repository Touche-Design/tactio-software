import numpy as np
from enum import Enum

class SerialActions(Enum):
    LEDON = 0
    LEDOFF = 1
    CALIBRATE = 2

class SerialProcessor:
    def __init__(self, port):
        self.input_ser = port

    def parseSerial(self): # Parses the input from serial port and converts to array
        if not self.input_ser.inWaiting():
            return (), -2
        else:
            if(not self.input_ser.isOpen()): # Skip and return zeros if there is nothing plugged in
                return (), -1
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
                    return addrs, 1
                # 0b0100 corresponds to column data
                elif(byte&0xF0 == 0b01000000):
                    valid = byte&0x0F
                    addr = int.from_bytes(self.input_ser.read(), byteorder='big')
                    data = np.zeros((4,4))
                    # For each column
                    for i in range(4):
                        # For each row
                        for j in range(4):
                            data[j,i] = int.from_bytes(self.input_ser.read() + self.input_ser.read(), byteorder='big')
                    return (addr, data), 0
                else:
                    # In case neither applies here
                    return (byte), -1
