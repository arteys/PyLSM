#LSM2.py - script that can open .LSM files from Carl Zeiss LSM710 microscope obtained in lambda mode and convert them into pseudo-realistic colored images (with heli of napari).
# I make this thing mostly for self-education, so it may (must) contain realy stupid mistakes and just strange things


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


def wavelength_to_rgb(wavelength, gamma):

    '''This converts a given wavelength of light to an 
    approximate RGB color value. The wavelength must be given
    in nanometers in the range from 380 nm through 750 nm
    (789 THz through 400 THz).

    Based on code by Dan Bruton
    http://www.physics.sfasu.edu/astro/color/spectra.html
    '''

    wavelength = float(wavelength)
    if wavelength >= 380 and wavelength <= 440:
        attenuation = 0.3 + 0.7 * (wavelength - 380) / (440 - 380)
        R = ((-(wavelength - 440) / (440 - 380)) * attenuation) ** gamma
        G = 0.0
        B = (1.0 * attenuation) ** gamma
    elif wavelength >= 440 and wavelength <= 490:
        R = 0.0
        G = ((wavelength - 440) / (490 - 440)) ** gamma
        B = 1.0
    elif wavelength >= 490 and wavelength <= 510:
        R = 0.0
        G = 1.0
        B = (-(wavelength - 510) / (510 - 490)) ** gamma
    elif wavelength >= 510 and wavelength <= 580:
        R = ((wavelength - 510) / (580 - 510)) ** gamma
        G = 1.0
        B = 0.0
    elif wavelength >= 580 and wavelength <= 645:
        R = 1.0
        G = (-(wavelength - 645) / (645 - 580)) ** gamma
        B = 0.0
    elif wavelength >= 645 and wavelength <= 750:
        attenuation = 0.3 + 0.7 * (750 - wavelength) / (750 - 645)
        R = (1.0 * attenuation) ** gamma
        G = 0.0
        B = 0.0
    else:
        R = 0.0
        G = 0.0
        B = 0.0
    # R *= 255
    # G *= 255
    # B *= 255
    RGB = np.array([R,G,B])
    return RGB

def realtime_lambda_to_graph(x_coordinate, y_coordinate, Image_array, Channel_array, Save_or_not):

    #From single point to square with some side
    #For napari

    side = 10

    x_1 = x_coordinate - side
    x_2 = x_coordinate + side
    y_1 = y_coordinate - side
    y_2 = y_coordinate + side


    Type_conversion_constant = 10000

    Intensity_data = Image_array[x_1:x_2,y_1:y_2,:]

    Intensity_data_avereged = np.average(Intensity_data, axis = (0,1))*Type_conversion_constant


    Channel_array = np.array(Channel_array).astype(int)
    Intensity_data_avereged = Intensity_data_avereged.astype(int)
    

    Spectral_data = np.column_stack((Channel_array, Intensity_data_avereged))

    graphplot = plt.plot(Channel_array,Intensity_data_avereged)
    plt.pause(0.05) #If i want update the graph. But work strange yet
    plt.draw()
    


    if Save_or_not == 1:
        np.savetxt("Spectrum_point.csv", Spectral_data, fmt='%i', delimiter=",")
    else: 
        pass

def toClipboardForExcel(array):
    """
    Copies an array into a string format acceptable by Excel.
    Columns separated by \t, rows separated by \n
    """
    # Borrowed from https://stackoverflow.com/a/22488567. Works only in Windows.
    # Create string from array. 
    line_strings = []
    for line in array:
        line_strings.append("\t".join(line.astype(str)).replace("\n",""))
    array_string = "\r\n".join(line_strings)

    # Put string into clipboard (open, clear, set, close)
    clipboard.OpenClipboard()
    clipboard.EmptyClipboard()
    clipboard.SetClipboardText(array_string)
    clipboard.CloseClipboard()

def channels_to_lambda(image, channel_array):
    x,y,z = np.shape(image)
    single_image_size = [x,y]
    colored_image_array = np.zeros((z,x,y,3)).astype(int)


    for index, wavelength in enumerate(channel_array):
        
    
        rgb_value_channel = wavelength_to_rgb(wavelength,1) #Calculating color for this wavelength (wl)

        rgb_matrix_r = np.full((single_image_size),rgb_value_channel[0])  #Creating wl colored sqares for R,G,B
        rgb_matrix_g = np.full((single_image_size),rgb_value_channel[1])
        rgb_matrix_b = np.full((single_image_size),rgb_value_channel[2]) 

        
        # rgb_matrix_rgb = np.stack((rgb_matrix_r, rgb_matrix_g, rgb_matrix_b), axis = 2)*255
        # cv2.imwrite((str(wavelength) + '.png') , rgb_matrix_rgb.astype(int))

        # print(rgb_matrix_rgb[0,0], wavelength)

        image_i = image[:,:,index]
        
        rgb_colored_channel_r = np.multiply(rgb_matrix_r,image_i) #Multipling colored squares by gamma value
        rgb_colored_channel_g = np.multiply(rgb_matrix_g,image_i)
        rgb_colored_channel_b = np.multiply(rgb_matrix_b,image_i)

        colored_channel_i = np.stack((rgb_colored_channel_r, rgb_colored_channel_g, rgb_colored_channel_b), axis = 2).astype(int)
        colored_image_array[index,:,:,:] = colored_channel_i.astype(int)


        # channel_c = cv2.cvtColor(colored_channel_i, cv2.COLOR_RGB2BGR)
        # cv2.imwrite((str(wavelength) + '.png') , colored_channel_i.astype(int))



    image_average = np.average(colored_image_array, axis = 0).astype(int) #Averaging layers to construct lambda-colored image

    image_average_unit_8 = np.uint8(image_average)

    #OpenCV2 by default uses BGR 
    
    im_bgr = cv2.cvtColor(image_average_unit_8, cv2.COLOR_RGB2BGR)

    return im_bgr
    
def spectra_extraction(image_name, image, channel_array):
    type_conversion_constant = 10000 #When numbers a big we didnt lose much when convert it to int. And ints look much nicer in Excel

    intensity_data_full_avereged = (np.average(image, axis = (0,1))*type_conversion_constant).astype(int)

    channel_array = np.array(channel_array).astype(int) #From list to np array

    # wl_column_name = image_name + 'WL'

    d = {'Wavelength': channel_array, image_name: intensity_data_full_avereged}

    spectral_data_full = pd.DataFrame(data = d)

    return spectral_data_full

def automatic_brightness_and_contrast(image, clip_hist_percent=1):
    "From https://stackoverflow.com/a/56909036/3715678 Thank you nathancy"
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Calculate grayscale histogram
    hist = cv2.calcHist([gray],[0],None,[256],[0,256])
    hist_size = len(hist)
    
    # Calculate cumulative distribution from the histogram
    accumulator = []
    accumulator.append(float(hist[0]))
    for index in range(1, hist_size):
        accumulator.append(accumulator[index -1] + float(hist[index]))
    
    # Locate points to clip
    maximum = accumulator[-1]
    clip_hist_percent *= (maximum/100.0)
    clip_hist_percent /= 2.0
    
    # Locate left cut
    minimum_gray = 0
    while accumulator[minimum_gray] < clip_hist_percent:
        minimum_gray += 1
    
    # Locate right cut
    maximum_gray = hist_size -1
    while accumulator[maximum_gray] >= (maximum - clip_hist_percent):
        maximum_gray -= 1
    
    # Calculate alpha and beta values
    
    gray_dif = maximum_gray - minimum_gray 
    if gray_dif == 0: #Sometimes...
        gray_dif = 1


    alpha = 255 / (gray_dif)
    beta = -minimum_gray * alpha
    
    '''
    # Calculate new histogram with desired range and show histogram 
    new_hist = cv2.calcHist([gray],[0],None,[256],[minimum_gray,maximum_gray])
    plt.plot(hist)
    plt.plot(new_hist)
    plt.xlim([0,256])
    plt.show()
    '''

    auto_result = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
    return (auto_result, alpha, beta)

root = tk.Tk()
paths = fd.askopenfilenames(parent=root, title='Open images')

javabridge.start_vm(class_path=bioformats.JARS)

spectra = pd.DataFrame()

folder_path = os.path.dirname(paths[0])

# Check if folder /Image exists, if no - create one
if os.path.isdir(folder_path + '/Images'):
    print('Image folder already exists')
else:
    os.mkdir(folder_path + '/Images')

for path in paths:

    image_name_w_ext = os.path.basename(path)
    folder_path = os.path.dirname(path)
    image_name,extention = image_name_w_ext.split(".") 

    image, scale = bioformats.load_image(path, rescale=False, wants_max_intensity=True)
    metadata_raw = bioformats.get_omexml_metadata(path)

    # Open LSM, extract images, their sizes and quantitiy and OME-XML metadata

    channel_array = []
    DOMTree = xml.dom.minidom.parseString(metadata_raw)
    collection = DOMTree.documentElement

    channels = collection.getElementsByTagName("Channel")

    for channel in channels:
        if channel.hasAttribute("Name"):
            channel_name = channel.getAttribute("Name")
            channel_array.append(channel_name)

    image_average_unit_8 = channels_to_lambda(image,channel_array)
    spectrum_c = spectra_extraction(image_name, image, channel_array)

    frames = [spectra, spectrum_c]
    spectra = pd.concat(frames, axis=1)

    #Autocorrecting brightness and contrast
    auto_result, alpha, beta = automatic_brightness_and_contrast(image_average_unit_8)
    # cv2.imshow('image',auto_result)
    # cv2.waitKey(0)

    output_image_file_name_orig = folder_path + '/Images/' + str(image_name) + '_orig' + '.png'
    output_image_file_name_corr = folder_path + '/Images/' + str(image_name) + '_corr' + '.png'

    cv2.imwrite(output_image_file_name_orig, image_average_unit_8)
    cv2.imwrite(output_image_file_name_corr, auto_result)

output_spectra_file_name = folder_path + '/Images/' + 'spectra' + '.xlsx'

spectra.to_excel(output_spectra_file_name, index=False)  

javabridge.kill_vm()
