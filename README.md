# touche-software

This repo contains useful scripts for interacting with the Tactio sensor chain.

All code requires Python3 and has been tested with Python 3.6 and above. 

In order to visualize the sensor information, the [Tactio visualization software](https://github.com/Touche-Design/tactio-software) can be utilized. In order to use the visualization software, make sure to check a couple of things:
1. Screen layout of the sensor nodes need to be configured. Take a look at the `configs` folder to describe the desired geometery for the present node addresses in the system. Use one of the pre-existing configs or make your own, and make sure it is selected in the code. If necessary, modify the line 
```python
position_data = et.parse('configs/2sensor.xml').getroot()
``` 
2. Set your Network Controller to the necessary target under your Serial port devices. This needs to be performed while the network controller is plugged in. Here, you may need to modify the follwing line:
```python
self.input_ser = serial.Serial('COM8')
``` 
3. To see the visualization, run the following command in the visualization folder:
```bash
python3 MultiSensorVis.py
```
To incorporate Tactio into your own project, you can utilize the PyTactio library to handle the communications. The PyTactio class contains all necessary methods for reading data and sending commands to a Tactio chain, and only has a dependency on the PySerial library. This can be installed using the following command. 
```bash
pip3 install pyserial
```
