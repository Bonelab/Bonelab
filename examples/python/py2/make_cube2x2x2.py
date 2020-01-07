from __future__ import division

import os
import sys
import vtk
import vtkski

fileroot = "cube2x2x2"

# -------------------------------------------------------------------------
# This makes an image with scalars on the Points

print "Generating a cube"
image = vtk.vtkImageData()
image.SetScalarTypeToShort()
image.SetNumberOfScalarComponents (1)
image.SetDimensions (2,2,2)
image.SetOrigin (0.5,0.5,0.5)
image.AllocateScalars ()
image.SetScalarComponentFromFloat (0, 0, 0, 0, 1)
image.SetScalarComponentFromFloat (1, 0, 0, 0, 2)
image.SetScalarComponentFromFloat (0, 1, 0, 0, 3)
image.SetScalarComponentFromFloat (1, 1, 0, 0, 4)
image.SetScalarComponentFromFloat (0, 0, 1, 0, 5)
image.SetScalarComponentFromFloat (1, 0, 1, 0, 6)
image.SetScalarComponentFromFloat (0, 1, 1, 0, 7)
image.SetScalarComponentFromFloat (1, 1, 1, 0, 8)

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
