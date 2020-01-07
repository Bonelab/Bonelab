import sys
import argparse
import vtk
import vtkn88

def settings(border):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/offset_add"
    print "  -%-26s%s" % ("input","in")
    print "  -%-26s%s" % ("output","out")
    print "  -%-26s%s" % ("z_only", "false" )
    print "  -%-26s%d %d %d" % ("border", border[0], border[1], border[2])
    print "!-------------------------------------------------------------------------"

parser = argparse.ArgumentParser (
    description="""Performs the equivalent IPL function using VTK classes:
offset_add""")

parser.add_argument ("--border", nargs = 3, type=int, default=[0,0,0],
        help="Set border (default: %(default)s)")

parser.add_argument ("input")
parser.add_argument ("output")

args = parser.parse_args()

input = args.input	
output = args.output
border = args.border

settings(border)

print "Reading: ", input
reader = vtkn88.vtkn88AIMReader()
reader.SetFileName(input)
reader.GlobalWarningDisplayOff()
#reader.DataOnCellsOn()
reader.Update()

extent = reader.GetOutput().GetExtent()

box = vtk.vtkImageReslice()
box.SetInput(reader.GetOutput())
box.SetOutputExtent(extent[0]-border[0], extent[1]+border[0], 
                    extent[2]-border[1], extent[3]+border[1], 
                    extent[4]-border[2], extent[5]+border[2])
box.Update()

writer = vtkn88.vtkn88AIMWriter()
writer.SetInputConnection(box.GetOutputPort())
writer.SetFileName(output)
#writer.SetAimOffset( offset[0], offset[1], offset[2] )
writer.Update()

print "Writing: ", output

quit()