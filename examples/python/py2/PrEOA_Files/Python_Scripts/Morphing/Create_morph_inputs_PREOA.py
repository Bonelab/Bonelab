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

#Create Correct names
#Thickness Maps from IPL
dirname_original1 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Original/PREOA_00"
dirname_original2 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Original/PREOA_0"

#3D ROIs
dirname_roi1 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/ROIs/PREOA_00"
dirname_roi2 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/ROIs/PREOA_0"

#2D Maps Multiplied times 1000
dirname_scaled1 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Scaled/PREOA_00"
dirname_scaled2 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Scaled/PREOA_0"

#PNG Files for Visualization
dirname_png1 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_PNG/PREOA_00"
dirname_png2 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_PNG/PREOA_0"

#Naming for thickness maps
file_C1 = "_L_TC_THICK_MED"
file_C2 = "_R_TC_THICK_MED"
file_C3 = "_L_FC_THICK_MED"
file_C4 = "_R_FC_THICK_MED"
file_C5 = "_L_TC_THICK_LAT"
file_C6 = "_R_TC_THICK_LAT"
file_C7 = "_L_FC_THICK_LAT"
file_C8 = "_R_FC_THICK_LAT"
file_B1 = "_L_T_THICK_MED"
file_B2 = "_R_T_THICK_MED"
file_B3 = "_L_F_THICK_MED"
file_B4 = "_R_F_THICK_MED"
file_B5 = "_L_T_THICK_LAT"
file_B6 = "_R_T_THICK_LAT"
file_B7 = "_L_F_THICK_LAT"
file_B8 = "_R_F_THICK_LAT"

#Naming for ROIs
roi1 = "_L_XCT_T_MED"
roi2 = "_R_XCT_T_MED"
roi3 = "_L_XCT_F_MED"
roi4 = "_R_XCT_F_MED"
roi5 = "_L_XCT_T_LAT"
roi6 = "_R_XCT_T_LAT"
roi7 = "_L_XCT_F_LAT"
roi8 = "_R_XCT_F_LAT"


sample_number = 33 #First Sample Number
end = 33 #Last Sample number to be analysed
roi_number = 8 #Roi to be analysed at start
roi_end = 8 #Last ROI to analyse
npoints = 360  #Number of points to pick
angle = 0 #Starting angle
angle_inc = math.pi*2/npoints #Degree increment between points

while (sample_number <= end):
    while roi_number <= roi_end:
        if sample_number < 10:  #Naming all samples under 010
            file_num_bone = globals()['file_B%s' % roi_number]
            file_num_cart = globals()['file_C%s' % roi_number]
            filename_original_bone = dirname_original1 + str(sample_number) + file_num_bone + "_REG.aim"
            filename_original_cart = dirname_original1 + str(sample_number) + file_num_cart + "_REG.aim"
            filename_sca_bone = dirname_scaled1 + str(sample_number) + file_num_bone + "_sca.mha"
            filename_sca_cart = dirname_scaled1 + str(sample_number) + file_num_cart + "_sca.mha"
            roi_num = globals()['roi%s' % roi_number]
            filename_roi = dirname_roi1 + str(sample_number) + roi_num + "_R03.aim"
            filename_roi_out = dirname_scaled1 + str(sample_number) + roi_num + "_roi.mha"
            filename_points = dirname_scaled1 + str(sample_number) + file_num_bone + "_morph_pts.txt"
            print filename_original_bone

        else:  #Name all samples above 009
            file_num_bone = globals()['file_B%s' % roi_number]
            file_num_cart = globals()['file_C%s' % roi_number]
            filename_original_bone = dirname_original2 + str(sample_number) + file_num_bone + "_REG.aim"
            filename_original_cart = dirname_original2 + str(sample_number) + file_num_cart + "_REG.aim"
            filename_sca_bone = dirname_scaled2 + str(sample_number) + file_num_bone + "_sca.mha"
            filename_sca_cart = dirname_scaled2 + str(sample_number) + file_num_cart + "_sca.mha"
            roi_num = globals()['roi%s' % roi_number]
            filename_roi = dirname_roi2 + str(sample_number) + roi_num + "_R03.aim"
            filename_roi_out = dirname_scaled2 + str(sample_number) + roi_num + "_roi.mha"
            filename_points = dirname_scaled2 + str(sample_number) + file_num_bone + "_morph_pts.txt"
            print filename_original_bone


        ##########################################################################################################
        #### Create ROI Binary Image to Select Points
        if roi_number < 9:  #Only need to do this once for cartilage and bone (same ROI applies)
            #Read in 3D ROI
            aim = vtkn88.vtkn88AIMReader()
            aim.SetFileName(filename_roi)
            aim.DataOnCellsOff()
            aim.Update()
            image = aim.GetOutput()

            # calcuLATe dimensions [x,y,z]
            _extent = image.GetExtent()
            ConstPixelDims = [_extent[1]-_extent[0]+1, _extent[3]-_extent[2]+1, _extent[5]-_extent[4]+1]

            # vtkArray to Numpy array with reshape [x,y,z]
            np_image = vtk_to_numpy(image.GetPointData().GetArray(0))
            np_image = np_image.reshape(ConstPixelDims,order='F')

            # Create max image
            max_image = np_image.max(axis=2)/5.491488103
            max_value = np.amax(max_image)
            remove_zero = max_image[~np.all(max_image == 0, axis=1)]
            transposed_image = np.transpose(remove_zero)
            final_image = transposed_image[~np.all(transposed_image == 0, axis=1)]
            final_image = np.pad(final_image, (5,5), 'constant', constant_values=(0, 0))
            globals()['final_image%s' % sample_number] = final_image

            # Flip right knees (note that every second name is a right knee)
            if sample_number % 2 == 0:
                final_image = np.fliplr(final_image)

            #Find center of mass
            com = scipy.ndimage.measurements.center_of_mass(final_image)
            c_y = com[1]
            c_x = com[0]

            #Calculate Image Dimenstions
            x_dim = final_image.shape[0]
            y_dim = final_image.shape[1]

            #Calculate points
            points_x = []
            points_y = []
            for i in range(npoints):
                    r = 0
                    x = c_x
                    y = c_y
                    value = 1
                    while (value !=0) and (x < (x_dim-1)) and (y < (y_dim-1)) and (x >=0) and (y >=0):
                            x = c_x - r*math.cos(angle)
                            y = c_y + r*math.sin(angle)
                            value = final_image[[x], [y]]
                            r = r + 1
                    y_final = c_y + (r-2)*math.sin(angle)
                    x_final = c_x - (r-2)*math.cos(angle)
                    points_x.append(x_final)
                    points_y.append(y_final)
                    angle = angle + angle_inc

                    array_x = np.array(points_x)
                    array_y = np.array(points_y)
                    combined = np.vstack((array_x, array_y)).T

            # Write out points
            write_file  = np.array(['index\n64'])
            np.savetxt(filename_points, write_file, delimiter=" ", fmt="%s")
            with open(filename_points,'a') as file:
                np.savetxt(file, combined)

            # Show figure of points
            plot = plt.figure()
            plt.imshow(final_image,cmap= "nipy_spectral", vmin=-0, vmax=3)
            plt.scatter(x=array_y, y=array_x, c='r', s=40)
            plt.scatter(x=c_y, y=c_x, c='b', s=40)
            #plt.savefig("/Users/jbhatla/Documents/UofC/PrEOA/Analysis/test.png")
            #plt.show()


            ######################  Create binary files #################
            #Create blank image
            imagedata2 = vtk.vtkImageData()
            imagedata2.SetDimensions(y_dim, x_dim, 1)
            imagedata2.SetNumberOfScalarComponents(1)
            imagedata2.SetScalarTypeToFloat()

            #Fill image with binary information
            for x in range (0, (x_dim)):
                for y in range (0, (y_dim)):
                    value = final_image[[x], [y]]
                    if value > 0:
                        imagedata2.SetScalarComponentFromFloat(y, (x), 0, 0, 1)
                    if value == 0:
                        imagedata2.SetScalarComponentFromFloat(y, (x), 0, 0, 0)

            # Cast image to right type
            outputScalarType = vtk.VTK_SHORT

            caster2 = vtk.vtkImageCast()
            caster2.SetOutputScalarType(outputScalarType)
            caster2.SetInput(imagedata2)
            caster2.ReleaseDataFlagOff()
            caster2.Update()

            # Write the binary 2D image out
            writer = vtk.vtkMetaImageWriter()
            writer.SetInputConnection(caster2.GetOutputPort())
            writer.SetInput(imagedata2)
            writer.SetFileName(filename_roi_out)
            writer.Write()


        ################################################################################################
        ####### Create Scaled Image to be transforLAT Bone

        # Read in the 3D thickness map image
        aim = vtkn88.vtkn88AIMReader()
        aim.SetFileName(filename_original_bone)
        aim.DataOnCellsOff()
        aim.Update()
        image = aim.GetOutput()

        # calcuLATe dimensions [x,y,z]
        _extent = image.GetExtent()
        ConstPixelDims = [_extent[1]-_extent[0]+1, _extent[3]-_extent[2]+1, _extent[5]-_extent[4]+1]

        # vtkArray to Numpy array with reshape [x,y,z]
        np_image = vtk_to_numpy(image.GetPointData().GetArray(0))
        np_image = np_image.reshape(ConstPixelDims,order='F')

        #Create max image
        max_image = np_image.max(axis=2)/5.491488103
        max_value = np.amax(max_image)
        transposed_image = np.transpose(max_image)
        final_image = np.pad(transposed_image, (5,5), 'constant', constant_values=(0, 0))

        #Flip right knees
        if sample_number % 2 == 0:
            final_image = np.fliplr(final_image)

        #Calculate dimentions
        x_dim = final_image.shape[0]
        y_dim = final_image.shape[1]

        #Create blank image
        imagedata = vtk.vtkImageData()
        imagedata.SetDimensions(y_dim, x_dim, 1)
        imagedata.SetNumberOfScalarComponents(1)
        imagedata.SetScalarTypeToFloat()

        #Fill image with max thickness values
        for x in range (0, (x_dim)):
            for y in range (0, (y_dim)):
                value = final_image[[x], [y]]
                value_sca = value*1000
                value_int = np.rint(value_sca)
                imagedata.SetScalarComponentFromFloat(y, (x), 0, 0, value_int)

        # Cast
        outputScalarType = vtk.VTK_SHORT

        caster = vtk.vtkImageCast()
        caster.SetOutputScalarType(outputScalarType)
        caster.SetInput(imagedata)
        caster.ReleaseDataFlagOff()
        caster.Update()

        # Write the image out
        writer = vtk.vtkMetaImageWriter()
        writer.SetInputConnection(caster.GetOutputPort())
        writer.SetInput(imagedata)
        writer.SetFileName(filename_sca_bone)
        writer.Write()

        ####### Create Scaled Image to be transforLAT Cartilage (Same as above but for cartilage)

        # Read in the cartilage image
        aim = vtkn88.vtkn88AIMReader()
        aim.SetFileName(filename_original_cart)
        aim.DataOnCellsOff()
        aim.Update()
        image = aim.GetOutput()

        # calcuLATe dimensions [x,y,z]
        _extent = image.GetExtent()
        ConstPixelDims = [_extent[1]-_extent[0]+1, _extent[3]-_extent[2]+1, _extent[5]-_extent[4]+1]

        # vtkArray to Numpy array with reshape [x,y,z]
        np_image = vtk_to_numpy(image.GetPointData().GetArray(0))
        np_image = np_image.reshape(ConstPixelDims,order='F')

        #Create max map
        max_image = np_image.max(axis=2)/5.491488103
        max_value = np.amax(max_image)
        transposed_image = np.transpose(max_image)
        final_image = np.pad(transposed_image, (5,5), 'constant', constant_values=(0, 0))

        #Flip right knees
        if sample_number % 2 == 0:
            final_image = np.fliplr(final_image)

        #Get image dimesions
        x_dim = final_image.shape[0]
        y_dim = final_image.shape[1]

        #Create blank image
        imagedata = vtk.vtkImageData()
        imagedata.SetDimensions(y_dim, x_dim, 1)
        imagedata.SetNumberOfScalarComponents(1)
        imagedata.SetScalarTypeToFloat()

        #Fill image with thickness data
        for x in range (0, (x_dim)):
            for y in range (0, (y_dim)):
                value = final_image[[x], [y]]
                value_sca = value*1000
                value_int = np.rint(value_sca)
                imagedata.SetScalarComponentFromFloat(y, (x), 0, 0, value_int)

        # Cast
        outputScalarType = vtk.VTK_SHORT
        print "Converting to {0}".format(vtk.vtkImageScalarTypeNameMacro(outputScalarType))
        caster = vtk.vtkImageCast()
        caster.SetOutputScalarType(outputScalarType)
        caster.SetInput(imagedata)
        caster.ReleaseDataFlagOff()
        caster.Update()

        # Write the image out
        writer = vtk.vtkMetaImageWriter()
        writer.SetInputConnection(caster.GetOutputPort())
        writer.SetInput(imagedata)
        writer.SetFileName(filename_sca_cart)
        writer.Write()

        #Do next roi and sample numbers
        roi_number = roi_number + 1
        if roi_number == 9:
            sample_number = sample_number+1
            roi_number = 1
        print sample_number
        print roi_number
