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

if (len(sys.argv) != 11):
  print "Usage: vtkpython Femur_FE example.conf NORM_001.AIM cortMask.vtk trabmask.vtk 1.22 -3.34 33.7 15 10 175 10.5 5.5"
  sys.exit(1)
configFile = sys.argv[1]
inputAimFile = sys.argv[2]
inputCortMaskFile = sys.argv[3]
inputTrabMaskFile = sys.argv[4]
calibrationSlope = sys.argv[5]
calibrationIntercept = sys.argv[6]
angle = sys.argv[7]
neckAngle = sys.argv[8]
angleShaft = sys.argv[9]
shaftLength = sys.argv[10]
#headConstraintMaxDepth = float(sys.argv[11])
#trochConstraintMaxDepth = float(sys.argv[12])



outputFaimFile = os.path.splitext(inputAimFile)[0] + "_" + neckAngle + ".inp"
outputCapFile = os.path.splitext(inputAimFile)[0] + "_CAP.aim"

# Read in configuration file.
print "Reading configuration file", configFile
# Here we are actually executing it as python code.
execfile (configFile)

# Print out values that we read in.  This also has the effect of causing
# this script to die if configuration values are missing (which is a good thing).

print "input file                            :", inputAimFile
print "output file                           :", outputFaimFile
print "cortical mask                         :", inputCortMaskFile
print "trabecular mask                       :", inputTrabMaskFile
print "calibration slope                     :", calibrationSlope
print "calibration intercept                 :", calibrationIntercept
print "element size                          :", elementSize
print "angle                                 :", angle
print "neck angle                            :", neckAngle
print "shaft angle                           :", angleShaft
print "shaft end to head length              :", shaftLength
print "model type                            :", modelType
print "modulus                               :", modulus
print "Poisson's ratio                       :", poisson
print "head displacement                     :", trochDisplacement
print "head constraint max depth             :", headConstraintMaxDepth
print "trochanter contraint max depth        :", trochConstraintMaxDepth
#print "number of E values                    :", numberE

# -------------------------------------------------------------------------
#Function to print message with time stamp.

def Log (msg, *additionalLines):
  # Print first line with time stamp
  print "%9.3f %s" % (time.time()-startTime, msg)
  # Print subsequent lines indented by 10 spaces
  for line in additionalLines:
    print " " * 10 + line

startTime = time.time()

# Set normal vectors for femoral head and greater trochanter
normalHeadVector  = (0,0,1)
normalTrochVector = (0,0,-1)
normalShaftVector = (1,0,0)

# neckAngle input always represents angle of internal rotation
# this is different for left and right femurs
# may need more robust check than just >100 to decide left and right
if (float(angle) > 100):
  angle = float(angle) + float(neckAngle)
else:
  angle = float(angle) - float(neckAngle)

print "Actual rotation is %.3f" % angle

# -------------------------------------------------------------------------
# Read  input data and mask to only select ROI defined by vtk masks

outputAimFile = os.path.splitext(inputAimFile)[0] + "_CAL.aim"
outputAimFile2 = os.path.splitext(inputAimFile)[0] + "_CAL_TEST.aim"

Log ("Reading input data and masks.")
reader = vtkn88.vtkn88AIMReader()
reader.SetFileName (inputAimFile)
reader.DebugOff()
reader.Update()

image = reader.GetOutput()
imageBounds = image.GetBounds()

#Debugging
#Log ("Read %d points from test AIM file." % image.GetNumberOfPoints())
#imageBoundstest = image.GetBounds()
#Log ("Image bounds:", ("%.4f" + " %.4f"*5) % imageBoundstest)

# -------------------------------------------------------------------------
# -------------------------------------------------------------------------
# Perform rough cut (bounding box) based on cortical mask to improve speed
'''

cortMask = vtk.vtkPolyDataReader()
cortMask.SetFileName(inputCortMaskFile)
cortMask.Update()

origin = image.GetOrigin()
Log ("Image origin:", ("%.4f" + " %.4f"*2) % origin)

dimensions = reader.GetOutput().GetDimensions()
Log ("Image dimensions", ("%.4f" + " %.4f"*2) % dimensions)

spacing = reader.GetOutput().GetSpacing()
Log ("Image spacing", ("%.4f" + " %.4f"*2) % spacing)

cortMaskBounds = cortMask.GetOutput().GetBounds()
Log ("Cortical mask bounds", ("%.4f" + " %.4f"*5) % cortMaskBounds)

originMask = (cortMaskBounds[0]*spacing[0], cortMaskBounds[1]*spacing[1], cortMaskBounds[2]*spacing[2])
Log ("Mask origin:", ("%.4f" + " %.4f"*2) % originMask)

newExtent = (int((cortMaskBounds[0]-origin[0])/spacing[0]),
		int((cortMaskBounds[1]-origin[0])/spacing[0]),
		int((cortMaskBounds[2]-origin[1])/spacing[1]),
		int((cortMaskBounds[3]-origin[1])/spacing[1]),
		int((cortMaskBounds[4]-origin[2])/spacing[2]),
		int((cortMaskBounds[5]-origin[2])/spacing[2])) 
	
Log ("New Extent",
   ("%.4f" + " %.4f"*5) % newExtent)

reslice = vtk.vtkExtractVOI()
reslice.SetInput( image )
reslice.SetVOI(newExtent)
reslice.Update()

image = reslice.GetOutput()
origin2 = image.GetOrigin()
image.SetOrigin(cortMaskBounds[0], cortMaskBounds[2], cortMaskBounds[4])
image.Update()

imageBoundsCut = reslice.GetOutput().GetBounds()
Log ("Rough cut image bounds", ("%.4f" + " %.4f"*5) % imageBoundsCut)

# -------------------------------------------------------------------------
# DEBUGGING Write out cropped and filtered aim
outputAimFileTest = os.path.splitext(inputAimFile)[0] + "_TEST_ROUGH_CUT.aim"
writer = vtkn88.vtkn88AIMWriter()
writer.SetInput (image)
writer.SetFileName (outputAimFileTest)
#writer.Write()
# -------------------------------------------------------------------------

'''


# -------------------------------------------------------------------------
# -------------------------------------------------------------------------
# Perform masking of regions with cortical and trabecular 

cortMask = vtk.vtkPolyDataReader()
cortMask.SetFileName(inputCortMaskFile)
cortMask.Update()

stencilData = vtk.vtkPolyDataToImageStencil()
stencilData.SetInput(cortMask.GetOutput())
stencilData.SetInformationInput(image)
stencilData.SetTolerance(1)


stencilWholeBone = vtk.vtkImageStencil()
stencilWholeBone.SetInput(image)
stencilWholeBone.SetBackgroundValue(-2000)
stencilWholeBone.SetStencil(stencilData.GetOutput())
stencilWholeBone.Update()

imageWholeBone = stencilWholeBone.GetOutput()
imageBoundstest = imageWholeBone.GetBounds()

#Cut out copy of trabecular region from stencilWholeBone
trabMask = vtk.vtkPolyDataReader()
trabMask.SetFileName(inputTrabMaskFile)
trabMask.Update()

stencilDataTrab = vtk.vtkPolyDataToImageStencil()
stencilDataTrab.SetInput(trabMask.GetOutput())
stencilDataTrab.SetInformationInput(imageWholeBone)

stencilTrabBone = vtk.vtkImageStencil()
stencilTrabBone.SetInput(imageWholeBone)
stencilTrabBone.SetBackgroundValue(0)
stencilTrabBone.SetStencil(stencilDataTrab.GetOutput())
stencilTrabBone.Update()

#'Remove' trabecular region to get cortical region
stencilDataNoTrab = vtk.vtkPolyDataToImageStencil()
stencilDataNoTrab.SetInput(trabMask.GetOutput())
stencilDataNoTrab.SetInformationInput(imageWholeBone)

stencilNoTrabBone = vtk.vtkImageStencil()
stencilNoTrabBone.ReverseStencilOn()
stencilNoTrabBone.SetInput(imageWholeBone)
stencilNoTrabBone.SetBackgroundValue(0)
stencilNoTrabBone.SetStencil(stencilDataNoTrab.GetOutput())
stencilNoTrabBone.Update()


# -------------------------------------------------------------------------
# DEBUGGING Write out cropped and filtered aim

#add two regions together
#blendCortTrab = vtk.vtkImageMathematics()
#blendCortTrab.SetOperationToAdd()
#blendCortTrab.SetInput1(stencilTrabBone.GetOutput())
#blendCortTrab.SetInput2(stencilNoTrabBone.GetOutput())
#blendCortTrab.Update()

#outputAimFileTest = os.path.splitext(inputAimFile)[0] + "_SOLID_CORT.aim"
#writer = vtkn88.vtkn88AIMWriter()
#writer.SetInput (blendCortTrab.GetOutput())
#writer.SetFileName (outputAimFileTest)
#writer.Write()
# -------------------------------------------------------------------------


# Create transform that rotates image to desired orientation
# + 90.0 changes so force is applied in z direction
transform = vtk.vtkTransform()
transform.RotateZ(float(angle))
transform.RotateY(float(angleShaft)+90.0)

# Find associated 4x4 matrix
matrix = vtk.vtkMatrix4x4()
matrix = transform.GetMatrix()

# Apply matrix to image with cubic interpolation
#rescale to "elementSize" mm isotropic voxels
resliceCort = vtk.vtkImageReslice()
resliceTrab = vtk.vtkImageReslice()


##IF statement to check which type of model (ie if need to separate cort and trab)
if (modelType == 4):
  reslice.SetInput(blendCortTrab.GetOutput())
else:
  resliceCort.SetInput(stencilNoTrabBone.GetOutput())
  resliceTrab.SetInput(stencilTrabBone.GetOutput())

resliceCort.SetResliceAxes(matrix)
resliceCort.SetInterpolationModeToCubic()
resliceCort.SetOutputSpacing(elementSize, elementSize, elementSize)
resliceCort.Update()

resliceTrab.SetResliceAxes(matrix)
resliceTrab.SetInterpolationModeToCubic()
resliceTrab.SetOutputSpacing(elementSize, elementSize, elementSize)
resliceTrab.Update()

imageTrab = resliceTrab.GetOutput()
imageCort = resliceCort.GetOutput()


# -------------------------------------------------------------------------
# DEBUGGING
# Write out cropped and filtered aim
outputAimFilePre = os.path.splitext(inputAimFile)[0] + "_CORT.aim"
writer = vtkn88.vtkn88AIMWriter()
writer.SetInput (resliceCort.GetOutput())
writer.SetFileName (outputAimFilePre)
#writer.Write()
# -------------------------------------------------------------------------


# -------------------------------------------------------------------------
# DEBUGGING
# Write out cropped and filtered aim
outputAimFilePre = os.path.splitext(inputAimFile)[0] + "_TRAB.aim"
writer = vtkn88.vtkn88AIMWriter()
writer.SetInput (resliceTrab.GetOutput())
writer.SetFileName (outputAimFilePre)
#writer.Write()
# -------------------------------------------------------------------------


# -------------------------------------------------------------------------
# Grab the scalar data from the AIM (which is the actual data),
# and convert it to a native numpy array.
# Note: Both the vtkImage and numpy array point to the *same* underlying
# data. No copy is made.
# Caveat: At some (not to distant) future date, AimReader will be
# using the Scalars on the CellData instead of the PointData scalars.

scalarsTrab = imageTrab.GetPointData().GetScalars()
imageArrayTrab = numpy_support.vtk_to_numpy (scalarsTrab)

# Convert it to a float array because doing math with 8 bit precision is dopey.
# (Note: This obviously *does* make a copy of the original data)
imageAsFloatTrab = array (imageArrayTrab, float)
print "Initial range of data is %.3f to %.3f" % (min(imageAsFloatTrab), max(imageAsFloatTrab))

# -------------------------------------------------------------------------
# Manipulate the numpy array trabecular

# Linear transform
imageAsFloatTrab = float(calibrationSlope)*imageAsFloatTrab + float(calibrationIntercept)

# Correct for values removed by masking precess that were set to zero (instead of image minimum)
imageAsFloatTrab[imageAsFloatTrab==float(calibrationIntercept)] = 0

# Threshold away negative values and assume fully mineralized = 1200 mg/ccm
minImageTrab = min(imageAsFloatTrab)
maxImageTrab = max(imageAsFloatTrab)
print "After density calibration, trabecular has a range of %.3f to %.3f" % (minImageTrab, maxImageTrab)

numpy.clip(imageAsFloatTrab, 0, 1800, out=imageAsFloatTrab)

minImageTrab = min(imageAsFloatTrab)
maxImageTrab = max(imageAsFloatTrab)
print "After rescale calibration, trabecular has a range of %.3f to %.3f" % (minImageTrab, maxImageTrab)

# Normalize
imageAsFloatTrab = ((126)/(maxImageTrab - minImageTrab)) * (imageAsFloatTrab - minImageTrab)

# Debugging
minImageNormTrab = min(imageAsFloatTrab)
maxImageNormTrab = max(imageAsFloatTrab)
print "Normalized, trabecular has  a range of %.3f to %.3f" % (minImageNormTrab, maxImageNormTrab)


# -------------------------------------------------------------------------
# Convert the numpy array back to a vtkArray and re-assign it to
# be the PointData scalars of the image.

imageArrayTrab = array (imageAsFloatTrab, int16)
scalarsTrab = numpy_support.numpy_to_vtk (imageArrayTrab)
imageTrab.GetPointData().SetScalars(scalarsTrab)
imageTrab.SetScalarTypeToShort()


# -------------------------------------------------------------------------
# REPEAT process for cortical bone

scalarsCort = imageCort.GetPointData().GetScalars()
imageArrayCort = numpy_support.vtk_to_numpy (scalarsCort)
imageAsFloatCort = array (imageArrayCort, float)
print "Initial range of data is %.3f to %.3f" % (min(imageAsFloatCort), max(imageAsFloatCort))

# -------------------------------------------------------------------------
# Manipulate the numpy array cortical
# Linear transform
imageAsFloatCort = float(calibrationSlope)*imageAsFloatCort + float(calibrationIntercept)

# Correct for values removed by masking precess that were set to zero (instead of image minimum)
imageAsFloatCort[imageAsFloatCort==float(calibrationIntercept)] = 0

# Threshold away negative values and assume fully mineralized = 1800 mg/ccm
minImageCort = min(imageAsFloatCort)
maxImageCort = max(imageAsFloatCort)
print "After density calibration, cortical has a range of %.3f to %.3f" % (minImageCort, maxImageCort)

numpy.clip(imageAsFloatCort, 0, 1800, out=imageAsFloatCort)

minImageCort = min(imageAsFloatCort)
maxImageCort = max(imageAsFloatCort)
print "After rescale calibration, cortical has a range of %.3f to %.3f" % (minImageCort, maxImageCort)

# Normalize
imageAsFloatCort = ((((126)/(maxImageCort - minImageCort)) * (imageAsFloatCort - minImageCort))) + 126

imageAsFloatCort[imageAsFloatCort==126] = 0

# Debugging
minImageNormCort = min(imageAsFloatCort)
maxImageNormCort = max(imageAsFloatCort)
print "Normalized, cortical has  a range of %.3f to %.3f" % (minImageNormCort, maxImageNormCort)


# -------------------------------------------------------------------------
# Convert the numpy array back to a vtkArray and re-assign it to
# be the PointData scalars of the image.

imageArrayCort = array (imageAsFloatCort, int16)
scalarsCort = numpy_support.numpy_to_vtk (imageArrayCort)
imageCort.GetPointData().SetScalars(scalarsCort)
imageCort.SetScalarTypeToShort()


#add two regions together
blendCortTrab = vtk.vtkImageMathematics()
blendCortTrab.SetOperationToAdd()
blendCortTrab.SetInput1(imageTrab)
blendCortTrab.SetInput2(imageCort)
blendCortTrab.Update()


# -------------------------------------------------------------------------
# DEBUGGING Write out cropped and filtered aim
outputAimFileTest = os.path.splitext(inputAimFile)[0] + "_BLEND.aim"
writer = vtkn88.vtkn88AIMWriter()
writer.SetInput (blendCortTrab.GetOutput())
writer.SetFileName (outputAimFileTest)
#writer.Write()
# -------------------------------------------------------------------------


#whole bounds of image
boxBounds = blendCortTrab.GetOutput().GetBounds()

Log ("Bounds of bone nodes:",
   ("%.4f" + " %.4f"*5) % boxBounds)

boxBounds2 = (boxBounds[0],
		boxBounds[0]+ int(int(shaftLength)),
		boxBounds[2],
		boxBounds[3],
		boxBounds[4],
		boxBounds[5]) 
	
Log ("Limiting to box bounds:",
   ("%.4f" + " %.4f"*5) % boxBounds2)

box = vtk.vtkBox()
box.SetBounds (boxBounds2)

stencilData = vtk.vtkImplicitFunctionToImageStencil()
stencilData.SetInput(box)
stencilData.SetInformationInput(blendCortTrab.GetOutput())

stencil = vtk.vtkImageStencil()
stencil.SetInput(blendCortTrab.GetOutput())
stencil.SetBackgroundValue(0)
stencil.SetStencil(stencilData.GetOutput())
stencil.Update()

image2 = stencil.GetOutput()
imageBounds2 = image2.GetBounds()

'''
# -------------------------------------------------------------------------
# Create endcap for TROCHANTER

#create solid image where bone is 0 to crop caps from
image3 = vtk.vtkImageData()
image3.DeepCopy(image2)
image3.Update()

imageCap = vtk.vtkImageThreshold()
imageCap.SetInput(image3)
imageCap.ThresholdBetween(1,252)
imageCap.SetInValue(0)
imageCap.SetOutValue(253)
imageCap.Update()


# -------------------------------------------------------------------------
# DEBUGGING Write out cropped and filtered aim
outputAimFileTest = os.path.splitext(inputAimFile)[0] + "_CAP_TEST.aim"
writer = vtkn88.vtkn88AIMWriter()
writer.SetInput (imageCap.GetOutput())
writer.SetFileName (outputAimFileTest)
#writer.Write()
# -------------------------------------------------------------------------


#whole bounds of image
boxBounds = imageCap.GetOutput().GetBounds()

# Convert the 3D image data from the AIM file to hexagonal cells
hexa = vtkn88.vtkn88ImageToMesh()
hexa.SetInput(image2)
hexa.Update()

materialTable = vtkn88.vtkn88MaterialTable()

generator = vtkn88.vtkn88FiniteElementModelGenerator()
generator.SetInputConnection (0, hexa.GetOutputPort())
generator.SetInput(1, materialTable)
generator.Update()
modelTemp = generator.GetOutput()

# Find all the visible nodes.
visibleNodesIds = vtk.vtkIdTypeArray()

Log ("Finding nodes on trochanter for PMMA cap")

vtkn88.vtkn88NodeSetsByGeometry.FindNodesOnVisibleSurface (
  visibleNodesIds,
  modelTemp,
  normalTrochVector,
  -1)
Log ("Found %d visible exterior nodes." % visibleNodesIds.GetNumberOfTuples())


# Add this list of nodes to the model with the name "BONE TOP VISIBLE NODES"
modelTemp.AddNodeSet (visibleNodesIds, "BONE TROCH PMMA NODES")

# We're going to need these points as vtkPolyData, for one to write them
# out, but also to further filter based on geometry, so let's grab
# them now as vtkPolyData
visibleBoneVertices = modelTemp.DataSetFromSelection("BONE TROCH PMMA NODES")

# Now we filter this node set by maximum depth, measured from the highest
# surface node with the correct material that we found.
# Find highest surface point:
Log ("Filtering node set by depth.")
visibleBoneVertices.ComputeBounds()
visibleNodesBounds = visibleBoneVertices.GetBounds()

Log ("Bounds of visible bone nodes:",
   ("%.4f" + " %.4f"*5) % visibleNodesBounds)

boxBounds = (visibleNodesBounds[0],
		visibleNodesBounds[1],
		visibleNodesBounds[2],
		visibleNodesBounds[3],
		visibleNodesBounds[4],
		visibleNodesBounds[4]+trochConstraintMaxDepth) 
	
Log ("Limiting to box bounds:",
   ("%.4f" + " %.4f"*5) % boxBounds)
box = vtk.vtkBox()
box.SetBounds (boxBounds)
filter = vtk.vtkExtractGeometry()
filter.SetImplicitFunction (box)
filter.ExtractInsideOn()
filter.ExtractBoundaryCellsOn()
filter.SetInput (0, visibleBoneVertices)
filter.Update()
filteredSurfaceVertices = filter.GetOutput()

filteredSurfaceVertices.ComputeBounds()
filteredVisibleBounds = filteredSurfaceVertices.GetBounds()
Log ("Bounds of visible filtered bone nodes:",
     ("%.4f" + " %.4f"*5) % filteredVisibleBounds)


boxBounds2 = (filteredVisibleBounds[0]-5,
                  filteredVisibleBounds[1]+5,
                  filteredVisibleBounds[2]-5,
                  filteredVisibleBounds[3]+5,
                  filteredVisibleBounds[4]-5,
                  filteredVisibleBounds[5])

box = vtk.vtkBox()
box.SetBounds (boxBounds2)

stencilData = vtk.vtkImplicitFunctionToImageStencil()
stencilData.SetInput(box)
stencilData.SetInformationInput(image2)

stencil = vtk.vtkImageStencil()
stencil.SetInput(imageCap.GetOutput())
stencil.SetBackgroundValue(0)
stencil.SetStencil(stencilData.GetOutput())
stencil.Update()

blend1 = vtk.vtkImageMathematics()
blend1.SetOperationToAdd()
blend1.SetInput1(image2)
blend1.SetInput2(stencil.GetOutput())
blend1.Update()

blend = vtk.vtkImageMathematics()
blend.SetOperationToReplaceCByK()
blend.SetConstantC(255)
blend.SetConstantK(0)
blend.SetInput1(blend1.GetOutput())
blend.Update()


# -------------------------------------------------------------------------
# Create endcap for FEMORAL HEAD


image4 = vtk.vtkImageData()
image4.DeepCopy(image2)
image4.Update()

imageCap = vtk.vtkImageThreshold()
imageCap.SetInput(image4)
imageCap.ThresholdBetween(1,252)
imageCap.SetInValue(0)
imageCap.SetOutValue(253)
imageCap.Update()



# -------------------------------------------------------------------------
# DEBUGGING Write out cropped and filtered aim
#outputAimFileTest = os.path.splitext(inputAimFile)[0] + "_CAP_TEST.aim"
#writer = vtkn88.vtkn88AIMWriter()
#writer.SetInput (imageCap.GetOutput())
#writer.SetFileName (outputAimFileTest)
#writer.Write()
# -------------------------------------------------------------------------


Log ("Finding nodes on femoral head for PMMA cap")

vtkn88.vtkn88NodeSetsByGeometry.FindNodesOnVisibleSurface (
  visibleNodesIds,
  modelTemp,
  normalHeadVector,
  -1)
Log ("Found %d visible exterior nodes." % visibleNodesIds.GetNumberOfTuples())


# Add this list of nodes to the model with the name "BONE TOP VISIBLE NODES"
modelTemp.AddNodeSet (visibleNodesIds, "BONE HEAD PMMA NODES")

# We're going to need these points as vtkPolyData, for one to write them
# out, but also to further filter based on geometry, so let's grab
# them now as vtkPolyData
visibleBoneVertices = modelTemp.DataSetFromSelection("BONE HEAD PMMA NODES")

# Now we filter this node set by maximum depth, measured from the highest
# surface node with the correct material that we found.
# Find highest surface point:
Log ("Filtering node set by depth.")
visibleBoneVertices.ComputeBounds()
visibleNodesBounds = visibleBoneVertices.GetBounds()

Log ("Bounds of visible bone nodes:",
   ("%.4f" + " %.4f"*5) % visibleNodesBounds)

boxBounds = (visibleNodesBounds[0],
		visibleNodesBounds[1],
		visibleNodesBounds[2],
		visibleNodesBounds[3],
		visibleNodesBounds[5]-headConstraintMaxDepth,
		visibleNodesBounds[5]) 
	
Log ("Limiting to box bounds:",
   ("%.4f" + " %.4f"*5) % boxBounds)
box = vtk.vtkBox()
box.SetBounds (boxBounds)
filter = vtk.vtkExtractGeometry()
filter.SetImplicitFunction (box)
filter.ExtractInsideOn()
filter.ExtractBoundaryCellsOn()
filter.SetInput (0, visibleBoneVertices)
filter.Update()
filteredSurfaceVertices = filter.GetOutput()

filteredSurfaceVertices.ComputeBounds()
filteredVisibleBounds = filteredSurfaceVertices.GetBounds()
Log ("Bounds of visible filtered bone nodes:",
     ("%.4f" + " %.4f"*5) % filteredVisibleBounds)



boxBounds2 = (filteredVisibleBounds[0]-5,
                  filteredVisibleBounds[1]+5,
                  filteredVisibleBounds[2]-5,
                  filteredVisibleBounds[3]+5,
                  filteredVisibleBounds[4],
                  filteredVisibleBounds[5]+2)


Log ("Created BOX:",
    ("%.4f" + " %.4f"*5) % boxBounds2)
box = vtk.vtkBox()
box.SetBounds (boxBounds2)

stencilData = vtk.vtkImplicitFunctionToImageStencil()
stencilData.SetInput(box)
stencilData.SetInformationInput(blend.GetOutput())

stencil = vtk.vtkImageStencil()
stencil.SetInput(imageCap.GetOutput())
stencil.SetBackgroundValue(0)
stencil.SetStencil(stencilData.GetOutput())
stencil.Update()

image2.Update()

blend2 = vtk.vtkImageMathematics()
blend2.SetOperationToAdd()
blend2.SetInput1(blend.GetOutput())
blend2.SetInput2(stencil.GetOutput())
blend2.Update()

blend3 = vtk.vtkImageMathematics()
blend3.SetOperationToReplaceCByK()
blend3.SetConstantC(255)
blend3.SetConstantK(0)
blend3.SetInput1(blend2.GetOutput())
blend3.Update()


# -------------------------------------------------------------------------
# Create endcap for FEMORAL SHAFT

image5 = vtk.vtkImageData()
image5.DeepCopy(image2)
image5.Update()

#Debugging
#imageBounds = image5.GetBounds()
#Log ("Image bounds:", (" %.4f"*6) % imageBounds)

imagePadExtent = image5.GetExtent()

imagePad = vtk.vtkImageConstantPad()
imagePad.SetInput(image5)
imagePad.SetConstant(-10)
imagePad.SetOutputWholeExtent(imagePadExtent[0], (imagePadExtent[1]+int(200)), imagePadExtent[2],
                                imagePadExtent[3], imagePadExtent[4], imagePadExtent[5]+int(50))
imagePad.Update()


imagePad2 = vtk.vtkImageConstantPad()
imagePad2.SetInput(blend3.GetOutput())
imagePad2.SetConstant(0)
imagePad2.SetOutputWholeExtent(imagePadExtent[0], (imagePadExtent[1]+int(200)), imagePadExtent[2],
                                imagePadExtent[3], imagePadExtent[4], imagePadExtent[5]+int(50))
imagePad2.Update()


#Debugging
#imageBounds = imagePad.GetOutput().GetBounds()
#Log ("Image bounds Padded:", (" %.4f"*6) % imageBounds)

imageCap = vtk.vtkImageThreshold()
imageCap.SetInput(imagePad2.GetOutput())
imageCap.ThresholdBetween(1,252)
imageCap.SetInValue(0)
imageCap.SetOutValue(254)
imageCap.Update()


# -------------------------------------------------------------------------
# DEBUGGING Write out cropped and filtered aim
#outputAimFileTest = os.path.splitext(inputAimFile)[0] + "_LARGER.aim"
#writer = vtkn88.vtkn88AIMWriter()
#writer.SetInput (imagePad2.GetOutput())
#writer.SetFileName (outputAimFileTest)
#writer.Write()
# -------------------------------------------------------------------------


# Convert the 3D image data from the AIM file to hexagonal cells

hexa = vtkn88.vtkn88ImageToMesh()
hexa.SetInput(imagePad2.GetOutput())
hexa.Update()

materialTable = vtkn88.vtkn88MaterialTable()

boxBounds = imageCap.GetOutput().GetBounds()
tempBound = boxBounds[0]

Log ("Constructing a finite element model")
generator = vtkn88.vtkn88FiniteElementModelGenerator()
generator.SetInputConnection (0, hexa.GetOutputPort())
generator.SetInput(1, materialTable)
generator.Update()
modelTemp = generator.GetOutput()

# Find all the visible nodes.
Log ("Finding visible nodes.")
visibleNodesIds = vtk.vtkIdTypeArray()


Log ("Finding nodes on femoral shaft for PMMA cap")

vtkn88.vtkn88NodeSetsByGeometry.FindNodesOnVisibleSurface (
  visibleNodesIds,
  modelTemp,
  normalShaftVector,
  -1)
Log ("Found %d visible exterior femoral shaft nodes." % visibleNodesIds.GetNumberOfTuples())


# Add this list of nodes to the model with the name "BONE TOP VISIBLE NODES"
modelTemp.AddNodeSet (visibleNodesIds, "BONE SHAFT PMMA NODES")

# We're going to need these points as vtkPolyData, for one to write them
# out, but also to further filter based on geometry, so let's grab
# them now as vtkPolyData
visibleBoneVertices = modelTemp.DataSetFromSelection("BONE SHAFT PMMA NODES")

# Now we filter this node set by maximum depth, measured from the highest
# surface node with the correct material that we found.
# Find highest surface point:
Log ("Filtering node set by depth.")
visibleBoneVertices.ComputeBounds()
visibleNodesBounds = visibleBoneVertices.GetBounds()

Log ("Bounds of visible bone nodes:", ("%.4f" + " %.4f"*5) % visibleNodesBounds)

boxBounds = (visibleNodesBounds[1],
		visibleNodesBounds[1],
		visibleNodesBounds[2],
		visibleNodesBounds[3],
		visibleNodesBounds[4],
		visibleNodesBounds[5]) 
	
Log ("Limiting to box bounds:", ("%.4f" + " %.4f"*5) % boxBounds)
box = vtk.vtkBox()
box.SetBounds (boxBounds)
filter = vtk.vtkExtractGeometry()
filter.SetImplicitFunction (box)
filter.ExtractInsideOn()
filter.ExtractBoundaryCellsOn()
filter.SetInput (0, visibleBoneVertices)
filter.Update()
filteredSurfaceVertices = filter.GetOutput()

filteredSurfaceVertices.ComputeBounds()
filteredVisibleBounds = filteredSurfaceVertices.GetBounds()
Log ("Bounds of visible filtered bone nodes:",
     ("%.4f" + " %.4f"*5) % filteredVisibleBounds)

translationZ = tan(float(10)/57.2958)*(filteredVisibleBounds[0]-tempBound)
#print "Z translation is: %.3f" % (translationZ)

boxBounds2 = (filteredVisibleBounds[0]-5,
                  filteredVisibleBounds[1]+157.48,
                  filteredVisibleBounds[2]-8,
                  filteredVisibleBounds[3]+8,
                  filteredVisibleBounds[4]-15-translationZ,
                  filteredVisibleBounds[5]+5-translationZ)


heightShaftCap = (filteredVisibleBounds[5]+5)-(filteredVisibleBounds[4]-10)

transformCap = vtk.vtkTransform()
transformCap.RotateY(float(10))

Log ("Created BOX:",
    ("%.4f" + " %.4f"*5) % boxBounds2)
box = vtk.vtkBox()
box.SetBounds (boxBounds2)
box.SetTransform(transformCap)

stencilData = vtk.vtkImplicitFunctionToImageStencil()
stencilData.SetInput(box)
stencilData.SetInformationInput(imagePad2.GetOutput())

stencil = vtk.vtkImageStencil()
stencil.SetInput(imageCap.GetOutput())
stencil.SetBackgroundValue(0)
stencil.SetStencil(stencilData.GetOutput())
stencil.Update()

image5.Update()

blend4 = vtk.vtkImageMathematics()
blend4.SetOperationToAdd()
blend4.SetInput1(imagePad2.GetOutput())
blend4.SetInput2(stencil.GetOutput())
blend4.Update()

blend5 = vtk.vtkImageMathematics()
blend5.SetOperationToReplaceCByK()
blend5.SetConstantC(255)
blend5.SetConstantK(0)
blend5.SetInput1(blend4.GetOutput())
blend5.Update()


finalImage = vtk.vtkImageThreshold()
finalImage.SetInput(blend5.GetOutput())
finalImage.ThresholdByLower(254)
finalImage.SetOutValue(200)
finalImage.Update()
'''

# -------------------------------------------------------------------------
# Write out the result

print "Writing to", outputAimFile
writer = vtkn88.vtkn88AIMWriter()
writer.SetInput (image2)  # REMEMBER TO CHANGE THIS WHEN ADDING SHAFT CAP
writer.SetFileName (outputAimFile)
writer.Write()

# -------------------------------------------------------------------------
# Read calibrated data

Log ("Reading calibrated data.")
reader = vtkn88.vtkn88AIMReader()
reader.SetFileName (outputAimFile)
reader.DataOnCellsOn()
reader.Update()
image = reader.GetOutput()
Log ("Read %d points from AIM file." % image.GetNumberOfPoints())
imageBounds = image.GetBounds()
Log ("Image bounds:", (" %.4f"*6) % imageBounds)


# -------------------------------------------------------------------------
# Convert the 3D image data from the AIM file to hexagonal cells

Log ("Converting to hexagonal cells.")
hexa = vtkn88.vtkn88ImageToMesh()
hexa.SetInputConnection (reader.GetOutputPort())
hexa.Update()
Log ("Generated %d hexahedrons" % hexa.GetOutput().GetNumberOfCells())

outputModelFile = os.path.splitext(inputAimFile)[0] + "_model.vtu"

writer = vtk.vtkXMLUnstructuredGridWriter()
#filename = "model_geometry.vtu"
writer.SetFileName (outputModelFile)
writer.SetInput (hexa.GetOutput())
Log ("Writing nodes to " + outputModelFile)
writer.Write()

# -------------------------------------------------------------------------
# Assigning material properties
# 0 = homogenous E = modulus specified below
#
# modules values in MPa
#
# 1 = scaled: Morgan and Keavney 2003 J Biomech
#	E = 6850*density^1.49
#
# 2 = scaled: Peng 2006 Med Eng Phy
#	Ecort = 2065*density^3.09
#	Etrab = 1904*density^1.64
#       	where cort is defined as density > 1.0g/cm3 
#
# 3 = scaled: Keyak 1998 J Biomech, Bessho 2007 J Biomech
#		0<p<=0.27   	E = 33900*p^2.20
#		0.27<p<=06 	    E = 5307*p + 469
#	    0.6<p      	    E = 10200*p^2.01
#
# 4 = scaled trab, homogenous cort: Varghese/Hangartener 2011 J Biomech
#	Ecort = 16500 MPa
#	Etrab = 3 * density ^ 1.8 	density  (g/cm3)
#
# 5 = scaled: Keller 1994 - ash density and valid for trab and cort
#	E = 10500*density^2.29
#



Log ("Creating material table.")
materialTable = vtkn88.vtkn88MaterialTable()
pmmaMaterial = vtkn88.vtkn88LinearIsotropicMaterial()
pmmaMaterial.SetYoungsModulus(2500)
pmmaMaterial.SetPoissonsRatio(0.4)
materialTable.AddMaterial(253, pmmaMaterial)


shaftHolderMaterial = vtkn88.vtkn88LinearIsotropicMaterial()
shaftHolderMaterial.SetYoungsModulus(50000)
shaftHolderMaterial.SetPoissonsRatio(0.3)
materialTable.AddMaterial(254, shaftHolderMaterial)


if (modelType == 0):
    
    for i in range(1,numberE):
        boneMaterial = vtkn88.vtkn88LinearIsotropicMaterial()
        boneMaterial.SetYoungsModulus(modulus)
        boneMaterial.SetPoissonsRatio(poisson)
        materialTable.AddMaterial(i, boneMaterial)

elif (modelType == 1):
  for i in range(1,numberE-1):
    boneMaterial = vtkn88.vtkn88LinearIsotropicMaterial()
    # take back to density units
    value = (i / ((numberE-2.0)/(maxImage - minImage)) + minImage)/1000
    #print "Value is: %.1f %.4f" % (i, value)
    valueMod = 6850*(value**1.49)
    #print "Value is: %.1f %.4f" % (i, valueMod)
    boneMaterial.SetYoungsModulus(valueMod)
    boneMaterial.SetPoissonsRatio(poisson)
    materialTable.AddMaterial(i, boneMaterial)

elif (modelType == 2):
  for i in range(1,numberE-1):
        boneMaterial = vtkn88.vtkn88LinearIsotropicMaterial()
	# take back to density units
        value = (i / ((numberE-2.0)/(maxImage - minImage)) + minImage)/1000
        if (value > 1.0):
            #print "Value is: %.1f %.4f" % (i, value)
            valueMod = 2065*(value**3.09)
            #print "Value is: %.1f %.4f" % (i, valueMod)
            boneMaterial.SetYoungsModulus(valueMod)
            boneMaterial.SetPoissonsRatio(poisson)
            materialTable.AddMaterial(i, boneMaterial)
        else:
            #print "Value is: %.1f %.4f" % (i, value)
            valueMod = 1904*(value**1.64)
            #print "Value is: %.1f %.4f" % (i, valueMod)
            boneMaterial.SetYoungsModulus(valueMod)
            boneMaterial.SetPoissonsRatio(poisson)
            materialTable.AddMaterial(i, boneMaterial)

elif (modelType == 3):	
    for i in range(1,numberE-1):
        boneMaterial = vtkn88.vtkn88LinearIsotropicMaterial()
        # take back to density units
        value = (i / ((numberE-2.0)/(maxImage - minImage)) + minImage)/1000
        if (value > 0.60):
            #print "Value is: %.1f %.4f" % (i, value)
            valueMod = 10200*(value**2.01)
            #print "1Value is: %.1f %.4f" % (i, valueMod)
            boneMaterial.SetYoungsModulus(valueMod)
            boneMaterial.SetPoissonsRatio(poisson)
            materialTable.AddMaterial(i, boneMaterial)
            
        elif (value < 0.27):
            #print "Value is: %.1f %.4f" % (i, value)
            valueMod = 33900*(value**2.20)
            #print "2Value is: %.1f %.4f" % (i, valueMod)
            boneMaterial.SetYoungsModulus(valueMod)
            boneMaterial.SetPoissonsRatio(poisson)
            materialTable.AddMaterial(i, boneMaterial)
        else:
            #print "Value is: %.1f %.4f" % (i, value)
            valueMod = 5307*value+469
            #print "3Value is: %.1f %.4f" % (i, valueMod)
            boneMaterial.SetYoungsModulus(valueMod)
            boneMaterial.SetPoissonsRatio(poisson)
            materialTable.AddMaterial(i, boneMaterial)
                
elif (modelType == 4):	
    for i in range(1,numberE-1):
        boneMaterial = vtkn88.vtkn88LinearIsotropicMaterial()
        # take back to density units   
        value = (i / ((numberE-2.0)/(maxImage - minImage)) + minImage)/1000
        if (value > 1.19):
            #print "Value is: %.1f %.4f" % (i, value)
            valueMod = 16500
            #print "Value is: %.1f %.4f" % (i, valueMod)
            boneMaterial.SetYoungsModulus(valueMod)
            boneMaterial.SetPoissonsRatio(poisson)
            materialTable.AddMaterial(i, boneMaterial)
        else: 
            #print "Value is: %.1f %.4f" % (i, value)
            valueMod = 3000*(value**1.8)
            #print "Value is: %.1f %.4f" % (i, valueMod)
            boneMaterial.SetYoungsModulus(valueMod)
            boneMaterial.SetPoissonsRatio(poisson)
            materialTable.AddMaterial(i, boneMaterial)
   
else:
    for i in range(1,127):
      boneMaterial = vtkn88.vtkn88LinearIsotropicMaterial()
      # take back to density units
      value = (i / ((126)/(maxImageTrab - minImageTrab)) + minImageTrab)/1000
      #print "Value is: %.1f %.4f" % (i, value)
      valueMod = 10500*(value**2.29)
      #print "Value is: %.1f %.4f" % (i, valueMod)
      boneMaterial.SetYoungsModulus(valueMod)
      boneMaterial.SetPoissonsRatio(poisson)
      materialTable.AddMaterial(i, boneMaterial)
    for i in range(127,253):
      boneMaterial = vtkn88.vtkn88LinearIsotropicMaterial()
      # take back to density units
      value = ((i-126) / ((126)/(maxImageCort - minImageCort)) + minImageCort)/1000
      #print "Value is: %.1f %.4f" % (i, value)
      valueMod = 10500*(value**2.29)
      #print "Value is: %.1f %.4f" % (i, valueMod)
      boneMaterial.SetYoungsModulus(valueMod)
      boneMaterial.SetPoissonsRatio(poisson)
      materialTable.AddMaterial(i, boneMaterial)


# -------------------------------------------------------------------------
# We pass the data through vtkMeshGenerator to create a vtkMeshModel object,
# but we don't specify any particular FE test, as we are going to manually
# add constraints.

Log ("Constructing a finite element model")
generator = vtkn88.vtkn88FiniteElementModelGenerator()
generator.SetInputConnection (0, hexa.GetOutputPort())
generator.SetInput(1, materialTable)
generator.SetModelSourceDescription (inputAimFile)
generator.Update()
model = generator.GetOutput()
model.ComputeBounds()
bounds = model.GetBounds()
Log ("Model bounds:", (" %.4f"*6) % bounds)
	 

# Set normal vectors for femoral head and greater trochanger
normalHeadVector  = (0,0,1)
normalTrochVector = (0,0,-1)
normalShaftVector = (1,0,0)

# Surface to search for voxels on end of shaft
zShaftModelSurface = bounds[1]

# --------------------------------------------------------------------------
# Constraint 1: Apply a fixed constraint to the femoral shaft

Log ("Adding the SHAFT constraint.")

# Find all the visible nodes.
Log ("Finding visible nodes.")
visibleNodesIds = vtk.vtkIdTypeArray()

vtkn88.vtkn88NodeSetsByGeometry.FindNodesOnVisibleSurface(
                                                          visibleNodesIds,
                                                          model,
                                                          normalShaftVector,
                                                          -1)

model.AddNodeSet (visibleNodesIds, "SHAFT VISIBLE NODES")
Log ("Found %d visible nodes." % visibleNodesIds.GetNumberOfTuples())

# We're going to need these points as vtkPolyData, for one to write them
# out, but also to further filter based on geometry, so let's grab
# them now as vtkPolyData
visibleBoneVertices = model.DataSetFromSelection("SHAFT VISIBLE NODES")

# Now save these nodes to a file so that we can examine them with ParaView, etc...
writer = vtk.vtkXMLPolyDataWriter()
visibleBoneNodesFile = "visible_bone_nodes_shaft_FAL_ISO.vtp"
writer.SetFileName (visibleBoneNodesFile)
writer.SetInput (visibleBoneVertices)
Log ("Writing nodes to %s" % visibleBoneNodesFile)
#writer.Write()

# Now we filter this node set by maximum depth, measured from the highest
# surface node with the correct material that we found.
# Find highest surface point:

Log ("Filtering node set by depth.")

visibleBoneVertices.ComputeBounds()
visibleNodesBounds = visibleBoneVertices.GetBounds()
Log ("Bounds of visible bone nodes:",
    ("%.4f" + " %.4f"*5) % visibleNodesBounds)


#midZ = int(cos(float(10)/57.2958)*(heightShaftCap/2))

boxBounds = (visibleNodesBounds[1],
             visibleNodesBounds[1],
             visibleNodesBounds[2],
             visibleNodesBounds[3],
             visibleNodesBounds[4],
             visibleNodesBounds[5])

Log ("Limiting to box bounds:",
     ("%.4f" + " %.4f"*5) % boxBounds)
box = vtk.vtkBox()
box.SetBounds (boxBounds)
filter = vtk.vtkExtractGeometry()
filter.SetImplicitFunction (box)
filter.ExtractInsideOn()
filter.ExtractBoundaryCellsOn()
filter.SetInput (0, visibleBoneVertices)
filter.Update()
filteredSurfaceVertices = filter.GetOutput()
Log ("Found %d nodes in bounding box." % filteredSurfaceVertices.GetNumberOfCells())
filteredSurfaceVertices.ComputeBounds()
filteredSurfaceVerticesBounds = filteredSurfaceVertices.GetBounds()

# Save to file so we can examine in ParaView, etc...
depthFilteredBoneNodesFile = os.path.splitext(inputAimFile)[0] + "_nodes_shaft.vtu"
writer = vtk.vtkXMLUnstructuredGridWriter()
#depthFilteredBoneNodesFile = "depth_filtered_bone_nodes_troch.vtu"
writer.SetFileName (depthFilteredBoneNodesFile)
writer.SetInput (filteredSurfaceVertices)
#Log ("Writing nodes to %s" % depthFilteredBoneNodesFile)
#writer.Write()

nodeSet = filteredSurfaceVertices.GetPointData().GetPedigreeIds()
model.AddNodeSet (nodeSet, "SHAFT VISIBLE NODES")

#set displacement constraint for all axis (ie fixed in all directions)
model.CreateDisplacementConstraint ("SHAFT VISIBLE NODES", 0, 0, "SHAFT SURFACE CONSTRAINT");
model.CreateDisplacementConstraint ("SHAFT VISIBLE NODES", 1, 0, "SHAFT SURFACE CONSTRAINT");
#model.CreateDisplacementConstraint ("SHAFT VISIBLE NODES", 2, 0, "SHAFT SURFACE CONSTRAINT");

# Now get these nodes (with point coordinates) and save them to a file
# so that we can examine them with ParaView, etc...
nodesFileShaft = os.path.splitext(inputAimFile)[0] + "_nodes_shaft.vtu"
verticesShaft = model.DataSetFromSelection ("SHAFT VISIBLE NODES")
writer = vtk.vtkXMLUnstructuredGridWriter()
#nodesFileShaft = "shaft_nodes.vtp"
writer.SetFileName (nodesFileShaft)
writer.SetInput (verticesShaft)
Log ("Writing nodes to " + nodesFileShaft)
writer.Write()

# --------------------------------------------------------------------------
# Constraint 2: Apply a displacement to the greater trochanter.
#
#
# We want to find the bone nodes that you would be able to see if
# you looked up from the greater trochanter.
# Further, we are going to limit the depth of nodes that we accept, where
# the depth is measured from the highest such node that we see

Log ("Adding the TROCHANTER BONE SURFACE constraint.")

# Find all the visible nodes.
Log ("Finding visible nodes.")
visibleNodesIds = vtk.vtkIdTypeArray()

vtkn88.vtkn88NodeSetsByGeometry.FindNodesOnVisibleSurface(
                                                          visibleNodesIds,
                                                          model,
                                                          normalTrochVector,
                                                          -1)

model.AddNodeSet (visibleNodesIds, "BONE BOTTOM VISIBLE NODES")
Log ("Found %d visible nodes." % visibleNodesIds.GetNumberOfTuples())



# We're going to need these points as vtkPolyData, for one to write them
# out, but also to further filter based on geometry, so let's grab
# them now as vtkPolyData
visibleBoneVertices = model.DataSetFromSelection("BONE BOTTOM VISIBLE NODES")

# Now save these nodes to a file so that we can examine them with ParaView, etc...
writer = vtk.vtkXMLPolyDataWriter()
visibleBoneNodesFile = "visible_bone_nodes_troch.vtp"
writer.SetFileName (visibleBoneNodesFile)
writer.SetInput (visibleBoneVertices)
Log ("Writing nodes to %s" % visibleBoneNodesFile)
#writer.Write()

# Now we filter this node set by maximum depth, measured from the highest
# surface node with the correct material that we found.
# Find highest surface point:

Log ("Filtering node set by depth.")

visibleBoneVertices.ComputeBounds()
visibleNodesBounds = visibleBoneVertices.GetBounds()
Log ("Bounds of visible bone nodes:",
   ("%.4f" + " %.4f"*5) % visibleNodesBounds)



boxBounds = (visibleNodesBounds[0],
		visibleNodesBounds[1],
		visibleNodesBounds[2],
		visibleNodesBounds[3],
		visibleNodesBounds[4],
		visibleNodesBounds[4]+trochConstraintMaxDepth) 
	
			 
Log ("Limiting to box bounds:",
   ("%.4f" + " %.4f"*5) % boxBounds)
box = vtk.vtkBox()
box.SetBounds (boxBounds)
filter = vtk.vtkExtractGeometry()
filter.SetImplicitFunction (box)
filter.ExtractInsideOn()
filter.ExtractBoundaryCellsOn()
filter.SetInput (0, visibleBoneVertices)
filter.Update()
filteredSurfaceVertices = filter.GetOutput()
Log ("Found %d nodes in bounding box." % filteredSurfaceVertices.GetNumberOfCells())
filteredSurfaceVertices.ComputeBounds()
filteredSurfaceVerticesBounds = filteredSurfaceVertices.GetBounds()

# Save to file so we can examine in ParaView, etc...
depthFilteredBoneNodesFile = os.path.splitext(inputAimFile)[0] + "_nodes_troch.vtu"
writer = vtk.vtkXMLUnstructuredGridWriter()
#depthFilteredBoneNodesFile = "depth_filtered_bone_nodes_troch.vtu"
writer.SetFileName (depthFilteredBoneNodesFile)
writer.SetInput (filteredSurfaceVertices)
Log ("Writing nodes to %s" % depthFilteredBoneNodesFile)
writer.Write()

nodeSet = filteredSurfaceVertices.GetPointData().GetPedigreeIds()
model.AddNodeSet (nodeSet, "BONE BOTTOM VISIBLE NODES")

#model.CreateDisplacementConstraint ("BONE BOTTOM VISIBLE NODES", 0, 0, "TROCHANTER SURFACE CONSTRAINT");
#model.CreateDisplacementConstraint ("BONE BOTTOM VISIBLE NODES", 1, 0, "TROCHANTER SURFACE CONSTRAINT");
model.CreateDisplacementConstraint ("BONE BOTTOM VISIBLE NODES",2, trochDisplacement,"TROCH DISPLACEMENT");



# --------------------------------------------------------------------------
# Constraint 3: Apply a constraint to the top of the femoral head
#
# We want to find the bone nodes that you
# would be able to see if you looked down upon the image from above.
# Further, we are going to limit the depth of nodes that we accept, where
# the depth is measured from the highest such node that we see

Log ("Adding the BONE HEAD TOP SURFACE constraint.")

vtkn88.vtkn88NodeSetsByGeometry.FindNodesOnVisibleSurface (
  visibleNodesIds,
  model,
  normalHeadVector,
  -1)
Log ("Found %d visible exterior nodes." % visibleNodesIds.GetNumberOfTuples())

# Add this list of nodes to the model with the name "BONE TOP VISIBLE NODES"
model.AddNodeSet (visibleNodesIds, "BONE TOP VISIBLE NODES")

# We're going to need these points as vtkPolyData, for one to write them
# out, but also to further filter based on geometry, so let's grab
# them now as vtkPolyData
visibleBoneVertices = model.DataSetFromSelection("BONE TOP VISIBLE NODES")

# Now save these nodes to a file so that we can examine them with ParaView, etc...
writer = vtk.vtkXMLPolyDataWriter()
visibleBoneNodesFile = "visible_bone_nodes_head.vtp"
writer.SetFileName (visibleBoneNodesFile)
writer.SetInput (visibleBoneVertices)
Log ("Writing nodes to %s" % visibleBoneNodesFile)
#writer.Write()

# Now we filter this node set by maximum depth, measured from the highest
# surface node with the correct material that we found.
# Find highest surface point:

Log ("Filtering node set by depth.")

visibleBoneVertices.ComputeBounds()
visibleNodesBounds = visibleBoneVertices.GetBounds()
Log ("Bounds of visible bone nodes:",
   ("%.4f" + " %.4f"*5) % visibleNodesBounds)

boxBounds = (visibleNodesBounds[0],
		visibleNodesBounds[0]+100,
		visibleNodesBounds[2],
		visibleNodesBounds[3],
		visibleNodesBounds[5]- ((visibleNodesBounds[5]-visibleNodesBounds[4])/2),
		visibleNodesBounds[5]) 

	
Log ("Limiting to box bounds:",
   ("%.4f" + " %.4f"*5) % boxBounds)
box = vtk.vtkBox()
box.SetBounds (boxBounds)
filter = vtk.vtkExtractGeometry()
filter.SetImplicitFunction (box)
filter.ExtractInsideOn()
filter.ExtractBoundaryCellsOn()
filter.SetInput (0, visibleBoneVertices)
filter.Update()
filteredSurfaceVertices = filter.GetOutput()

filteredSurfaceVertices.ComputeBounds()
visibleNodesBounds2 = filteredSurfaceVertices.GetBounds()
Log ("Bounds of visible bone nodes:",
     ("%.4f" + " %.4f"*5) % visibleNodesBounds2)

boxBounds2 = (visibleNodesBounds2[0],
              visibleNodesBounds2[1],
              visibleNodesBounds2[2],
              visibleNodesBounds2[3],
              visibleNodesBounds2[5]-headConstraintMaxDepth,
              visibleNodesBounds2[5]) 

Log ("Limiting to box bounds:",
     ("%.4f" + " %.4f"*5) % boxBounds2)
box2 = vtk.vtkBox()
box2.SetBounds (boxBounds2)
filter2 = vtk.vtkExtractGeometry()
filter2.SetImplicitFunction (box2)
filter2.ExtractInsideOn()
filter2.ExtractBoundaryCellsOn()
filter2.SetInput (0, filteredSurfaceVertices)
filter2.Update()
filteredSurfaceVertices2 = filter2.GetOutput()

Log ("Found %d nodes in bounding boxes." % filteredSurfaceVertices2.GetNumberOfCells())
filteredSurfaceVertices2.ComputeBounds()
filteredSurfaceVerticesBounds = filteredSurfaceVertices2.GetBounds()

# Save to file so we can examine in ParaView, etc...
depthFilteredBoneNodesFile = os.path.splitext(inputAimFile)[0] + "_nodes_head.vtu"
writer = vtk.vtkXMLUnstructuredGridWriter()
#depthFilteredBoneNodesFile = "depth_filtered_bone_nodes_head.vtu"
writer.SetFileName (depthFilteredBoneNodesFile)
writer.SetInput (filteredSurfaceVertices2)
Log ("Writing nodes to %s" % depthFilteredBoneNodesFile)
writer.Write()

nodeSet = filteredSurfaceVertices2.GetPointData().GetPedigreeIds()
model.AddNodeSet (nodeSet, "BONE TOP VISIBLE NODES")



# Create a constraint that is applied to BONE TOP VISIBLE NODES.
model.CreateDisplacementConstraint ("BONE TOP VISIBLE NODES", 2, 0, "HEAD TOP CONSTRAINT");


# --------------------------------------------------------------------------
# Constraint 4: Define node set in order to determine load sharing

Log ("Finding load sharing nodes")


transform = vtk.vtkTransform()


#################
#####FIX THIS TO use user specified
#################
transform.RotateY(float(40))


#################
#####FIX THIS TO be user specified
#################
movez = (66-visibleNodesBounds[4])-35
movex = (37-visibleNodesBounds[0])-20

transform.Translate (movex, 0, movez)

#################
#####FIX THIS TO BE AUTOMATICALLY SELECTED, it may be okay as is
#################
boxBounds = (35,125,-60,30,0,21)

#was 10 to 11 for z

box = vtk.vtkBox()
box.SetBounds (boxBounds)
box.SetTransform(transform)

filter = vtk.vtkExtractGeometry()
filter.SetImplicitFunction (box)
filter.ExtractInsideOn()
filter.ExtractBoundaryCellsOn()
filter.SetInput (model)
filter.Update()
filteredSurfaceVertices = filter.GetOutput()
Log ("Found %d nodes in bounding box." % filteredSurfaceVertices.GetNumberOfCells())
filteredSurfaceVertices.ComputeBounds()
filteredSurfaceVerticesBounds = filteredSurfaceVertices.GetBounds()

# Save to file so we can examine in ParaView, etc...
depthFilteredBoneNodesFile = os.path.splitext(inputAimFile)[0] + "_nodes_neck.vtu"
writer = vtk.vtkXMLUnstructuredGridWriter()
#depthFilteredBoneNodesFile = "depth_filtered_bone_nodes_neck.vtu"
writer.SetFileName (depthFilteredBoneNodesFile)
writer.SetInput (filteredSurfaceVertices)
#Log ("Writing nodes to %s" % depthFilteredBoneNodesFile)
#writer.Write()

nodeSet = filteredSurfaceVertices.GetPointData().GetPedigreeIds()
model.AddNodeSet (nodeSet, "NECK NODES")

# Now get these nodes (with point coordinates) and save them to a file
# so that we can examine them with ParaView, etc...
nodesFileNeck = os.path.splitext(inputAimFile)[0] + "_nodes_neck.vtu"
verticesNeck = model.DataSetFromSelection ("NECK NODES")
writer = vtk.vtkXMLUnstructuredGridWriter()
#nodesFileNeck = "neck_nodes.vtp"
writer.SetFileName (nodesFileNeck)
writer.SetInput (verticesNeck)
Log ("Writing nodes to " + nodesFileNeck)
writer.Write()


# --------------------------------------------------------------------------
# Set the node sets that will be used for post-processing
info = model.GetInformation()
postProcessingNodeSetsKey = vtkn88.vtkn88FiniteElementRun.POST_PROCESSING_NODE_SETS()
postProcessingNodeSetsKey.Append (info, "BONE BOTTOM VISIBLE NODES")
postProcessingNodeSetsKey.Append (info, "BONE TOP VISIBLE NODES")
postProcessingNodeSetsKey.Append (info, "SHAFT VISIBLE NODES")
postProcessingNodeSetsKey.Append (info, "NECK NODES")

# --------------------------------------------------------------------------
# Write out faim file

Log ("Writing file %s" % outputFaimFile)
writer = vtkn88.vtkn88FAIMInputWriter()
writer.SetInput (model)
writer.SetFileName (outputFaimFile)
writer.SetIterationLimit(10000)
writer.SetConvergenceTolerance(0.0001)
writer.Update()

Log ("Done.")


