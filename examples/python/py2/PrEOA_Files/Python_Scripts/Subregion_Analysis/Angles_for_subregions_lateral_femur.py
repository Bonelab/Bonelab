### This script creates subregions in the lateral femur for the PrE-OA Study.
# This script was adjusted manually to create the desired regions and is therefore not set up to run robustly
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

filename = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Scaled/PREOA_005_L_XCT_F_LAT_roi.mha"

##############################Read ROI ############
reader = vtk.vtkMetaImageReader()
reader.SetFileName(filename)
reader.Update()

image = reader.GetOutput()
# calculate dimensions [x,y,z]
_extent = image.GetExtent()
ConstPixelDims = [_extent[1]-_extent[0]+1, _extent[3]-_extent[2]+1, _extent[5]-_extent[4]+1]

# vtkArray to Numpy array with reshape [x,y,z]
np_image = vtk_to_numpy(image.GetPointData().GetArray(0))
np_image = np_image.reshape(ConstPixelDims,order='F')
max_image = np_image.max(axis=2)
final_image = np.transpose(max_image)
lateral_mask = np.transpose(max_image)
medial_mask = np.transpose(max_image)
anterior_mask = np.transpose(max_image)
posterior_mask = np.transpose(max_image)

x_dim = final_image.shape[0]
y_dim = final_image.shape[1]

#Determine length in the z direction of each ROI
length = x_dim/3

############Create Mask ##########
# Create masks based on where they are relative to the length.  This was done manually by adjusting this code for the PrE-OA Study

for x in range (0, (x_dim)):
    for y in range (0, (y_dim)):
        value = final_image[[x], [y]]
        if value ==1 and x < (length*2) and x < length: #>> for medial << for lateral >< for posterior <> for anterior
            posterior_mask[[x], [y]] = 1
        else:
            posterior_mask[[x], [y]] = 0
#Save chosen mask
np.savetxt("/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Subregions/posterior_mask_fem_lat.txt", posterior_mask)


plot = plt.figure()
plt.imshow(posterior_mask,cmap= "nipy_spectral", vmin=-0, vmax=3)
cbar = plt.colorbar()
plt.show()
