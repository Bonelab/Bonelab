# Description:
#   A script for generating a RP model
#   The steps for preparing the model are:
#       1) Copy the _SEG.AIM to the project disk
#       2) Run '@IPL_RP.COM INPUT.AIM'
#       3) Copy the _RP.AIM to a Linux/Mac machine
#       4) Run 'python prepairRP.py INPUT_RP.AIM INPUT_RP.stl initials'
#       5) Visualize before printing
#
# History:
#   2016.XX.XX  Steven Boyd     Created the prototyping script (see rapidprototype.py)
#   2016.06.29  Bryce Besler    Add initials to the side of the image
#
# Notes:
#   - Experimentally determine good choises for the factor(s): deciFactor
#   - Models can be at most 100 MB for Connex 500

from __future__ import division

import sys
import time
import vtk
import vtkbonelab
import numpy as np

# -------------------------------------------------------------------------
#  Utility functions


def log(msg, *additionalLines):
    """Print message with time stamp.

    The first argument is printed with a time stamp.
    Subsequent arguments are printed one to a line without a timestamp.
    """
    print "%8.2f %s" % (time.time() - start_time, msg)
    for line in additionalLines:
        print " " * 9 + line
start_time = time.time()

# -------------------------------------------------------------------------
#  Configuration
if len(sys.argv) != 3:
    print "Usage: python {0} file.aim output.stl".format(sys.argv[0])
    sys.exit(1)

aim_file = sys.argv[1]
stl_file = sys.argv[2]
deciFactor = 0.75 #.85  # 0 to 1, 0 is no decimation. What a 0.75 is compared to a 0.85 should be determine imperically
gaussSTD = 1.2  # STD for the gaussian filter
gaussRadius = 2.0  # radius for the gaussian filter
contourValue=50 # Contour value for vtkImageMarchingCubes

# -------------------------------------------------------------------------
# Load image and prepair
log("Reading AIM file " + aim_file)
reader = vtkbonelab.vtkbonelabAIMReader()
reader.SetFileName(aim_file)
reader.DataOnCellsOff()
reader.Update()

image = reader.GetOutput()
log("Read %d points from AIM file." % image.GetNumberOfPoints())
image_bounds = image.GetBounds()
log("Image bounds:", (" %.4f" * 6) % image_bounds)
image_extent = image.GetExtent()
log("Image extent:", (" %d" * 6) % image_extent)

# -------------------------------------------------------------------------
# Smooth the image data
log("Gaussian smoothing.")
gauss = vtk.vtkImageGaussianSmooth()
gauss.SetStandardDeviation(gaussSTD)
gauss.SetRadiusFactor(gaussRadius)
gauss.SetInputConnection(reader.GetOutputPort())
gauss.Update()
log("Total of %d voxels" % gauss.GetOutput().GetNumberOfCells())

# -------------------------------------------------------------------------
# Pad the image data
log("Padding the data.")
pad = vtk.vtkImageConstantPad()
pad.SetConstant(0)
pad.SetOutputWholeExtent(image_extent[0] - 1, image_extent[1] + 1,
                         image_extent[2] - 1, image_extent[3] + 1,
                         image_extent[4] - 1, image_extent[5] + 1)
pad.SetInputConnection(gauss.GetOutputPort())
pad.Update()
log("Total of %d padded voxels" % pad.GetOutput().GetNumberOfCells())

# -------------------------------------------------------------------------
# Extract the isosurface
log("Extracting isosurface.")
mcube = vtk.vtkImageMarchingCubes()
mcube.SetValue(0, contourValue)
mcube.SetInputConnection(pad.GetOutputPort())
mcube.Update()
log("Generated %d triangles" % mcube.GetOutput().GetNumberOfCells())

# --------------------------------------------------------------------------
# Decimate the isosurface to reduce size
log("Decimating the isosurface.")
deci = vtk.vtkQuadricDecimation()
deci.SetInputConnection(mcube.GetOutputPort())
deci.SetTargetReduction(deciFactor)
deci.Update()
log("Decimated to %d triangles" % deci.GetOutput().GetNumberOfCells())

# --------------------------------------------------------------------------
# Performing final clean on image data
log('Cleaning up the appended images')
cleaner = vtk.vtkCleanPolyData()
cleaner.SetInputConnection(deci.GetOutputPort())
cleaner.Update()

# --------------------------------------------------------------------------
# Perform connectivity filter on decimated object
log("Extracting largest component from decimated object")
filt = vtk.vtkPolyDataConnectivityFilter()
filt.SetInputConnection(cleaner.GetOutputPort())
filt.SetExtractionModeToLargestRegion()
filt.Update()

# --------------------------------------------------------------------------
# Create a render window and renderer.
log("Rendering")
ren = vtk.vtkRenderer()
renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(ren)
renWin.SetSize(600, 600)
renWin.SetWindowName("Bone Imaging Laboratory")

iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)

mapper = vtk.vtkPolyDataMapper()
mapper.ScalarVisibilityOff()
mapper.SetInputConnection(filt.GetOutputPort())

actor = vtk.vtkActor()
actor.SetMapper(mapper)

ren.AddActor(actor)
ren.SetBackground(.8, .8, .8)

iren.Initialize()
renWin.Render()
iren.Start()

# --------------------------------------------------------------------------
# Generate the STL file
log("Writing STL file to " + stl_file)
writer = vtk.vtkSTLWriter()
writer.SetFileName(stl_file)
writer.SetFileTypeToBinary()
writer.SetInputConnection(filt.GetOutputPort())
writer.Write()

log("Finished!")
