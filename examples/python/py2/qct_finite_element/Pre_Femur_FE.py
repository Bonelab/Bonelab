from __future__ import division

import os
import sys
import time
import vtk
import vtkski




# -------------------------------------------------------------------------

if (len(sys.argv) != 5):
  print "Usage: vtkpython Pre_Femur_FE input.aim output.aim cortMask.wrl 88.1125"
  sys.exit(1)
#inputDirectory = sys.argv[1]
inputAimFile = sys.argv[1]
outputAimFile = sys.argv[2]
cortMaskFile = sys.argv[3]
angle = sys.argv[4]

# Read  input data
#reader = vtk.vtkDICOMImageReader()
#reader.SetDirectoryName(inputDirectory) 
#reader.Update()

# -------------------------------------------------------------------------
# Read  input data
print "Reading input data."
reader = vtkski.vtkskiAIMReader()
reader.SetFileName (inputAimFile)
reader.Update()
image = reader.GetOutput()
print "Read %d points from AIM file." % image.GetNumberOfPoints()
imageBounds = image.GetBounds()
#Log ("Image bounds:",
       #	 ("%.4f" + " %.4f"*5) % imageBounds)

# Read  input data with GDCM
#reader = vtk.vtkGDCMImageReader()
#reader.SetFileNames(inputDirectory) 
#reader.Update()


cortMask = vtk.vtkPolyDataReader()
cortMask.SetFileName(cortMaskFile)
cortMask.Update()


stencilData = vtk.vtkPolyDataToImageStencil()
stencilData.SetInput(cortMask.GetOutput())
stencilData.SetInformationInput(image)

stencil = vtk.vtkImageStencil()
stencil.SetInput(image)
stencil.SetBackgroundValue(-500)
stencil.SetStencil(stencilData.GetOutput())


# Create transform that rotates image to desired orientation
transform = vtk.vtkTransform()
transform.RotateZ(float(angle))

# Find associated 4x4 matrix
matrix = vtk.vtkMatrix4x4()
matrix = transform.GetMatrix()

# Apply matrix to image with cubic interpolation
reslice = vtk.vtkImageReslice()
reslice.SetInput(stencil.GetOutput())
reslice.SetResliceAxes(matrix)
reslice.SetInterpolationModeToCubic()


image2 = reslice.GetOutput()
imageBounds = image2.GetBounds()

# -------------------------------------------------------------------------
writer = vtkski.vtkskiAIMWriter()
writer.SetInput (image2)
#writer.SetPosition(-108,-105,-33)
#writer.CalculatePositionFromOriginOn()
writer.SetFileName (outputAimFile)
writer.Write()


