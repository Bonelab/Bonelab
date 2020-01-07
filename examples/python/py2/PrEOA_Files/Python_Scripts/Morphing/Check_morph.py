import sys
import argparse
import vtk
import vtkn88
import os
from vtk.util import numpy_support
from vtk.util.numpy_support import numpy_to_vtk, vtk_to_numpy
import numpy as np
import scipy.optimize as opt
import pylab as plt
import random as rand
from matplotlib.image import AxesImage
import scipy
from scipy import ndimage
import math

##########################################################################################################
#Binary morphed data and output png files
dirname1 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Morphed/PREOA_00"
dirname2 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Morphed/PREOA_0"
dirname_png1 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Check/PREOA_00"
dirname_png2 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Check/PREOA_0"
file1 = "_L_XCT_T_MED_Morph"
file2 = "_R_XCT_T_MED_Morph"
file3 = "_L_XCT_F_MED_Morph"
file4 = "_R_XCT_F_MED_Morph"
file5 = "_L_XCT_T_LAT_Morph"
file6 = "_R_XCT_T_LAT_Morph"
file7 = "_L_XCT_F_LAT_Morph"
file8 = "_R_XCT_F_LAT_Morph"
ending_image = "_bin.mha"
ending_png = "_bin.png"

#Binary images to compare against (the one we are morphig all the data to)
reference1 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Scaled/PREOA_005_L_XCT_T_MED_roi.mha"
reference2 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Scaled/PREOA_005_L_XCT_T_MED_roi.mha"
reference3 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Scaled/PREOA_005_L_XCT_F_MED_roi.mha"
reference4 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Scaled/PREOA_005_L_XCT_F_MED_roi.mha"
reference5 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Scaled/PREOA_005_L_XCT_T_LAT_roi.mha"
reference6 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Scaled/PREOA_005_L_XCT_T_LAT_roi.mha"
reference7 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Scaled/PREOA_005_L_XCT_F_LAT_roi.mha"
reference8 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Scaled/PREOA_005_L_XCT_F_LAT_roi.mha"

start = 5 #First sample to analyse
end = 32 #Last sample to anal
i = 0
while start <= end:
    i = 1
    while i <9:
        if start < 10:  #Name files with sample number below 10
            file_num = globals()['file%s' % i]
            reference = globals()['reference%s' % i]
            print reference
            filename = dirname1 + str(start) + file_num + ending_image
            png = dirname_png1 + str(start) + file_num + ending_png
            print filename
        else:  #Name files with sample number above 9
            file_num = globals()['file%s' % i]
            reference = globals()['reference%s' % i]
            print reference
            filename = dirname2 + str(start) + file_num + ending_image
            png = dirname_png2 + str(start) + file_num + ending_png
            print filename

        #Read morphed file
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName(filename)
        reader.Update()
        imageR = reader.GetOutput()

        # calculate dimensions [x,y,z]
        _extent = imageR.GetExtent()
        ConstPixelDimsR = [_extent[1]-_extent[0]+1, _extent[3]-_extent[2]+1, _extent[5]-_extent[4]+1]

        # vtkArray to Numpy array with reshape [x,y,z]
        np_imageR = vtk_to_numpy(imageR.GetPointData().GetArray(0))
        np_imageR = np_imageR.reshape(ConstPixelDimsR,order='F')
        max_imageR = np_imageR.max(axis=2)
        transposed_image_greyscale = np.transpose(max_imageR)
        transposed_image_greyscale = transposed_image_greyscale

        #Read binary file to compare morphed file to
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName(reference)
        reader.Update()
        imageR = reader.GetOutput()

        # calculate dimensions [x,y,z]
        _extent = imageR.GetExtent()
        ConstPixelDimsR = [_extent[1]-_extent[0]+1, _extent[3]-_extent[2]+1, _extent[5]-_extent[4]+1]

        # vtkArray to Numpy array with reshape [x,y,z]
        np_imageR = vtk_to_numpy(imageR.GetPointData().GetArray(0))
        np_imageR = np_imageR.reshape(ConstPixelDimsR,order='F')
        max_imageR = np_imageR.max(axis=2)
        transposed_image_reference = np.transpose(max_imageR)

        #Substract images to identify where differences are
        visual_check = transposed_image_reference - transposed_image_greyscale

        #Write out png file
        plt.imshow(visual_check,cmap= "nipy_spectral", vmin = 0, vmax = 1)#max_value_T_M)
        #cbar = plt.colorbar()
        plt.savefig(png)
        #plt.show()

        i = i+1
    start = start + 1
