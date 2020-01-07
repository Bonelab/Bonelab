from __future__ import division

import os
import sys
import vtk
import vtkski

fileroot = "1x1x2"

# -------------------------------------------------------------------------
# This makes an image with scalars on the Points

print "Generating a volume"
image = vtk.vtkImageData()
image.SetScalarTypeToShort()
image.SetNumberOfScalarComponents (1)
image.SetDimensions (1,1,2)
image.SetOrigin (0.5,0.5,0.5)
image.AllocateScalars ()
image.SetScalarComponentFromFloat (0, 0, 0, 0, 127)
image.SetScalarComponentFromFloat (0, 0, 1, 0, 127)

writer = vtk.vtkXMLImageDataWriter()
filename = fileroot + ".vti"
writer.SetFileName (filename)
writer.SetInput (image)
print "Writing image to", filename
writer.Write()

# -------------------------------------------------------------------------
# Convert to hexagonal cells

print "Converting to hexagonal cells."
hexa = vtkski.vtkskiImageToMesh()
hexa.SetInput (image)
hexa.AssignScalarsToCellsOn()
hexa.NodalCoordinatesRelativeToOriginOn()
hexa.HexahedronModeOn()
hexa.Update()
print "Generated %d hexahedrons" % hexa.GetOutput().GetNumberOfCells()

writer = vtk.vtkXMLUnstructuredGridWriter()
filename = fileroot + ".vtu"
writer.SetFileName (filename)
writer.SetInput (hexa.GetOutput())
print "Writing cells to",  filename
writer.Write()
