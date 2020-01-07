from __future__ import division

import os
import sys
import time
import vtk
import vtkski

# Required for manipulating arrays in numpy
import numpy
from numpy.core import *
from vtk.util import numpy_support

# -------------------------------------------------------------------------
#  Configuration

if (len(sys.argv) != 2):
  print "Usage: vtkpython Femur_FE example.conf"
  sys.exit(1)
configFile = sys.argv[1]

# Read in configuration file.
print "Reading configuration file", configFile
# Here we are actually executing it as python code.
execfile (configFile)

# Print out values that we read in.  This also has the effect of causing
# this script to die if configuration values are missing (which is a good thing).

print "input file                            :", inputAimFile
print "output file                           :", outputFaimFile
print "calibration slope                     :", calibrationSlope
print "calibration intercept                 :", calibrationIntercept
print "model type                            :", modelType
print "modulus                               :", modulus
print "Poisson's ratio                       :", poisson
print "head displacement                     :", headDisplacement
print "head contraint max depth              :", headConstraintMaxDepth
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

outputAimFile = os.path.splitext(inputAimFile)[0] + "_CAL.AIM"


Log ("Reading input data.")
reader = vtkski.vtkskiAIMReader()
reader.SetFileName (inputAimFile)
reader.Update()
image = reader.GetOutput()
Log ("Read %d points from AIM file." % image.GetNumberOfPoints())
imageBounds = image.GetBounds()
Log ("Image bounds:",
	 ("%.4f" + " %.4f"*5) % imageBounds)

# -------------------------------------------------------------------------
# Grab the scalar data from the AIM (which is the actual data),
# and convert it to a native numpy array.
# Note: Both the vtkImage and numpy array point to the *same* underlying
# data. No copy is made.
# Caveat: At some (not to distant) future date, AimReader will be
# using the Scalars on the CellData instead of the PointData scalars.

scalars = image.GetPointData().GetScalars()

imageArray = numpy_support.vtk_to_numpy (scalars)

# Convert it to a float array because doing math with 8 bit precision is dopey.
# (Note: This obviously *does* make a copy of the original data)

imageAsFloat = array (imageArray, float)

print "Initial range of data is %.3f to %.3f" % (min(imageAsFloat), max(imageAsFloat))

# -------------------------------------------------------------------------
# Manipulate the numpy array.

# Linear transform
imageAsFloat = calibrationSlope*imageAsFloat + calibrationIntercept
# Threshold away negative values and assume fully mineralized = 1200 mg/ccm

#imageAsFloat *= imageAsFloat>0
#imageAsFloat += 500

numpy.clip(imageAsFloat, 0, 1200, out=imageAsFloat)

minImage = min(imageAsFloat)
maxImage = max(imageAsFloat)
print "After calibration, it has a range of %.3f to %.3f" % (minImage, maxImage)

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
image.GetPointData().SetScalars(scalars)
image.SetScalarTypeToChar()


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
writer = vtkski.vtkskiAIMWriter()
#writer.DebugOn()
writer.SetInput (image)
#writer.NewProcessingLogOff()
#writer.SetProcessingLog (log)
writer.CalculatePositionFromOriginOn()
writer.SetFileName (outputAimFile)
writer.Write()


# -------------------------------------------------------------------------
# Read calibrated data

Log ("Reading calibrated data.")
reader = vtkski.vtkskiAIMReader()
reader.SetFileName (outputAimFile)
reader.Update()
image = reader.GetOutput()
Log ("Read %d points from AIM file." % image.GetNumberOfPoints())
imageBounds = image.GetBounds()
Log ("Image bounds:",
	 ("%.4f" + " %.4f"*5) % imageBounds)


# -------------------------------------------------------------------------
# Convert the 3D image data from the AIM file to hexagonal cells

Log ("Converting to hexagonal cells.")
hexa = vtkski.vtkskiImageToMesh()
hexa.SetInputConnection (reader.GetOutputPort())
hexa.AssignScalarsToCellsOn()
hexa.NodalCoordinatesRelativeToOriginOn()
hexa.HexahedronModeOn()
hexa.Update()
Log ("Generated %d hexahedrons" % hexa.GetOutput().GetNumberOfCells())

outputModelFile = os.path.splitext(inputAimFile)[0] + "_model_geometry.vtu"

writer = vtk.vtkXMLUnstructuredGridWriter()
#filename = "model_geometry.vtu"
writer.SetFileName (outputModelFile)
writer.SetInput (hexa.GetOutput())
Log ("Writing nodes to " + outputModelFile)
writer.Write()

# -------------------------------------------------------------------------
# We pass the data through vtkMeshGenerator to create a vtkMeshModel object,
# but we don't specify any particular FE test, as we are going to manually
# add constraints.

Log ("Constructing a finite element model")
generator = vtkski.vtkskiFiniteElementModelGenerator()
generator.SetInputConnection (hexa.GetOutputPort())
generator.SetTestType (0)
generator.SetModelSourceDescription (inputAimFile)
#generator.SetDensityToModulusConversionModel (0) # 0 is Homminga et al. (2001) J Biomech 34(4):513-517
#Log ("Density to Modulus Model %d." % generator.GetDensityToModulusConversionModel ())
generator.SetIsotropicElasticModulus (modulus)
#generator.SetExponent(exponent)
generator.SetIsotropicPoissonsRatio(poisson) 
#generator.SetEngineeringStrain(-0.04)  
#generator.SetTestingAxis(1) 
# generator.UnevenSurfaceOn()
# generator.SetDirectionPolarity(0)
generator.Update()
model = generator.GetOutput()
model.ComputeBounds()
bounds = model.GetBounds()
Log ("Model bounds:",
	 ("%.4f" + " %.4f"*5) % bounds)
	 
# Set normal vectors for femoral head and greater trochanger
normalHeadVector  = (0,-1,0)
normalTrochVector = (0,1,0)

# Surface to search for voxels on end of shaft
zShaftModelSurface = bounds[5]


# -------------------------------------------------------------------------
# Assigning material properties
# Model type:
# 0 = homogenous E = modulus specified below
# 1 = scaled: E = 6850*density^1.49 (Morgan and Keavney 2003 J Biomech)
# 2 = scaled: Ecort = 2065*density^3.09, Etrab = 1904*density^1.64 
#       where cort is defined as density > 1.0g/cm3 (Peng 2006 Med Eng Phy)
# 3 = scaled: (Keyak 1998 J Biomech, Bessho 2007 J Biomech)
#	0<p<=0.27  - E = 33900*p^2.20
#	0.27<p<=06 - E = 5307*p + 469
#	0.6<p      - E = 10200*p^2.01

if (modelType == 0):
	materialTable = model.GetMaterialTable()
	for i in range(1,127):
		materialTable.SetModulus (i, modulus)

elif (modelType == 1):
	materialTable = model.GetMaterialTable()
	for i in range(1,128):
		# take back to density units
		value = (i / (127.0/(maxImage - minImage)) + minImage)/1000
		#print "Value is: %.1f %.4f" % (i, value)
		valueMod = 6850*(value**1.49)
		#print "Value is: %.1f %.4f" % (i, valueMod)
		materialTable.SetModulus (i, valueMod)

elif (modelType == 2):
	materialTable = model.GetMaterialTable()
	for i in range(1,128):
		# take back to density units
		value = (i / (127.0/(maxImage - minImage)) + minImage)/1000
		if (value > 1.0):
			#print "Value is: %.1f %.4f" % (i, value)
			valueMod = 2065*(value**3.09)
			#print "Value is: %.1f %.4f" % (i, valueMod)
			materialTable.SetModulus (i, valueMod)
		else:
			#print "Value is: %.1f %.4f" % (i, value)
			valueMod = 1904*(value**1.64)
			#print "Value is: %.1f %.4f" % (i, valueMod)
			materialTable.SetModulus (i, valueMod)

else:	
	materialTable = model.GetMaterialTable()
	for i in range(1,128):
		# take back to density units
		value = (i / (127.0/(maxImage - minImage)) + minImage)/1000
		if (value > 0.60):
			#print "Value is: %.1f %.4f" % (i, value)
			valueMod = 10200*(value**2.01)
			#print "1Value is: %.1f %.4f" % (i, valueMod)
			materialTable.SetModulus (i, valueMod)
		elif (value < 0.27):
			#print "Value is: %.1f %.4f" % (i, value)
			valueMod = 33900*(value**2.20)
			#print "2Value is: %.1f %.4f" % (i, valueMod)
			materialTable.SetModulus (i, valueMod)
		else:
			#print "Value is: %.1f %.4f" % (i, value)
			valueMod = 5307*value+469
			#print "3Value is: %.1f %.4f" % (i, valueMod)
			materialTable.SetModulus (i, valueMod)


# --------------------------------------------------------------------------
# Determine bone geometry

Log ("Determining bone geometry.")

moi = vtkski.vtkskiTensorOfInertia()
moi.SetInput (image)
#moi.SetSpecificValue (-1)# later change to not include 127
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

# The following line finds all nodes that have x coordinate (the value
# 0 = x axis) equal to bounds[1], which is the flat shaft surface, and also 
# have material index -1 (all materials).
# It attaches these nodes as a node set named "SHAFT END NODES" to model.


vtkski.vtkskiNodeSetsByGeometry.AddNodesOnPlane(
	2,
	zShaftModelSurface,
	"SHAFT END NODES",
	model,
	-1)
Log ("Found %d nodes belonging to SHAFT END" % 
	 model.NodeIdsFromSelection("SHAFT END NODES").GetNumberOfTuples())


# Create a constraint that is applied to SHAFT END NODES.
# We set all directions to be fixed (note that 0=fixed).
fixedAxisFlagsShaft = (0,0,0)
model.SetFixedConstraints ("SHAFT END NODES", fixedAxisFlagsShaft, "SHAFT SURFACE CONSTRAINT")

# Now get these nodes (with point coordinates) and save them to a file
# so that we can examine them with ParaView, etc...
nodesFileShaft = os.path.splitext(inputAimFile)[0] + "_shaft_nodes.vtu"
verticesShaft = model.DataSetFromSelection ("SHAFT END NODES")
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
vtkski.vtkskiNodeSetsByGeometry.FindNodesOnVisibleSurface (
  visibleNodesIds,
  model,
  normalTrochVector,
  -1)
Log ("Found %d visible nodes." % visibleNodesIds.GetNumberOfTuples())
model.AddNodeSet (visibleNodesIds, "BONE BOTTOM VISIBLE NODES")

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
			visibleNodesBounds[3] - trochConstraintMaxDepth,
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
depthFilteredBoneNodesFile = os.path.splitext(inputAimFile)[0] + "_nodes_troch.vtu"
writer = vtk.vtkXMLUnstructuredGridWriter()
#depthFilteredBoneNodesFile = "depth_filtered_bone_nodes_troch.vtu"
writer.SetFileName (depthFilteredBoneNodesFile)
writer.SetInput (filteredSurfaceVertices)
Log ("Writing nodes to %s" % depthFilteredBoneNodesFile)
writer.Write()

nodeSet = filteredSurfaceVertices.GetPointData().GetPedigreeIds()
model.AddNodeSet (nodeSet, "BONE BOTTOM VISIBLE NODES")

# Create a constraint that is applied to BONE BOTTOM VISIBLE NODES.
# We set all directions to be fixed (note that 0=fixed).
fixedAxisFlags = (1,0,1)
model.SetFixedConstraints ("BONE BOTTOM VISIBLE NODES", fixedAxisFlags, "TROCHANTER SURFACE CONSTRAINT")


# --------------------------------------------------------------------------
# Constraint 3: Apply a displacement to the top of the femoral head
#
# We want to find the bone nodes that you
# would be able to see if you looked down upon the image from above.
# Further, we are going to limit the depth of nodes that we accept, where
# the depth is measured from the highest such node that we see

Log ("Adding the BONE HEAD TOP SURFACE constraint.")

vtkski.vtkskiNodeSetsByGeometry.FindNodesOnVisibleSurface (
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
		visibleNodesBounds[1],
		visibleNodesBounds[2],
		visibleNodesBounds[2] + headConstraintMaxDepth,
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
depthFilteredBoneNodesFile = os.path.splitext(inputAimFile)[0] + "_nodes_head.vtu"
writer = vtk.vtkXMLUnstructuredGridWriter()
#depthFilteredBoneNodesFile = "depth_filtered_bone_nodes_head.vtu"
writer.SetFileName (depthFilteredBoneNodesFile)
writer.SetInput (filteredSurfaceVertices)
Log ("Writing nodes to %s" % depthFilteredBoneNodesFile)
writer.Write()

nodeSet = filteredSurfaceVertices.GetPointData().GetPedigreeIds()
model.AddNodeSet (nodeSet, "BONE TOP VISIBLE NODES")

# Create a constraint that is applied to the node set.  This constraint
# means displacement of the y axis (1 = y axis) by the value 'displacement'.
model.SetDisplacementConstraints (
	"BONE TOP VISIBLE NODES",
	1,
	headDisplacement,
	"HEAD TOP DISPLACEMENT");

# --------------------------------------------------------------------------
# Set the node sets that will be used for post-processing

postProcessingNodeSetsKey = vtkski.vtkskiFiniteElementRun.POST_PROCESSING_NODE_SETS()
info = model.GetInformation()
postProcessingNodeSetsKey.Append (info, "SHAFT END NODES")
postProcessingNodeSetsKey.Append (info, "BONE BOTTOM VISIBLE NODES")
postProcessingNodeSetsKey.Append (info, "BONE TOP VISIBLE NODES")


# --------------------------------------------------------------------------
# Set various parameters

# Set maximum number of iterations and convergence tolerance.
 
#modelInfo = model.GetInformation()
#modelInfo.Set (vtkski.vtkFiniteElementRun.ITERATION_LIMIT(), 10000)
#modelInfo.Set (vtkski.vtkFiniteElementRun.CONVERSION_TOLERANCE(), 0.0001)

# --------------------------------------------------------------------------
# Write out faim file

Log ("Writing file %s" % outputFaimFile)
writer = vtkski.vtkskiFAIMInputWriter()
writer.SetInput (model)
writer.SetFileName (outputFaimFile)
writer.Update()


Log ("Done.")
