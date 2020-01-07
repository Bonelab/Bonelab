import sys
import argparse
import vtk
import vtkn88

def settings(support):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/median_filter"
    print "  -%-26s%s" % ("input","in")
    print "  -%-26s%d" % ("add_offset", support )
    print "!-------------------------------------------------------------------------"

parser = argparse.ArgumentParser (
    description="""Performs the equivalent IPL function using VTK classes:
offset_add""")

parser.add_argument ("--support", type=int, default = 1,
        help="Set offset (default: %(default)s)")

parser.add_argument ("input")
parser.add_argument ("output")

args = parser.parse_args()

input = args.input	
output = args.output
support = args.support

settings(support)

print "Reading: ", input
reader = vtkn88.vtkn88AIMReader()
reader.SetFileName(input)
reader.GlobalWarningDisplayOff()
#reader.DataOnCellsOn()
reader.Update()

extent = reader.GetOutput().GetExtent()

voi = vtk.vtkExtractVOI()
voi.SetInput(reader.GetOutput())
voi.SetVOI( extent[0]+support, extent[1]-support, 
            extent[2]+support, extent[3]-support, 
            extent[4]+support, extent[5]-support)
voi.Update()

median = vtk.vtkImageMedian3D( )
median.SetKernelSize ( support, support, support )
median.SetInputConnection(voi.GetOutputPort())

writer = vtkn88.vtkn88AIMWriter()
writer.SetInputConnection(median.GetOutputPort())
writer.SetFileName(output)
#writer.SetAimOffset( offset[0], offset[1], offset[2] )
writer.Update()

print "Writing: ", output

quit()