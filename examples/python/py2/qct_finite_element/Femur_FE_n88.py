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

if (len(sys.argv) != 8):
  print "Usage: vtkpython Femur_FE example.conf NORM_001.AIM cortMask.vtk 1.22 -3.34 58.7"
  sys.exit(1)
configFile = sys.argv[1]
inputAimFile = sys.argv[2]
inputCortMaskFile = sys.argv[3]
calibrationSlope = sys.argv[4]
calibrationIntercept = sys.argv[5]
angle = sys.argv[6]
angleShaft = sys.argv[7]

outputFaimFile = os.path.splitext(inputAimFile)[0] + "_FAL_ISO.inp"

# Read in configuration file.
print "Reading configuration file", configFile
# Here we are actually executing it as python code.
execfile (configFile)

# Print out values that we read in.  This also has the effect of causing
# this script to die if configuration values are missing (which is a good thing).

print "input file                            :", inputAimFile
print "output file                           :", outputFaimFile
print "cortical mask                         :", inputCortMaskFile
print "calibration slope                     :", calibrationSlope
print "calibration intercept                 :", calibrationIntercept
print "angle                                 :", angle
print "shaft angle                           :", angleShaft
print "model type                            :", modelType
print "modulus                               :", modulus
print "Poisson's ratio                       :", poisson
print "head displacement                     :", headDisplacement
print "head constraint max depth             :", headConstraintMaxDepth
print "trochanter contraint max depth        :", trochConstraintMaxDepth

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

outputAimFile = os.path.splitext(inputAimFile)[0] + "_CAL_FAL_ISO.aim"

tempInputAimFile = "M0001_0625.aim"


Log ("Reading input data and masks.")
reader = vtkn88.vtkn88AIMReader()
#reader.DataOnCellsOn()
reader.SetFileName (tempInputAimFile)
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
transform.RotateZ(float(angle))
transform.RotateY(float(angleShaft))

# Find associated 4x4 matrix
matrix = vtk.vtkMatrix4x4()
matrix = transform.GetMatrix()

# Apply matrix to image with cubic interpolation
#rescale to ???? mm isotropic voxels
reslice = vtk.vtkImageReslice()
reslice.SetInput(stencil.GetOutput())
reslice.SetResliceAxes(matrix)
reslice.SetInterpolationModeToCubic()
reslice.SetOutputSpacing(1.0, 1.0, 1.0)
reslice.Update()

#clip to have smooth surface on shaft end and leave only 6cm of shaft

imageClip = reslice.GetOutput()
Log ("Read %d points from AIM file." % imageClip.GetNumberOfPoints())
imageBoundsClip = imageClip.GetBounds()
Log ("Image bounds:",
	 ("%.4f" + " %.4f"*5) % imageBoundsClip)



clip = vtk.vtkExtractVOI()
clip.SetInput(reslice.GetOutput())
clip.Update()
wholeVOI = clip.GetVOI()
clip.SetVOI(wholeVOI[0], wholeVOI[1], wholeVOI[2], wholeVOI[3], wholeVOI[4]+56, wholeVOI[5])
clip.Update()

imageClip = clip.GetOutput()
Log ("Read %d points from AIM file." % imageClip.GetNumberOfPoints())
imageBoundsClip = imageClip.GetBounds()
Log ("Image bounds:",
	 ("%.4f" + " %.4f"*5) % imageBoundsClip)


# Filter with gaussian  
gauss = vtk.vtkImageGaussianSmooth()
gauss.SetInput(clip.GetOutput())
gauss.SetStandardDeviations(2,2,2)
gauss.SetRadiusFactors(0.5,0.5,0.5)
gauss.Update()

image2 = gauss.GetOutput()
imageBounds2 = image2.GetBounds()

Log ("Read %d points from AIM file." % image2.GetNumberOfPoints())
imageBounds2 = image2.GetBounds()
Log ("Image bounds:",
	 ("%.4f" + " %.4f"*5) % imageBounds2)


# -------------------------------------------------------------------------
# Write out cropped and filtered aim

outputAimFilePre = os.path.splitext(inputAimFile)[0] + "_PRE_FAL_ISO.aim"

print "Writing to", outputAimFilePre
writer = vtkn88.vtkn88AIMWriter()
#writer.DebugOn()
writer.SetInput (image2)
#writer.NewProcessingLogOff()
#writer.SetProcessingLog (log)
#writer.CalculatePositionFromOriginOn()
writer.SetFileName (outputAimFilePre)
writer.Write()


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
# Debugging
#print scalars
#print "****Scalar type: ", image.GetScalarType()

# As a check, save this vtkImageData in VTK format.
#print "Saving vtkImageData as image.vti"
#writer = vtk.vtkXMLImageDataWriter()
#writer.SetInput (image)
#writer.SetFileName ("image.vti")
#writer.Write()


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

outputModelFile = os.path.splitext(inputAimFile)[0] + "_model_FAL_ISO.vtu"

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

Log ("Creating material table.")
materialTable = vtkn88.vtkn88MaterialTable()

if (modelType == 0):
    boneMaterial = vtkn88.vtkn88IsotropicMaterial()
    for i in range(1,127):
        boneMaterial.SetYoungsModulus(modulus)
        boneMaterial.SetPoissonsRatio(poisson)
        materialTable.AddMaterial(i, boneMaterial)

elif (modelType == 1):
	boneMaterial = vtkn88.vtkn88IsotropicMaterial()
	for i in range(1,128):
		# take back to density units
		value = (i / (127.0/(maxImage - minImage)) + minImage)/1000
		#print "Value is: %.1f %.4f" % (i, value)
		valueMod = 6850*(value**1.49)
        #print "Value is: %.1f %.4f" % (i, valueMod)
        boneMaterial.SetYoungsModulus(valueMod)
        boneMaterial.SetPoissonsRatio(poisson)
        materialTable.AddMaterial(i, boneMaterial)

elif (modelType == 2):
    boneMaterial = vtkn88.vtkn88IsotropicMaterial()
    for i in range(1,128):
		# take back to density units
        value = (i / (127.0/(maxImage - minImage)) + minImage)/1000
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
    for i in range(1,128):
        boneMaterial = vtkn88.vtkn88IsotropicMaterial()
        # take back to density units
        value = (i / (127.0/(maxImage - minImage)) + minImage)/1000
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
                
else:
    for i in range(1,128):
        boneMaterial = vtkn88.vtkn88IsotropicMaterial()
        # take back to density units
    
      
        
        #TODO
        #change to use masked regions for classification
        #check these units
    
        
        
    
        value = (i / (127.0/(maxImage - minImage)) + minImage)/1000
        if (value > 1.0): #cortical bone
            #print "Value is: %.1f %.4f" % (i, value)
            valueMod = 16500
            #print "Value is: %.1f %.4f" % (i, valueMod)
            boneMaterial.SetYoungsModulus(valueMod)
            boneMaterial.SetPoissonsRatio(poisson)
            materialTable.AddMaterial(i, boneMaterial)
        else: #trabecular bone
            #print "Value is: %.1f %.4f" % (i, value)
            valueMod = 3000*(value**1.8)
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
normalHeadVector  = (1,0,0)
normalTrochVector = (-1,0,0)
normalNeckVector = (0,0,-1)

# Surface to search for voxels on end of shaft
zShaftModelSurface = bounds[4]


# --------------------------------------------------------------------------
# Determine bone geometry

Log ("Determining bone geometry.")

moi = vtkn88.vtkn88TensorOfInertia()
moi.SetInput (image)
#moi.SetSpecificValue (-1)# later change to not include 127 for PMMA
moi.SetLowerThreshold(1)
moi.SetUpperThreshold(127)
moi.UseThresholdsOn()
Log ("Number of cells belonging to bone: %d" % moi.GetCount())
Log ("Volume of bone: %.2f" % moi.GetVolume())
boneCenterOfMass =  (moi.GetCenterOfMassX(),
					 moi.GetCenterOfMassY(),
					 moi.GetCenterOfMassZ())
Log ("Center of mass of bone: %.5f, %.5f, %.5f" % boneCenterOfMass)
bonePrincipleAxes = vtk.vtkMatrix3x3()
moi.GetPrincipleAxes (bonePrincipleAxes)

# Take 3rd row - that is the 3rd principle axis, which is always the
# principle axis lying closest to the z axis.

boneAxisX = (bonePrincipleAxes.GetElement(0,0),
			 bonePrincipleAxes.GetElement(0,1),
			 bonePrincipleAxes.GetElement(0,2))
Log ("AxisX of bone: %.5f, %.5f, %.5f" % boneAxisX)

boneAxisY = (bonePrincipleAxes.GetElement(1,0),
			 bonePrincipleAxes.GetElement(1,1),
			 bonePrincipleAxes.GetElement(1,2))
Log ("AxisY of bone: %.5f, %.5f, %.5f" % boneAxisY)

boneAxisZ = (bonePrincipleAxes.GetElement(2,0),
			 bonePrincipleAxes.GetElement(2,1),
			 bonePrincipleAxes.GetElement(2,2))
Log ("AxisZ of bone: %.5f, %.5f, %.5f" % boneAxisZ)


# --------------------------------------------------------------------------
# Constraint 1: Apply a fixed constraint to the femoral shaft

Log ("Adding the SHAFT constraint.")

# Find all the visible nodes.
Log ("Finding visible nodes.")
visibleNodesIds = vtk.vtkIdTypeArray()

vtkn88.vtkn88NodeSetsByGeometry.FindNodesOnVisibleSurface(
                                                          visibleNodesIds,
                                                          model,
                                                          normalNeckVector,
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


boxBounds = (visibleNodesBounds[0],
             visibleNodesBounds[1],
             visibleNodesBounds[2],
             visibleNodesBounds[3],
             visibleNodesBounds[4],
             visibleNodesBounds[4])

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
depthFilteredBoneNodesFile = os.path.splitext(inputAimFile)[0] + "_nodes_shaft_FAL_ISO.vtu"
writer = vtk.vtkXMLUnstructuredGridWriter()
#depthFilteredBoneNodesFile = "depth_filtered_bone_nodes_troch.vtu"
writer.SetFileName (depthFilteredBoneNodesFile)
writer.SetInput (filteredSurfaceVertices)
#Log ("Writing nodes to %s" % depthFilteredBoneNodesFile)
#writer.Write()

nodeSet = filteredSurfaceVertices.GetPointData().GetPedigreeIds()
model.AddNodeSet (nodeSet, "SHAFT VISIBLE NODES")

# Create a constraint that is applied to SHAFT END NODES.
# We set all directions to be fixed (note that 1=fixed).
model.SetConstraintFixed ("SHAFT VISIBLE NODES",vtkn88.N88_NODES,1,1,1,"SHAFT SURFACE CONSTRAINT")

# Now get these nodes (with point coordinates) and save them to a file
# so that we can examine them with ParaView, etc...
nodesFileShaft = os.path.splitext(inputAimFile)[0] + "_nodes_shaft_FAL_ISO.vtu"
verticesShaft = model.DataSetFromSelection ("SHAFT VISIBLE NODES")
writer = vtk.vtkXMLUnstructuredGridWriter()
#nodesFileShaft = "shaft_nodes.vtp"
writer.SetFileName (nodesFileShaft)
writer.SetInput (verticesShaft)
Log ("Writing nodes to " + nodesFileShaft)
writer.Write()

# --------------------------------------------------------------------------
# Constraint 2: Apply a fixed constraint to the greater trochanter.
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
visibleBoneNodesFile = "visible_bone_nodes_troch_FAL_ISO.vtp"
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
			visibleNodesBounds[0] + trochConstraintMaxDepth,
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
depthFilteredBoneNodesFile = os.path.splitext(inputAimFile)[0] + "_nodes_troch_FAL_ISO.vtu"
writer = vtk.vtkXMLUnstructuredGridWriter()
#depthFilteredBoneNodesFile = "depth_filtered_bone_nodes_troch.vtu"
writer.SetFileName (depthFilteredBoneNodesFile)
writer.SetInput (filteredSurfaceVertices)
Log ("Writing nodes to %s" % depthFilteredBoneNodesFile)
writer.Write()

nodeSet = filteredSurfaceVertices.GetPointData().GetPedigreeIds()
model.AddNodeSet (nodeSet, "BONE BOTTOM VISIBLE NODES")

# Create a constraint that is applied to BONE BOTTOM VISIBLE NODES.
# We set all directions to be fixed (note that 1=fixed).
model.SetConstraintFixed ("BONE BOTTOM VISIBLE NODES",vtkn88.N88_NODES,1,0,0,"TROCHANTER SURFACE CONSTRAINT")

# --------------------------------------------------------------------------
# Constraint 3: Apply a displacement to the top of the femoral head
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
visibleBoneNodesFile = "visible_bone_nodes_head_FAL_ISO.vtp"
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

boxBounds2 = (visibleNodesBounds2[1] - headConstraintMaxDepth,
              visibleNodesBounds2[1],
              visibleNodesBounds2[2],
              visibleNodesBounds2[3],
              visibleNodesBounds2[4],
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
depthFilteredBoneNodesFile = os.path.splitext(inputAimFile)[0] + "_nodes_head_FAL_ISO.vtu"
writer = vtk.vtkXMLUnstructuredGridWriter()
#depthFilteredBoneNodesFile = "depth_filtered_bone_nodes_head.vtu"
writer.SetFileName (depthFilteredBoneNodesFile)
writer.SetInput (filteredSurfaceVertices2)
Log ("Writing nodes to %s" % depthFilteredBoneNodesFile)
writer.Write()

nodeSet = filteredSurfaceVertices2.GetPointData().GetPedigreeIds()
model.AddNodeSet (nodeSet, "BONE TOP VISIBLE NODES")

# Create a constraint that is applied to the node set.  This constraint
# means displacement of the y axis (0 = x axis) by the value 'displacement'.

model.SetConstraint (
	"BONE TOP VISIBLE NODES",
	0,
    vtkn88.N88_DISPLACEMENT,
    vtkn88.N88_NODES,
    -headDisplacement,
	"HEAD TOP DISPLACEMENT");

# --------------------------------------------------------------------------
# Set the node sets that will be used for post-processing
info = model.GetInformation()
postProcessingNodeSetsKey = vtkn88.vtkn88FiniteElementRun.POST_PROCESSING_NODE_SETS()
postProcessingNodeSetsKey.Append (info, "SHAFT VISIBLE NODES")
postProcessingNodeSetsKey.Append (info, "BONE BOTTOM VISIBLE NODES")
postProcessingNodeSetsKey.Append (info, "BONE TOP VISIBLE NODES")


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
