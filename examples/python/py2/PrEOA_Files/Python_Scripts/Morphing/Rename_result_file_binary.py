###### This script renames the binary files output from the morphing step done with elastix
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

#Name file
infile = sys.argv[1]
basename = os.path.basename(infile)
name = basename.split("roi")[0]
end = "Morph_bin.mha"
end2 = "Morph_bin.png"
filename = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Morphed/result.mha"
filename2 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Morphed/" + name + end
filenameLpng = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Binary_morphed_PNG/" + name + end2
print filename2

#Rename file
os.rename(filename, filename2)

########## Read image and write out PNG
reader = vtk.vtkMetaImageReader()
reader.SetFileName(filename2)
reader.Update()
imageL = reader.GetOutput()

# calculate dimensions [x,y,z]
_extent = imageL.GetExtent()
ConstPixelDimsL = [_extent[1]-_extent[0]+1, _extent[3]-_extent[2]+1, _extent[5]-_extent[4]+1]

# vtkArray to Numpy array with reshape [x,y,z]
np_imageL = vtk_to_numpy(imageL.GetPointData().GetArray(0))
np_imageL = np_imageL.reshape(ConstPixelDimsL,order='F')

# Create the difference map
max_imageL = np_imageL.max(axis=2)
remove_zero = max_imageL[~np.all(max_imageL == 0, axis=1)]
transposed_image = np.transpose(remove_zero)
final_imageL = transposed_image[~np.all(transposed_image == 0, axis=1)]
final_imageL = np.absolute(final_imageL)

#Write out png of binary image
plot = plt.figure()
plt.gca().axes.get_xaxis().set_visible(False)
plt.imshow(final_imageL,cmap= "nipy_spectral", vmin=-0, vmax=1)
cbar = plt.colorbar()
plt.gca().axes.get_yaxis().set_visible(False)
plt.savefig(filenameLpng)
