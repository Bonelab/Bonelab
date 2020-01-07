#!/usr/bin/env python
#
# File: genRange.py
#
# History:
#   2016.05.25  babesler@ucalgary.ca    Created based on Faim tutorial
#
# Description:
#   This file creates an image 'range.aim' which has all values up to 127 in a
#   single image.
#
# Notes:
#   - You have to change the file to change anything (values, names, etc)

# Imports
import vtkbonelab
import vtk
import numpy as np
import os
from vtk.util.numpy_support import numpy_to_vtk

# Constants
outputDirectory = os.path.join('.')
outputFile = os.path.join(outputDirectory, 'range.aim')
M = 128

# Create the image data (ones for negative x; note that this is sloppy)
dims = np.array((1, 1, M))
cellmap = np.zeros(dims)
for i in range(0, M):
    cellmap[0, 0, i] = i

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
