import sys
import argparse
import vtk
import os
from vtk.util import numpy_support
from vtk.util.numpy_support import numpy_to_vtk, vtk_to_numpy
import numpy as np
import scipy.optimize as opt
import pylab as plt
import random as rand
from matplotlib.image import AxesImage
import scipy
from scipy import stats
from scipy import ndimage
import matplotlib.pyplot as plt
plt.ioff()

#Name all 2D thickness maps that have already been morphed
dirname_read1 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Morphed/PREOA_00"
dirname_read2 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Morphed/PREOA_0"
dirname_write = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Average_Maps/Bone/"
file1 = "FC_THICK_LAT_Morph_roi.mha"
file2 = "FC_THICK_MED_Morph_roi.mha"
file3 = "TC_THICK_LAT_Morph_roi.mha"
file4 = "TC_THICK_MED_Morph_roi.mha"
file5 = "F_THICK_LAT_Morph_roi.mha"
file6 = "F_THICK_MED_Morph_roi.mha"
file7 = "T_THICK_LAT_Morph_roi.mha"
file8 = "T_THICK_MED_Morph_roi.mha"
Bin1 = "_XCT_F_LAT_Morph_bin.mha"
Bin2 = "_XCT_F_MED_Morph_bin.mha"
Bin3 = "_XCT_T_LAT_Morph_bin.mha"
Bin4 = "_XCT_T_MED_Morph_bin.mha"
Bin5 = "_XCT_F_LAT_Morph_bin.mha"
Bin6 = "_XCT_F_MED_Morph_bin.mha"
Bin7 = "_XCT_T_LAT_Morph_bin.mha"
Bin8 = "_XCT_T_MED_Morph_bin.mha"
png1 = "FC_LAT_Morph"
png2 = "FC_MED_Morph"
png3 = "TC_LAT_Morph"
png4 = "TC_MED_Morph"
png5 = "F_LAT_Morph"
png6 = "F_MED_Morph"
png7 = "T_LAT_Morph"
png8 = "T_MED_Morph"

#Set scale for images to be output
sca1 = 3
sca2 = 3
sca3 = 4#4.5
sca4 = 4#3.0
sca5 = 0.9
sca6 = 0.9 #1.2
sca7 = 2.3 #1.6
sca8 = 2.3

start = 5 #First sample number to be analysed
end = 33 #Last sample number to be analysed

regions = 5 #first region to analyse
regions_end = 6 #last region to analyse

while regions <= regions_end:
    #Name output files
    png_num = globals()['png%s' % regions] #PNG name for average map
    bin_num = globals()['Bin%s' % regions] #Binary image of region
    scale_num = globals()['sca%s' % regions] #Value for colour bar range of image

    #Name of all maps
    filename_write_injured = dirname_write + "Average_Maps_" + png_num + "_Injured.png"
    filename_write_contralateral = dirname_write + "Average_Maps_" + png_num + "_Contralateral.png"
    filename_write_control = dirname_write + "Average_Maps_" + png_num + "_Control.png"
    filename_write_controlL = dirname_write + "Average_Maps_" + png_num + "_ControlL.png"
    filename_write_controlR = dirname_write + "Average_Maps_" + png_num + "_ControlR.png"
    filename_bin = dirname_read1 + "5" + "_L"+ bin_num

    while start <= end:
        if start < 10: #Name files for left knee
            file_num = globals()['file%s' % regions]
            bin_num = globals()['Bin%s' % regions]
            filenameL = dirname_read1 + str(start) + "_L_"+ file_num
        else:
            file_num = globals()['file%s' % regions]
            bin_num = globals()['Bin%s' % regions]
            filenameL = dirname_read2 + str(start) + "_L_"+ file_num
        print filenameL
        # Read in the image
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName(filenameL)
        reader.Update()
        imageL = reader.GetOutput()

        # calculate dimensions [x,y,z]
        _extent = imageL.GetExtent()
        ConstPixelDimsL = [_extent[1]-_extent[0]+1, _extent[3]-_extent[2]+1, _extent[5]-_extent[4]+1]

        # vtkArray to Numpy array with reshape [x,y,z]
        np_imageL = vtk_to_numpy(imageL.GetPointData().GetArray(0))
        np_imageL = np_imageL.reshape(ConstPixelDimsL,order='F')
        max_imageL = np_imageL.max(axis=2)
        transposed_imageL = np.transpose(max_imageL)
        x_dim = transposed_imageL.shape[0]
        y_dim = transposed_imageL.shape[1]
        for x in range (0, (x_dim)):
            for y in range (0, (y_dim)):
                if transposed_imageL[[x], [y]] <0:
                    transposed_imageL[[x], [y]] = 0
                if transposed_imageL[[x], [y]] <0:
                    transposed_imageL[[x], [y]] = 0
        globals()['final_imageL%s' % start] = transposed_imageL

        #Repeat for Right knee
        if start < 10:
            file_num = globals()['file%s' % regions]
            bin_num = globals()['Bin%s' % regions]
            filenameR = dirname_read1 + str(start) + "_R_"+ file_num
        else:
            file_num = globals()['file%s' % regions]
            bin_num = globals()['Bin%s' % regions]
            filenameR = dirname_read2 + str(start) + "_R_"+ file_num

        # Read in the image
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName(filenameR)
        reader.Update()
        imageR = reader.GetOutput()

        # calculate dimensions [x,y,z]
        _extent = imageR.GetExtent()
        ConstPixelDimsR = [_extent[1]-_extent[0]+1, _extent[3]-_extent[2]+1, _extent[5]-_extent[4]+1]

        # vtkArray to Numpy array with reshape [x,y,z]
        np_imageR = vtk_to_numpy(imageR.GetPointData().GetArray(0))
        np_imageR = np_imageR.reshape(ConstPixelDimsR,order='F')
        max_imageR = np_imageR.max(axis=2)
        transposed_image = np.transpose(max_imageR)
        x_dim = transposed_image.shape[0]
        y_dim = transposed_image.shape[1]
        for x in range (0, (x_dim)):
            for y in range (0, (y_dim)):
                if transposed_image[[x], [y]] <0:
                    transposed_image[[x], [y]] = 0
                if transposed_image[[x], [y]] <0:
                    transposed_image[[x], [y]] = 0
        globals()['final_imageR%s' % start] = transposed_image

        #Repeat untill all images are read in for this roi
        start = start + 1

    #Get dimentions of regerence image (for PREOA this is number 5)
    x_dim = final_imageL5.shape[0]
    y_dim = final_imageL5.shape[1]

    #Calculate mean for all images by reading through each pixel
    injured_values = []
    control_values = []
    controlL_values = []
    controlR_values = []
    contralateral_values = []
    for y in range (0, (y_dim-1)):
        for x in range (0, (x_dim-1)):
            injured = np.array([
                final_imageR5[[x], [y]],
                final_imageR6[[x], [y]],
                final_imageL7[[x], [y]],
                final_imageR8[[x], [y]],
                final_imageR9[[x], [y]],
                final_imageL13[[x], [y]],
                final_imageL15[[x], [y]],
                final_imageL16[[x], [y]],
                final_imageL22[[x], [y]],
                final_imageL27[[x], [y]],
                final_imageL28[[x], [y]],
                final_imageR29[[x], [y]],
                final_imageL30[[x], [y]],
                final_imageL32[[x], [y]],
                final_imageL33[[x], [y]],
                ])
            contralateral = np.array([
                final_imageL5[[x], [y]],
                final_imageL6[[x], [y]],
                final_imageR7[[x], [y]],
                final_imageL8[[x], [y]],
                final_imageL9[[x], [y]],
                final_imageR13[[x], [y]],
                final_imageR15[[x], [y]],
                final_imageR16[[x], [y]],
                final_imageR22[[x], [y]],
                final_imageR27[[x], [y]],
                final_imageR28[[x], [y]],
                final_imageL29[[x], [y]],
                final_imageR30[[x], [y]],
                final_imageR32[[x], [y]],
                final_imageL33[[x], [y]]
                ])
            control = np.array([
                final_imageL10[[x], [y]],
                final_imageL11[[x], [y]],
                final_imageL12[[x], [y]],
                final_imageL14[[x], [y]],
                final_imageL17[[x], [y]],
                final_imageL18[[x], [y]],
                final_imageL19[[x], [y]],
                final_imageL20[[x], [y]],
                final_imageL21[[x], [y]],
                final_imageL23[[x], [y]],
                final_imageL24[[x], [y]],
                final_imageL25[[x], [y]],
                final_imageL31[[x], [y]],
                final_imageL26[[x], [y]],
                final_imageR10[[x], [y]],
                final_imageR11[[x], [y]],
                final_imageR12[[x], [y]],
                final_imageR14[[x], [y]],
                final_imageR17[[x], [y]],
                final_imageR18[[x], [y]],
                final_imageR19[[x], [y]],
                final_imageR20[[x], [y]],
                final_imageR21[[x], [y]],
                final_imageR23[[x], [y]],
                final_imageR24[[x], [y]],
                final_imageR25[[x], [y]],
                final_imageR31[[x], [y]],
                final_imageR26[[x], [y]]
                ])
            controlL = np.array([
                final_imageL10[[x], [y]],
                final_imageL11[[x], [y]],
                final_imageL12[[x], [y]],
                final_imageL14[[x], [y]],
                final_imageL17[[x], [y]],
                final_imageL18[[x], [y]],
                final_imageL19[[x], [y]],
                final_imageL20[[x], [y]],
                final_imageL21[[x], [y]],
                final_imageL23[[x], [y]],
                final_imageL24[[x], [y]],
                final_imageL25[[x], [y]],
                final_imageL31[[x], [y]],
                final_imageL26[[x], [y]]
                ])
            controlR = np.array([
                final_imageR10[[x], [y]],
                final_imageR11[[x], [y]],
                final_imageR12[[x], [y]],
                final_imageR14[[x], [y]],
                final_imageR17[[x], [y]],
                final_imageR18[[x], [y]],
                final_imageR19[[x], [y]],
                final_imageR20[[x], [y]],
                final_imageR21[[x], [y]],
                final_imageR23[[x], [y]],
                final_imageR24[[x], [y]],
                final_imageR25[[x], [y]],
                final_imageR31[[x], [y]],
                final_imageR26[[x], [y]]
                ])

            #Calculate mean for each group
            mean_value_control = np.mean(control)
            mean_value_controlL = np.mean(controlL)
            mean_value_controlR = np.mean(controlR)
            mean_value_injured = np.mean(injured)
            mean_value_contralateral = np.mean(contralateral)

            #Set values that are zero to one (it looked better... probably not needed since we set are cropping the image later)
            if mean_value_injured > 0:
                injured_val = mean_value_injured
            else:
                injured_val = 1
            injured_values.append(injured_val)

            if mean_value_contralateral > 0:
                contralateral_val = mean_value_contralateral
            else:
                contralateral_val = 1
            contralateral_values.append(contralateral_val)

            if mean_value_control > 0:
                control_val = mean_value_control
            else:
                control_val = 1
            control_values.append(control_val)

            if mean_value_controlL > 0:
                controlL_val = mean_value_controlL
            else:
                controlL_val = 1
            controlL_values.append(controlL_val)

            if mean_value_controlR > 0:
                controlR_val = mean_value_controlR
            else:
                controlR_val = 1
            controlR_values.append(controlR_val)

    #Read all data into numpy array
    injured_average_map = np.array(injured_values)
    injured_average = injured_average_map.reshape(((x_dim-1),(y_dim-1)),order='F')

    contralateral_average_map = np.array(contralateral_values)
    contralateral_average = contralateral_average_map.reshape(((x_dim-1),(y_dim-1)),order='F')

    control_average_map = np.array(control_values)
    control_average = control_average_map.reshape(((x_dim-1),(y_dim-1)),order='F')

    controlL_average_map = np.array(controlL_values)
    controlL_average = controlL_average_map.reshape(((x_dim-1),(y_dim-1)),order='F')

    controlR_average_map = np.array(controlR_values)
    controlR_average = controlR_average_map.reshape(((x_dim-1),(y_dim-1)),order='F')

    #Find image dimentions
    x_dim = final_imageL5.shape[0]
    y_dim = final_imageL5.shape[1]

    #Read in Mask#############################
    reader_bin = vtk.vtkMetaImageReader()
    reader_bin.SetFileName(filename_bin)
    reader_bin.Update()
    image_bin = reader_bin.GetOutput()

    # calculate dimensions [x,y,z]
    _extent = image_bin.GetExtent()
    ConstPixelDims = [_extent[1]-_extent[0]+1, _extent[3]-_extent[2]+1, _extent[5]-_extent[4]+1]

    # vtkArray to Numpy array with reshape [x,y,z]
    np_image_bin = vtk_to_numpy(image_bin.GetPointData().GetArray(0))
    np_image_bin = np_image_bin.reshape(ConstPixelDims,order='F')
    max_image_bin = np_image_bin.max(axis=2)
    transposed_image_bin = np.transpose(max_image_bin)

    #Calculate dimenstions of binary image
    x_dim = transposed_image_bin.shape[0]
    y_dim = transposed_image_bin.shape[1]

    #Create binary array (might not need to do this...)
    binary = []
    for x in range (0, (y_dim)):
        for y in range (0, (x_dim)):
            value = transposed_image_bin[[y], [x]]
            if value > 0:
                binary.append(1)
            if value == 0:
                binary.append(0)
            if value < 0:
                binary.append(1)
    bin_array = np.array(binary)
    bin_im = bin_array.reshape(((x_dim),(y_dim)),order='F')

    #erode binary image to create smaller mask
    eroded = ndimage.binary_erosion(bin_im, iterations = 2)

    #Set all values outside binary mask to zero (to cut out the outside of the image that has doesn't morph perfectly even)
    injured_average_crop = injured_average
    for x in range (0, (x_dim-1)):
        for y in range (0, (y_dim-1)):
            value = eroded[[x],[y]]
            if value > 0:
                injured_average_crop[x,y] = injured_average[[x],[y]]/1000
            if value == 0:
                injured_average_crop[x,y] = 0

    contralateral_average_crop = contralateral_average
    for x in range (0, (x_dim-1)):
        for y in range (0, (y_dim-1)):
            value = eroded[[x],[y]]
            if value > 0:
                contralateral_average_crop[x,y] = contralateral_average[[x],[y]]/1000
            if value == 0:
                contralateral_average_crop[x,y] = 0

    control_average_crop = control_average
    for x in range (0, (x_dim-1)):
        for y in range (0, (y_dim-1)):
            value = eroded[[x],[y]]
            if value > 0:
                control_average_crop[x,y] = control_average[[x],[y]]/1000
            if value == 0:
                control_average_crop[x,y] = 0

    controlL_average_crop = controlL_average
    for x in range (0, (x_dim-1)):
        for y in range (0, (y_dim-1)):
            value = eroded[[x],[y]]
            if value > 0:
                controlL_average_crop[x,y] = controlL_average[[x],[y]]/1000
            if value == 0:
                controlL_average_crop[x,y] = 0

    controlR_average_crop = controlR_average
    for x in range (0, (x_dim-1)):
        for y in range (0, (y_dim-1)):
            value = eroded[[x],[y]]
            if value > 0:
                controlR_average_crop[x,y] = controlR_average[[x],[y]]/1000
            if value == 0:
                controlR_average_crop[x,y] = 0

    #Write out images for each group
    plot = plt.figure()
    plt.imshow(injured_average_crop,cmap= "jet", vmin=0.5, vmax=scale_num)
    cbar = plt.colorbar()
    cbar.set_label('Thickness (mm)', rotation=270, labelpad = 20)
    plt.gca().axes.get_yaxis().set_visible(False)
    plt.gca().axes.get_xaxis().set_visible(False)
    plt.savefig(filename_write_injured)
    #plt.show()

    plot = plt.figure()
    plt.imshow(contralateral_average_crop,cmap= "jet", vmin=0.5, vmax=scale_num)
    cbar = plt.colorbar()
    cbar.set_label('Thickness (mm)', rotation=270, labelpad = 20)
    plt.gca().axes.get_yaxis().set_visible(False)
    plt.gca().axes.get_xaxis().set_visible(False)
    plt.savefig(filename_write_contralateral)
    #plt.show()

    plot = plt.figure()
    plt.imshow(control_average_crop,cmap= "jet", vmin=0.5, vmax=scale_num)
    cbar = plt.colorbar()
    cbar.set_label('Thickness (mm)', rotation=270, labelpad = 20)
    plt.gca().axes.get_yaxis().set_visible(False)
    plt.gca().axes.get_xaxis().set_visible(False)
    plt.savefig(filename_write_control)
    #plt.show()

    plot = plt.figure()
    plt.imshow(controlL_average_crop,cmap= "jet", vmin=0.5, vmax=scale_num)
    cbar = plt.colorbar()
    cbar.set_label('Thickness (mm)', rotation=270, labelpad = 20)
    plt.gca().axes.get_yaxis().set_visible(False)
    plt.gca().axes.get_xaxis().set_visible(False)
    plt.savefig(filename_write_controlL)
    #plt.show()

    plot = plt.figure()
    plt.imshow(controlR_average_crop,cmap= "jet", vmin=0.5, vmax=scale_num)
    cbar = plt.colorbar()
    cbar.set_label('Thickness (mm)', rotation=270, labelpad = 20)
    plt.gca().axes.get_yaxis().set_visible(False)
    plt.gca().axes.get_xaxis().set_visible(False)
    plt.savefig(filename_write_controlR)
    #plt.show()

    regions = regions + 1
    start = 5
