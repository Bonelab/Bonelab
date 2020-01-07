from __future__ import division

import os
import sys
import time
import vtk
import vtkbonelab

# -------------------------------------------------------------------------
#  Utility functions

def log(msg, *additionalLines):
    """Print message with time stamp.
    
    The first argument is printed with the a time stamp.
    Subsequent arguments are printed one to a line without a timestamp.
    """
    print "%8.2f %s" % (time.time()-start_time, msg)
    for line in additionalLines:
        print " " * 9 + line
start_time = time.time()


# -------------------------------------------------------------------------
#  Configuration

if len(sys.argv) != 2:
  print "Usage: python rapidprototype.py file.aim"
  sys.exit(1)
aim_file = sys.argv[1]

# -------------------------------------------------------------------------
# Read input data

log("Reading AIM file " + aim_file)
reader = vtkbonelab.vtkbonelabAIMReader()
reader.SetFileName(aim_file)
reader.DataOnCellsOff()
reader.Update()
image = reader.GetOutput()
log("Read %d points from AIM file." % image.GetNumberOfPoints())
image_bounds = image.GetBounds()
log("Image bounds:", (" %.4f"*6) % image_bounds)
image_extent = image.GetExtent()
log("Image extent:", (" %d"*6) % image_extent)

# -------------------------------------------------------------------------
# Smooth the image data

log("Gaussian smoothing.")
gauss = vtk.vtkImageGaussianSmooth()
gauss.SetStandardDeviation(1.2)
gauss.SetRadiusFactor(2.0)
gauss.SetInputConnection(reader.GetOutputPort())
gauss.Update()
log("Total of %d voxels" % gauss.GetOutput().GetNumberOfCells())

# -------------------------------------------------------------------------
# Pad the image data
log ("Padding the data.")
pad = vtk.vtkImageConstantPad()
pad.SetConstant(0)
pad.SetOutputWholeExtent(image_extent[0]-1,image_extent[1]+1,
                         image_extent[2]-1,image_extent[3]+1,
                         image_extent[4]-1,image_extent[5]+1)
pad.SetInputConnection(gauss.GetOutputPort())
pad.Update()
log("Total of %d padded voxels" % pad.GetOutput().GetNumberOfCells())

# -------------------------------------------------------------------------
# Extract the isosurface

log("Extracting isosurface.")
mcube = vtk.vtkImageMarchingCubes()
mcube.SetValue(0,50)
mcube.SetInputConnection(pad.GetOutputPort())
mcube.Update()
log("Generated %d triangles" % mcube.GetOutput().GetNumberOfCells())
#log(" mcube %s" % mcube.GetOutput())

log("Decimating the isosurface.")
deci = vtk.vtkDecimatePro()
deci.SetInputConnection(mcube.GetOutputPort())
deci.SetTargetReduction(.85) # 0 to 1, 0 is no decimation.
deci.Update()
log("Decimated to %d triangles" % deci.GetOutput().GetNumberOfCells())

# --------------------------------------------------------------------------
# Create a render window and renderer.

ren = vtk.vtkRenderer()
renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(ren)
renWin.SetSize(600,600)
renWin.SetWindowName("Bone Imaging Laboratory")

iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)

mapper = vtk.vtkPolyDataMapper()
mapper.ScalarVisibilityOff()
mapper.SetInputConnection(deci.GetOutputPort())
#mapper.SetInputConnection(mcube.GetOutputPort())
actor = vtk.vtkActor()
#actor.GetProperty().SetColor(.5,.5,.5)
actor.SetMapper(mapper)

ren.AddActor(actor)
ren.SetBackground(.8,.8,.8)
 
iren.Initialize()
renWin.Render()
iren.Start()

# --------------------------------------------------------------------------
# Generate the STL file

log("Writing STL file.")
writer = vtk.vtkSTLWriter()
filename = "rapidprototype.stl"
writer.SetFileName(filename)
writer.SetFileTypeToBinary()
#writer.SetFileTypeToASCII()
writer.SetInputConnection(deci.GetOutputPort())
#writer.SetInputConnection(mcube.GetOutputPort())
log("Writing mesh to " + filename)
writer.Write()

log("Done.")
