from __future__ import division

import os
import sys
import time
import vtk
import vtkn88

# Required for manipulating arrays in numpy
import numpy
from numpy.core import *
from vtk.util import numpy_support

# -------------------------------------------------------------------------
#  Configuration

if (len(sys.argv) != 6):
  print "Usage: vtkpython Radius_FE NORM_001.AIM cortMask.vtk 1.22 -3.34 58.7"
  sys.exit(1)
inputAimFile = sys.argv[1]
inputCortMaskFile = sys.argv[2]
calibrationSlope = sys.argv[3]
calibrationIntercept = sys.argv[4]
angle = sys.argv[5]

outputFaimFile = os.path.splitext(inputAimFile)[0] + "_FAL_ISO.inp"

# Read in configuration file.
#print "Reading configuration file", configFile
# Here we are actually executing it as python code.
#execfile (configFile)

# Print out values that we read in.  This also has the effect of causing
# this script to die if configuration values are missing (which is a good thing).

print "input file                            :", inputAimFile
print "output file                           :", outputFaimFile
print "cortical mask                         :", inputCortMaskFile
print "calibration slope                     :", calibrationSlope
print "calibration intercept                 :", calibrationIntercept
print "angle                                 :", angle


# -------------------------------------------------------------------------

"""Function to print message with time stamp.
"""
def Log (msg, *additionalLines):
  # Print first line with time stamp
  print "%9.3f %s" % (time.time()-startTime, msg)
  # Print subsequent lines indented by 10 spaces
  for line in additionalLines:
    print " " * 10 + line

startTime = time.time()

# -------------------------------------------------------------------------
# Read  input data


Log ("Reading input data and masks.")
reader = vtkn88.vtkn88AIMReader()
#reader.DataOnCellsOn()
reader.SetFileName (inputAimFile)
reader.Update()

image = reader.GetOutput()
#print "Read %d points from AIM file." % image.GetNumberOfPoints()
imageBounds = image.GetBounds()

#Debugging
#Log ("Read %d points from test AIM file." % image.GetNumberOfPoints())
#imageBoundstest = image.GetBounds()
#Log ("Image bounds:", ("%.4f" + " %.4f"*5) % imageBoundstest)

cortMask = vtk.vtkPolyDataReader()
cortMask.SetFileName(inputCortMaskFile)
cortMask.Update()



stencilData = vtk.vtkPolyDataToImageStencil()
stencilData.SetInput(cortMask.GetOutput())
stencilData.SetInformationInput(image)

stencil = vtk.vtkImageStencil()
stencil.SetInput(image)
stencil.SetBackgroundValue(-500)
stencil.SetStencil(stencilData.GetOutput())
stencil.Update()

imagetest = stencil.GetOutput()
imageBoundstest = imagetest.GetBounds()


stencilDataMask = vtk.vtkPolyDataToImageStencil()
stencilDataMask.SetInput(cortMask.GetOutput())
stencilDataMask.SetInformationInput(image)

stencilMask = vtk.vtkImageStencil()
stencilMask.SetInput(image)
stencilMask.SetBackgroundValue(0)
stencilMask.SetStencil(stencilDataMask.GetOutput())
stencilMask.Update()

stencilMask2 = vtk.vtkImageStencil()
stencilMask2.SetInput(stencilMask.GetOutput())
stencilMask2.ReverseStencilOn()
stencilMask2.SetBackgroundValue(1)
stencilMask2.SetStencil(stencilDataMask.GetOutput())
stencilMask2.Update()

#----------------------------------------------------------------------------------------------
#Rotate image and mask

# Create transform that rotates image to desired orientation
transform = vtk.vtkTransform()
transform.RotateY(float(angle))


# Find associated 4x4 matrix
matrix = vtk.vtkMatrix4x4()
matrix = transform.GetMatrix()

# Apply matrix to image with cubic interpolation
#rescale to ???? mm isotropic voxels
reslice = vtk.vtkImageReslice()
reslice.SetInput(stencil.GetOutput())
reslice.SetResliceAxes(matrix)
reslice.SetInterpolationModeToCubic()
reslice.SetOutputSpacing(0.625, 0.625, 0.625)
reslice.Update()


# Apply matrix to mask with cubic interpolation
#rescale to ???? mm isotropic voxels
resliceMask = vtk.vtkImageReslice()
resliceMask.SetInput(stencilMask2.GetOutput())
resliceMask.SetResliceAxes(matrix)
resliceMask.SetInterpolationModeToNearestNeighbor()
resliceMask.SetOutputSpacing(0.625, 0.625, 0.625)
resliceMask.Update()





#----------------------------------------------------------------------------------------------

#clip to have smooth surface on ends

#imageClip = reslice.GetOutput()
#Log ("Read %d points from AIM file." % imageClip.GetNumberOfPoints())
#imageBoundsClip = imageClip.GetBounds()
    #Log ("Image bounds:",
#("%.4f" + " %.4f"*5) % imageBoundsClip)

#clip = vtk.vtkExtractVOI()
#clip.SetInput(reslice.GetOutput())
#clip.Update()
#wholeVOI = clip.GetVOI()
#clip.SetVOI(wholeVOI[0], wholeVOI[1], wholeVOI[2], wholeVOI[3], wholeVOI[4], wholeVOI[5])
#clip.Update()


#clip = vtk.vtkImageClip()
#clip.SetInput(reslice.GetOutput())
#clip.ClipDataOn()
#clip.Update()
#wholeVOI = clip.GetOutputWholeExtent()
#clip.SetOutputWholeExtent(wholeVOI[0], wholeVOI[1], wholeVOI[2], wholeVOI[3], wholeVOI[4]+30, wholeVOI[5]-5)
#clip.SetOutputWholeExtent(wholeVOI[0], wholeVOI[1], wholeVOI[2], wholeVOI[3], wholeVOI[4], wholeVOI[5])
#clip.Update()


#imageClip2 = clip.GetOutput()
#Log ("Read %d points from AIM file." % imageClip2.GetNumberOfPoints())
#imageBoundsClip2 = imageClip2.GetBounds()
    #Log ("Image bounds:",
#("%.4f" + " %.4f"*5) % imageBoundsClip2)

#----------------------------------------------------------------------------------------------

image2 = reslice.GetOutput()
imageBounds2 = image2.GetBounds()

imageMask = resliceMask.GetOutput()
imageMaskBounds = imageMask.GetBounds()
imageMask.Update()

cast = vtk.vtkImageCast()
cast.SetInput(resliceMask.GetOutput())
cast.SetOutputScalarTypeToChar()
cast.Update()

# Convert to int8 (i.e. VTK_CHAR)
#imageMask.SetScalarTypeToChar()
#imageMask.AllocateScalars()
#imageMask.Update()


# -------------------------------------------------------------------------
# Write out cropped aim

outputAimFilePre = os.path.splitext(inputAimFile)[0] + "_PRE.aim"

print "Writing to", outputAimFilePre
writer = vtkn88.vtkn88AIMWriter()
writer.SetInput (image2)
writer.SetFileName (outputAimFilePre)
writer.Write()



# -------------------------------------------------------------------------
# Write out cropped aim mask

outputAimFilePreMask = os.path.splitext(inputAimFile)[0] + "_MASK.aim"

print "Writing to", outputAimFilePreMask
writerMask = vtkn88.vtkn88AIMWriter()
writerMask.SetInput (cast.GetOutput())
writerMask.SetFileName (outputAimFilePreMask)
writerMask.Write()


Log ("Done.")
