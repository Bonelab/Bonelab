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

#####################Read Points##################
mask_post = np.loadtxt("/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Subregions/posterior_mask_tib_lat.txt")
mask_ant = np.loadtxt("/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Subregions/anterior_mask_tib_lat.txt")


dirname_original1 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Morphed/PREOA_00"
dirname_original2 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Morphed/PREOA_0"
filename_write = ("/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Subregions/lateral_tibia.txt")

sample_number = 5
end = 33
roi_number = 1
i = 0
while (sample_number <= end):
    print "test"
    i = 0
    while (sample_number <= end):
        if sample_number < 10:
            filename_original_bone = dirname_original1 + str(sample_number) + "_R_T_THICK_LAT_Morph_roi.mha"
            filename_original_cart = dirname_original1 + str(sample_number) + "_R_TC_THICK_LAT_Morph_roi.mha"
        else:
            filename_original_bone = dirname_original2 + str(sample_number) + "_R_T_THICK_LAT_Morph_roi.mha"
            filename_original_cart = dirname_original2 + str(sample_number) + "_R_TC_THICK_LAT_Morph_roi.mha"
        print filename_original_bone

        ########### Read Bone Image ##########
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName(filename_original_bone)
        reader.Update()

        image = reader.GetOutput()
        # calculate dimensions [x,y,z]
        _extent = image.GetExtent()
        ConstPixelDims = [_extent[1]-_extent[0]+1, _extent[3]-_extent[2]+1, _extent[5]-_extent[4]+1]

        # vtkArray to Numpy array with reshape [x,y,z]
        np_image = vtk_to_numpy(image.GetPointData().GetArray(0))
        np_image = np_image.reshape(ConstPixelDims,order='F')
        max_image = np_image.max(axis=2)
        final_image_bone = np.transpose(max_image)

        ########### Read Cartilage Image ##########
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName(filename_original_cart)
        reader.Update()

        image = reader.GetOutput()
        # calculate dimensions [x,y,z]
        _extent = image.GetExtent()
        ConstPixelDims = [_extent[1]-_extent[0]+1, _extent[3]-_extent[2]+1, _extent[5]-_extent[4]+1]

        # vtkArray to Numpy array with reshape [x,y,z]
        np_image = vtk_to_numpy(image.GetPointData().GetArray(0))
        np_image = np_image.reshape(ConstPixelDims,order='F')
        max_image = np_image.max(axis=2)
        final_image_cart = np.transpose(max_image)

        ############ Get dimentions ####
        x_dim = final_image_bone.shape[0]
        y_dim = final_image_bone.shape[1]

        ######## find mean anterior ######
        ant_mean_bone = []
        ant_mean_cart = []
        for x in range (0, (x_dim)):
            for y in range (0, (y_dim)):
                value = mask_ant[[x], [y]]
                if final_image_bone[[x], [y]] <0:
                    final_image_bone[[x], [y]] = 0
                if final_image_cart[[x], [y]] <0:
                    final_image_cart[[x], [y]] = 0
                if value !=0:
                    ant_mean_bone.append(final_image_bone[[x], [y]])
                    ant_mean_cart.append(final_image_cart[[x], [y]])
        mean_ant_bone = np.mean(ant_mean_bone)/1000 #Divide because we multiplied thickness values by 1000 before morphing
        mean_ant_cart = np.mean(ant_mean_cart)/1000

        ######## find mean posterior ######
        post_mean_bone = []
        post_mean_cart = []
        for x in range (0, (x_dim)):
            for y in range (0, (y_dim)):
                value = mask_post[[x], [y]]
                if final_image_bone[[x], [y]] <0:
                    final_image_bone[[x], [y]] = 0
                if final_image_cart[[x], [y]] <0:
                    final_image_cart[[x], [y]] = 0
                if value !=0:
                    post_mean_bone.append(final_image_bone[[x], [y]])
                    post_mean_cart.append(final_image_cart[[x], [y]])
        mean_post_bone = np.mean(post_mean_bone)/1000
        mean_post_cart = np.mean(post_mean_cart)/1000

        f = open(filename_write,'a')
        f.write ("%s %s %s %s %s \n" %(sample_number, mean_post_bone, mean_ant_bone, mean_post_cart, mean_ant_cart))
        f.close()

        lat_image_bone = final_image_bone * mask_post
        plot = plt.figure()
        #plt.imshow(mask_post,cmap= "nipy_spectral", vmin=0, vmax=3)
        #cbar = plt.colorbar()
        #plt.show()
        sample_number = sample_number+1
