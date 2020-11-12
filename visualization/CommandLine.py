import serial
import numpy as np
from SerialProcessor import SerialProcessor
import time

if __name__ == '__main__':
    spy = False
    with serial.serial_for_url('spy:///dev/cu.usbmodem1412' if spy else '/dev/cu.usbmodem1412') as ser:
        ser.baudrate = 9600
        processor = SerialProcessor(ser)
        time.sleep(2)
        ser.write(b'\x01') # Get all known node addresses
        while True:
            if ser.inWaiting():
                result, msg = processor.parseSerial()
                if msg == 1:
                    addrs_hex = ', '.join([f'0x{addr:02x}' for addr in result])
                    addrs_dec = ', '.join([f'{addr:3d}' for addr in result])
                    print(f'All known addresses: {addrs_hex} / {addrs_dec}')
                elif msg == 0:
                    addr, data = result
                    print(f'Data from {addr:3d}:')
                    if True:
                        for arr in data:
                            print('             ', end='')
                            for point in arr:
                                print(f'{int(point):4d} ', end='')
                            print('')
                else:
                    print(f'Unknown: {msg} | {result}')
