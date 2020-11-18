import serial
import numpy as np
from PyTactio import *
import time
import argparse

if __name__ == '__main__':
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--spy", "-s", help='Show serial port traffic. Incredibly verbose', action='store_true')
    argparser.add_argument("--verbose", "-v", help='Show all received node data', action='store_true')
    argparser.add_argument("--hide-data", help='Do not show that data was received at all', action='store_true')
    argparser.add_argument("port", help='The serial port device')
    args = argparser.parse_args()

    with serial.serial_for_url('spy://'+args.port if args.spy else args.port) as ser:
        ser.baudrate = 230400
        processor = SerialProcessor(ser)
        time.sleep(2)
        calibration = {'node17': (59592.555146471714, -2.594419402962785), 'node9': (61333.1489394592, -8.59053516372839), 'node20': (101231.12223841752, -9.283480517510938), 'node18': (52517.7314816211, 1.985340812003514), 'node8': (50939.09656321071, 11.257871296366801), 'node2': (65731.91265349595, 3.342035089777468), 'node15': (56893.89611828837, -1.62819078126779)}
        processor.sendCalibration(calibration)
        #ser.write(b'\x01') # Get all known node addresses
        #while True:
        #    result, msg = processor.parseSerial()
        #    if msg == SerialStatus.PORT_EMPTY:
        #        pass
        #    elif msg == SerialStatus.NET_ADDRS:
        #        result.sort()
        #        addrs_hex = ', '.join([f'0x{addr:02x}' for addr in result])
        #        addrs_dec = ', '.join([f'{addr:3d}' for addr in result])
        #        print(f'All known addresses ({len(result)} nodes): {addrs_hex} / {addrs_dec}')
        #    elif msg == SerialStatus.DATA:
        #        addr, data = result
        #        if not args.hide_data:
        #            print(f'Data from {addr:3d}:')
        #            if args.verbose:
        #                for arr in data:
        #                    print('             ', end='')
        #                    for point in arr:
        #                        print(f'{int(point):4d} ', end='')
        #                    print('')
        #    elif msg == SerialStatus.ERROR:
        #        print(f'Error: {msg} | {result}')
        #    elif msg == SerialStatus.PORT_CLOSED:
        #        print('Closed port')
        #        break
        #    else:
        #        print(f'Unknown: {msg} | {result}')
#