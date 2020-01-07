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

outputAimFile = os.path.splitext(inputAimFile)[0] + "_FINAL.aim"



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

#trabMask = vtk.vtkPolyDataReader()
#trabMask.SetFileName(trabMaskFile)
#trabMask.Update()

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

#Debugging
#Log ("Read %d points from test AIM file." % imagetest.GetNumberOfPoints())
#imageBoundstest = imagetest.GetBounds()
#Log ("Image bounds:", ("%.4f" + " %.4f"*5) % imageBoundstest)


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



#clip to have smooth surface on ends

imageClip = reslice.GetOutput()
Log ("Read %d points from AIM file." % imageClip.GetNumberOfPoints())
imageBoundsClip = imageClip.GetBounds()
Log ("Image bounds:",
	 ("%.4f" + " %.4f"*5) % imageBoundsClip)



#clip = vtk.vtkExtractVOI()
#clip.SetInput(reslice.GetOutput())
#clip.Update()
#wholeVOI = clip.GetVOI()
#clip.SetVOI(wholeVOI[0], wholeVOI[1], wholeVOI[2], wholeVOI[3], wholeVOI[4], wholeVOI[5])
#clip.Update()


clip = vtk.vtkImageClip()
clip.SetInput(reslice.GetOutput())
clip.ClipDataOn()
clip.Update()
wholeVOI = clip.GetOutputWholeExtent()
#clip.SetOutputWholeExtent(wholeVOI[0], wholeVOI[1], wholeVOI[2], wholeVOI[3], wholeVOI[4]+30, wholeVOI[5]-5)
clip.SetOutputWholeExtent(wholeVOI[0], wholeVOI[1], wholeVOI[2], wholeVOI[3], wholeVOI[4], wholeVOI[5])
clip.Update()


imageClip2 = clip.GetOutput()
Log ("Read %d points from AIM file." % imageClip2.GetNumberOfPoints())
imageBoundsClip2 = imageClip2.GetBounds()
Log ("Image bounds:",
	 ("%.4f" + " %.4f"*5) % imageBoundsClip2)



image2 = clip.GetOutput()
imageBounds2 = image2.GetBounds()



# -------------------------------------------------------------------------
# Write out cropped and filtered aim

outputAimFilePre = os.path.splitext(inputAimFile)[0] + "_PRE.aim"

print "Writing to", outputAimFilePre
writer = vtkn88.vtkn88AIMWriter()
#writer.DebugOn()
writer.SetInput (image2)
#writer.NewProcessingLogOff()
#writer.SetProcessingLog (log)
#writer.CalculatePositionFromOriginOn()
writer.SetFileName (outputAimFilePre)
#writer.Write()


# -------------------------------------------------------------------------
# Grab the scalar data from the AIM (which is the actual data),
# and convert it to a native numpy array.
# Note: Both the vtkImage and numpy array point to the *same* underlying
# data. No copy is made.
# Caveat: At some (not to distant) future date, AimReader will be
# using the Scalars on the CellData instead of the PointData scalars.

scalars = image2.GetPointData().GetScalars()

imageArray = numpy_support.vtk_to_numpy (scalars)

# Convert it to a float array because doing math with 8 bit precision is dopey.
# (Note: This obviously *does* make a copy of the original data)

imageAsFloat = array (imageArray, float)

print "Initial range of data is %.3f to %.3f" % (min(imageAsFloat), max(imageAsFloat))

# -------------------------------------------------------------------------
# Manipulate the numpy array.

# Linear transform
imageAsFloat = float(calibrationSlope)*imageAsFloat + float(calibrationIntercept)

# Correct for values removed by masking precess that were set to zero (instead of image minimum)
imageAsFloat[imageAsFloat==float(calibrationIntercept)] = 0

# Threshold away negative values and assume fully mineralized = 1200 mg/ccm
minImage = min(imageAsFloat)
maxImage = max(imageAsFloat)
print "After density calibration, it has a range of %.3f to %.3f" % (minImage, maxImage)

#imageAsFloat *= imageAsFloat>0
#imageAsFloat += 500

numpy.clip(imageAsFloat, 0, 1200, out=imageAsFloat)

minImage = min(imageAsFloat)
maxImage = max(imageAsFloat)
print "After rescale calibration, it has a range of %.3f to %.3f" % (minImage, maxImage)

# Convert units from mg/cm3 to g/cm3
#imageAsFloat /= 1000.0

# Exponential transform
# Note that the operator ** is exponentiation in python (Do not use ^)
#imageAsFloat = modulus*imageAsFloat**exponent

#minImage = min(imageAsFloat)
#maxImage = max(imageAsFloat)
#print "After conversion to modulus, it has a range of %.3f to %.3f" % (minImage, maxImage)


# Normalize
imageAsFloat = (127.0/(maxImage - minImage)) * (imageAsFloat - minImage)

# Debugging
minImageNorm = min(imageAsFloat)
maxImageNorm = max(imageAsFloat)
print "Normalized, it has a range of %.3f to %.3f" % (minImageNorm, maxImageNorm)

# -------------------------------------------------------------------------
# Convert the numpy array back to a vtkArray and re-assign it to
# be the PointData scalars of the image.

# Convert to int8 (i.e. VTK_CHAR)
imageArray = array (imageAsFloat, int8)
scalars = numpy_support.numpy_to_vtk (imageArray)
image2.GetPointData().SetScalars(scalars)
image2.SetScalarTypeToChar()




# -------------------------------------------------------------------------
# Write out the result

print "Writing to", outputAimFile
writer = vtkn88.vtkn88AIMWriter()
#writer.DebugOn()
writer.SetInput (image2)
#writer.NewProcessingLogOff()
#writer.SetProcessingLog (log)
#writer.CalculatePositionFromOriginOn()
writer.SetFileName (outputAimFile)
writer.Write()
writer.Update()


Log ("Done.")
