import xml.etree.ElementTree as et
import os

'''
tree = et.parse('2sensor.xml')
root = tree.getroot()
'''

position_data = et.parse('2sensor.xml').getroot()
