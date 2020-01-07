#!/usr/bin/env python
#
# File: createPoint.py
#
# History:
#   2016.05.24  babesler@ucalgary.ca    Created based on Faim tutorial
#
# Description:
#   This file creates an image 'point.aim' which is white (value 127) only
#   in the center for a single pixel and black (value 0) everywhere else
#
# Notes:
#   - You have to change the file to change anything (values, names, etc)
#   - The pixel is slightly off center since the size of the image dimensions
#       are odd (i.e. pixel from 50:51)

# Imports
import vtkbonelab
import vtk
import numpy as np
import os
from vtk.util.numpy_support import numpy_to_vtk

# Constants
outputDirectory = os.path.join('.')
outputFile = os.path.join(outputDirectory, 'point.aim')
IMAGE_VALUE = 127
M = 100

# Create the image data (ones for negative x)
dims = np.array((M, M, M))
cellmap = np.zeros(dims)
cellmap[M/2, M/2, M/2] = IMAGE_VALUE

# Convert to vtk image
cellmap_vtk = numpy_to_vtk(np.ravel(cellmap), deep=1, array_type=vtk.VTK_CHAR)
image = vtk.vtkImageData()
image.SetDimensions(dims+1)
image.GetCellData().SetScalars(cellmap_vtk)

# Write the image out
writer = vtkbonelab.vtkbonelabAIMWriter()
writer.CompressDataOn()
writer.SetFileName(outputFile)
writer.SetInputData(image)
writer.Update()

print "Finished!"
