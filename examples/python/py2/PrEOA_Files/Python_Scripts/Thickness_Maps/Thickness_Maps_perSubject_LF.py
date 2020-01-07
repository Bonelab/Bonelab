import sys
import argparse
import vtk
import vtkn88
import os
from vtk.util import numpy_support
from vtk.util.numpy_support import numpy_to_vtk, vtk_to_numpy
import numpy as np
import matplotlib.pyplot as plt

#Name files
infile = sys.argv[1]
basename = os.path.basename(infile)
name = basename.split("_R_")[0]
dirname_read = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Original/"
dirname_write = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/PNG_Original/"
end = "_L_F"
end2 = ".png"
filename = dirname_write + name + end +end2
T_M = dirname_read + name + "_L_F_THICK_MED_REG.AIM"
T_L = dirname_read + name + "_L_F_THICK_LAT_REG.AIM"
TC_M = dirname_read + name + "_L_FC_THICK_MED_REG.AIM"
TC_L = dirname_read + name + "_L_FC_THICK_LAT_REG.AIM"


lut = vtk.vtkLookupTable()
lut.SetNumberOfColors(5)
lut.SetHueRange(0.0,0.667)
lut.Build()


######## Read in the bone image data
aim_T_M = vtkn88.vtkn88AIMReader()
aim_T_M.SetFileName( T_M )
aim_T_M.DataOnCellsOff()
aim_T_M.Update()

aim_T_L = vtkn88.vtkn88AIMReader()
aim_T_L.SetFileName( T_L )
aim_T_L.DataOnCellsOff()
aim_T_L.Update()

aim_TC_M = vtkn88.vtkn88AIMReader()
aim_TC_M.SetFileName( TC_M  )
aim_TC_M.DataOnCellsOff()
aim_TC_M.Update()

aim_TC_L = vtkn88.vtkn88AIMReader()
aim_TC_L.SetFileName( TC_L )
aim_TC_L.DataOnCellsOff()
aim_TC_L.Update()


image_T_M = aim_T_M.GetOutput()
image_T_L = aim_T_L.GetOutput()
image_TC_M = aim_TC_M.GetOutput()
image_TC_L = aim_TC_L.GetOutput()

# calculate dimensions [x,y,z]
_extent_TM = image_T_M.GetExtent()
ConstPixelDims_TM = [_extent_TM[1]-_extent_TM[0]+1, _extent_TM[3]-_extent_TM[2]+1, _extent_TM[5]-_extent_TM[4]+1]

_extent_TL = image_T_L.GetExtent()
ConstPixelDims_TL = [_extent_TL[1]-_extent_TL[0]+1, _extent_TL[3]-_extent_TL[2]+1, _extent_TL[5]-_extent_TL[4]+1]

_extent_TCM = image_TC_M.GetExtent()
ConstPixelDims_TCM = [_extent_TCM[1]-_extent_TCM[0]+1, _extent_TCM[3]-_extent_TCM[2]+1, _extent_TCM[5]-_extent_TCM[4]+1]

_extent_TCL = image_TC_L.GetExtent()
ConstPixelDims_TCL = [_extent_TCL[1]-_extent_TCL[0]+1, _extent_TCL[3]-_extent_TCL[2]+1, _extent_TCL[5]-_extent_TCL[4]+1]

# vtkArray to Numpy array with reshape [x,y,z]
np_image_T_M = vtk_to_numpy(image_T_M.GetPointData().GetArray(0))
np_image_T_M = np_image_T_M.reshape(ConstPixelDims_TM,order='F')

np_image_T_L = vtk_to_numpy(image_T_L.GetPointData().GetArray(0))
np_image_T_L = np_image_T_L.reshape(ConstPixelDims_TL,order='F')

np_image_TC_M = vtk_to_numpy(image_TC_M.GetPointData().GetArray(0))
np_image_TC_M = np_image_TC_M.reshape(ConstPixelDims_TCM,order='F')

np_image_TC_L = vtk_to_numpy(image_TC_L.GetPointData().GetArray(0))
np_image_TC_L = np_image_TC_L.reshape(ConstPixelDims_TCL,order='F')
# display a single slice (z=95) of the numpy array

plt.ioff()

# create the max image along the z-axis
max_image_T_M = np_image_T_M.max(axis=2)/5.491488103
max_image_T_L = np_image_T_L.max(axis=2)/5.491488103
max_image_TC_M = np_image_TC_M.max(axis=2)/5.491488103
max_image_TC_L = np_image_TC_L.max(axis=2)/5.491488103
max_value_T_M = np.amax(max_image_T_M)
max_value_T_L = np.amax(max_image_T_L)
max_value_TC_M = np.amax(max_image_TC_M)
max_value_TC_L = np.amax(max_image_TC_L)

# Create the thickness maps in the right shape (transpost and remove zeros so they look ok)
#remove_zero_T_M = max_image_T_M[~np.all(max_image_T_M == 0, axis=1)]
transposed_T_M = np.transpose(max_image_T_M)
#small_T_M = transposed_T_M[~np.all(transposed_T_M == 0, axis=1)]

#remove_zero_T_L = max_image_T_L[~np.all(max_image_T_L == 0, axis=1)]
transposed_T_L = np.transpose(max_image_T_L)
#small_T_L = transposed_T_L[~np.all(transposed_T_L == 0, axis=1)]

#remove_zero_TC_M = max_image_TC_M[~np.all(max_image_TC_M == 0, axis=1)]
transposed_TC_M = np.transpose(max_image_TC_M)
#small_TC_M = transposed_TC_M[~np.all(transposed_TC_M == 0, axis=1)]

#remove_zero_TC_L = max_image_TC_L[~np.all(max_image_TC_L == 0, axis=1)]
transposed_TC_L = np.transpose(max_image_TC_L)
#small_TC_L = transposed_TC_L[~np.all(transposed_TC_L == 0, axis=1)]

#Create Imagewith bone and cartilage medial and lateral
plot = plt.figure()
plot.add_subplot(2,2,2)
plt.imshow(transposed_T_L,cmap= "jet", vmin=-0, vmax=3)#max_value_T_L)
cbar = plt.colorbar()
cbar.set_label('Thickness (mm)', rotation=270, labelpad = 20)
plt.title('Bone Lateral')
#plt.gca().invert_xaxis()
plt.gca().axes.get_xaxis().set_visible(False)
plt.gca().axes.get_yaxis().set_visible(False)

#cart = plt.figure()
plot.add_subplot(2,2,4)
plt.imshow(transposed_TC_L,cmap= "jet", vmin=-0, vmax=6)#max_value_TC_L)
cbar = plt.colorbar()
cbar.set_label('Thickness (mm)', rotation=270, labelpad = 20)
plt.title('Cartilage Lateral')
##.gca().invert_xaxis()
plt.gca().axes.get_xaxis().set_visible(False)
plt.gca().axes.get_yaxis().set_visible(False)

plot.add_subplot(2,2,3)
plt.imshow(transposed_TC_M,cmap= "jet", vmin=-0, vmax=6)#max_value_TC_M)
cbar = plt.colorbar()
cbar.set_label('Thickness (mm)', rotation=270, labelpad = 20)
plt.title('Cartilage Medial')
#plt.gca().invert_xaxis()
plt.gca().axes.get_xaxis().set_visible(False)
plt.gca().axes.get_yaxis().set_visible(False)

plot.add_subplot(2,2,1)
plt.imshow(transposed_T_M,cmap= "jet", vmin=-0, vmax=3,  aspect='equal')#max_value_T_M)
cbar = plt.colorbar()
cbar.set_label('Thickness (mm)', rotation=270, labelpad = 20)
plt.title('Bone Medial')
#plt.gca().invert_xaxis()
plt.gca().axes.get_xaxis().set_visible(False)
plt.gca().axes.get_yaxis().set_visible(False)
filename2 = name + end
plt.suptitle("Left Femur")
plot.savefig(filename, transparent=True, bbox_inches='tight')
#plt.figure()
#plt.imshow(difference,cmap= "seismic", vmin=0.5, vmax=3.6)
#plt.colorbar()
#plt.title('Difference Map (Cartilage - Bone)')


#b = np.zeros((270,149))
#rgbArray = np.zeros((270,149,3), 'uint8')
#rgbArray[..., 1] = small_cart*256
#rgbArray[..., 0] = small_bone*256
#rgbArray[..., 2] = (small_cart+small_bone)*256/2
#plt.figure()
#plt.imshow(rgbArray)
#plt.title('RGB Image green = cartilage, red = bone')
#plt.colorbar()
#plt.show()
