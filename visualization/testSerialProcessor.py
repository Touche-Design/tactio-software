from PyTactio import SerialProcessor, SerialStatus
import serial

port = serial.Serial('/dev/ttyACM0')
port.baudrate = 230400
sp = SerialProcessor(port)

while(True):
    (data, status) = sp.parseSerial()
    if(status == SerialStatus.DATA):
        print(data)