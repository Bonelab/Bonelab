import sys
import argparse
import vtk
import vtkn88

def settings(offset):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/offset_add"
    print "  -%-26s%s" % ("input","in")
    print "  -%-26s%d %d %d" % ("add_offset",offset[0], offset[1], offset[2] )
    print "!-------------------------------------------------------------------------"

parser = argparse.ArgumentParser (
    description="""Performs the equivalent IPL function using VTK classes:
offset_add""")

parser.add_argument ("--offset", nargs = 3, type=int, default=[0,0,0],
        help="Set offset (default: %(default)s)")

parser.add_argument ("input")
parser.add_argument ("output")

args = parser.parse_args()

input = args.input	
output = args.output
offset = args.offset

settings(offset)

print "Reading: ", input
reader = vtkn88.vtkn88AIMReader()
reader.SetFileName(input)
reader.GlobalWarningDisplayOff()
#reader.DataOnCellsOn()
reader.Update()

writer = vtkn88.vtkn88AIMWriter()
writer.SetInputConnection(reader.GetOutputPort())
writer.SetFileName(output)
writer.SetAimOffset( offset[0], offset[1], offset[2] )
writer.Update()

print "Writing: ", output

quit()