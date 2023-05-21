import javabridge
import bioformats
import numpy as np
import matplotlib.pyplot as plt
from xml.dom.minidom import parse
import xml.dom.minidom
import win32clipboard as clipboard
from tkinter import filedialog
import cv2
import pandas as pd
import tkinter as tk
import tkinter.filedialog as fd
import os
from xml.dom.minidom import Node
from xml.etree import ElementTree as ET
from xml.dom import minidom

path = 'C:\\Users\\Modern\\Desktop\\Python\\LSM Test\\DS-777 2 405 lambda.lsm'

javabridge.start_vm(class_path=bioformats.JARS)

image, scale = bioformats.load_image(path, rescale=False, wants_max_intensity=True)
metadata_raw = bioformats.get_omexml_metadata(path)

javabridge.kill_vm()

DOMTree = xml.dom.minidom.parseString(metadata_raw)


# Get the Pixels element
pixels_element = DOMTree.getElementsByTagName("Pixels")[0]

# Get the value of PhysicalSizeX attribute
physical_size_x = pixels_element.getAttribute("PhysicalSizeX")
physical_size_y = pixels_element.getAttribute("PhysicalSizeY")

# Print the value of PhysicalSizeX
print(physical_size_x, physical_size_y)