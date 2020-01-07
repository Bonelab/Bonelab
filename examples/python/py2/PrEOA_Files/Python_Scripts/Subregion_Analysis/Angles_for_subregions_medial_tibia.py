# This script uses the centroid from each medial and lateral compartment and draws a line between them
# The regions above this line and below this line are the posterior and anterior subregions
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

angle_increment = 180 #enter in degrees, this is the angle from the line between the centre of mass which divides the subregions if more than one subregions was needed
angle_from_shift = 0
filename = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Scaled/PREOA_005_L_XCT_T_MED_roi.mha"
points_file_lat = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/points/PREOA_005_L_XCT_T_Lat.txt"
points_file_med = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/points/PREOA_005_L_XCT_T_Med.txt"

#####################Read Points##################
# These points are the points selected in the creation of the ROI step in blSurfaceViewer
#Lateral compartment centroid:
points_lat = np.loadtxt(points_file_lat)
x_points_lat = points_lat[:,0]
y_points_lat = points_lat[:,1]
length_lat = len(x_points_lat)
centroid_x_lat = sum(x_points_lat)/length_lat
centroid_y_lat = sum(y_points_lat)/length_lat
print centroid_x_lat
print centroid_y_lat

#Medial compartment centroid
points_med = np.loadtxt(points_file_med)
x_points_med = points_med[:,0]
y_points_med = points_med[:,1]
length_med = len(x_points_med)
centroid_x_med = sum(x_points_med)/length_med
centroid_y_med = sum(y_points_med)/length_med
print centroid_x_med
print centroid_y_med

#Determine angle between the centroid of the medial and lateral compartments
shift_relative = np.arctan(abs(centroid_y_lat-centroid_y_med)/abs(centroid_x_lat-centroid_x_med))

#Determine if the lateral centroid or medial centroid is higher up in the y direction and determine if the angle needs to be added or subtracted
if centroid_y_lat < centroid_y_med:
    shift = shift_relative + math.pi/2
    shift_degree = shift*360/(math.pi*2)
    print shift_degree

if centroid_y_lat > centroid_y_med:
    shift = math.pi/2 - shift_relative
    shift_degree = shift*360/(math.pi*2)
    print shift_degree

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

#Find centroid of ROI and determine how many points are needed to define the regions (2 points to make a line to divide the regions)
com = scipy.ndimage.measurements.center_of_mass(final_image)
c_y = com[1]
c_x = com[0]
npoints = 360/angle_increment
start_angle = (shift + angle_from_shift*math.pi*2/360)
print "start_angle"
print start_angle
angle = start_angle #Angle relative to centre of mass along which a line will divide the regions
angle_inc = angle_increment*math.pi*2/360
points_x = []
points_y = []

#Find points and angles to define region
for i in range(npoints):
        r = 0
        x = c_x
        y = c_y
        value = final_image[[x], [y]]
        while (value !=0) and (x < (x_dim-1)) and (y < (y_dim-1)) and (x >=0) and (y >=0):
                x = c_x - r*math.cos(angle)
                y = c_y + r*math.sin(angle)
                value = final_image[[x], [y]]
                r = r + 1
        y_final = c_y + (r-2)*math.sin(angle)
        x_final = c_x - (r-2)*math.cos(angle)
        points_x.append(x_final)
        points_y.append(y_final)
        print angle
        angle = angle + angle_inc

        array_x = np.array(points_x)
        array_y = np.array(points_y)
        combined = np.vstack((array_x, array_y)).T
print array_x
print array_y
plot = plt.figure()
plt.imshow(final_image,cmap= "nipy_spectral", vmin=-0, vmax=3)
plt.scatter(x=array_y, y=array_x, c='r', s=40)
plt.scatter(x=c_y, y=c_x, c='b', s=40)
#plt.savefig("/Users/jbhatla/Documents/UofC/PrEOA/Analysis/test.png")
plt.show()

############Create Mask ##########
# Create first line
m1 = (points_y[0] - points_y[1])/(points_x[0] - points_x[1])
b1 = (float(points_y[0]) - m1*float(points_x[0]))

# Note this section specifically creates the PrE-OA regions, it is not set up to work with different inputs

for x in range (0, (x_dim)):
    for y in range (0, (y_dim)):
        value = final_image[[x], [y]]
        if value ==1 and y > (m1*x + b1): #>> for medial << for lateral >< for posterior <> for anterior
            posterior_mask[[x], [y]] = 1
        else:
            posterior_mask[[x], [y]] = 0
#Write out mask
np.savetxt("/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Subregions/posterior_mask_tib_med.txt", posterior_mask)

plot = plt.figure()
plt.imshow(posterior_mask,cmap= "nipy_spectral", vmin=-0, vmax=3)
cbar = plt.colorbar()
plt.show()
