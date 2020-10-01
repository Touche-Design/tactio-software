import serial
import numpy as np
import time

def parseSerial():
    if(not input_ser.isOpen()): # Skip and return zeros if there is nothing plugged in
        return np.zeros((4,4))
    count = 0 # Indicates row
    temp_array = np.zeros((4,4))
    started = False
    inStr = input_ser.readline()
    #print(inStr)
    inputs = inStr.decode('utf-8', errors='strict').split(";")
    if(inputs[0][0] == '$'):
        started = True
        print("Started")
        #print(inputs)
    if(len(inputs) > 1 and started):
        if(inputs[0][0] == '$'):
            id = inputs[0]
            for x in inputs[1:]:
                row_split = x.split(",")
                if(row_split[0].find("$") == -1 and len(row_split) > 1):
                    row_int = [int(row_split[i]) for i in range(len(row_split))]
                    if(np.shape(row_int)[0] == 4):
                        temp_array[count,:] = row_int
                        count += 1
            if(count > 3):
                print(temp_array)
                return temp_array
    else:
        return np.zeros((4,4))


input_ser = serial.Serial('/dev/ttyACM0') #Serial port for STM32
input_ser.baudrate = 115200
while True:
    parseSerial()
    #time.sleep(0.1)
