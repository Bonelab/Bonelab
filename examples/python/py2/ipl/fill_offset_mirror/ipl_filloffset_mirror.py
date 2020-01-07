import sys
import argparse
import vtk
import vtkn88

def settings():
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/filloffset_mirror"
    print "  -%-26s%s" % ("input","in")
    print "!-------------------------------------------------------------------------"

parser = argparse.ArgumentParser (
    description="""Performs the equivalent IPL function using VTK classes:
filloffset_mirror""")

parser.add_argument ("input")
parser.add_argument ("output")

args = parser.parse_args()

input = args.input	
output = args.output

settings()

print "Reading: ", input
reader = vtkn88.vtkn88AIMReader()
reader.SetFileName(input)
reader.GlobalWarningDisplayOff()
#reader.DataOnCellsOn()
reader.Update()

extent = reader.GetOutput().GetExtent()

off = reader.GetOffset()

print off
voi = vtk.vtkExtractVOI()
voi.SetInput(reader.GetOutput())
voi.SetVOI( extent[0]+off[0], extent[1]-off[0], 
            extent[2]+off[1], extent[3]-off[1], 
            extent[4]+off[2], extent[5]-off[2] )

mirror = vtk.vtkImageReslice()
mirror.SetInput(voi.GetOutput())
mirror.SetOutputExtent(extent[0], extent[1], 
                       extent[2], extent[3], 
                       extent[4], extent[5])
mirror.MirrorOn()
mirror.Update()

writer = vtkn88.vtkn88AIMWriter()
writer.SetInputConnection(mirror.GetOutputPort())
writer.SetFileName(output)
writer.CompressDataOn()
writer.SetAimOffset( off[0], off[1], off[2] )
writer.Update()

print "Writing: ", output

quit()