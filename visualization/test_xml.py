import xml.etree.ElementTree as et
import os

'''
tree = et.parse('2sensor.xml')
root = tree.getroot()
'''

position_data = et.parse('2sensor.xml').getroot()
'''
for child in position_data:
    print(child.attrib)
'''

print(int(position_data[0].find('id').text))