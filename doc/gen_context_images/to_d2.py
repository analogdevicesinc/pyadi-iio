# Convert XML to D2 diagram with jinja2
import os
import shutil
import sys
import xml.etree.ElementTree as ET
from jinja2 import Environment, FileSystemLoader
import xmltodict

xml_file = "fmcomms2-3.xml"

# # Load the XML file
# tree = ET.parse(xml_file)
# root = tree.getroot()

# # Create a dictionary to store the data
# data = {}


with open(xml_file, "r") as f:
    xml = f.read()
    data = xmltodict.parse(xml)

from pprint import pprint

pprint(data)

# Write to jinja2 template
loc = os.path.dirname(__file__)
loc = os.path.join(loc, "templates")
file_loader = FileSystemLoader(loc)
env = Environment(loader=file_loader)

loc = os.path.join("d2.tmpl")
template = env.get_template(loc)

output = template.render(devices=data['context']['device'])

output_filename = "diagram.d2"
with open(output_filename, "w") as f:
    f.write(output)