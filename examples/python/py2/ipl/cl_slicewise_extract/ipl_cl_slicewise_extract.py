import sys
import argparse
import vtk
import vtkn88

def settings(lower, upper, value_in):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/cl_slicewise_extractow"
    print "  -%-26s%s" % ("input","in")
    print "  -%-26s%.5f" % ("lo_vol_fract_in_perc",lower)
    print "  -%-26s%.5f" % ("up_vol_fract_in_perc",upper)
    print "  -%-26s%d" % ("value_in_range", value_in)
    print "!-------------------------------------------------------------------------"

parser = argparse.ArgumentParser (
    description="""Performs the equivalent IPL function using VTK classes:
cl_slicewise_extractow""")

parser.add_argument ("--lo_vol_fract_in_perc", type=float, default=25,
        help="Set slicewise extract lower fraction (default: %(default)s)")
parser.add_argument ("--up_vol_fract_in_perc", type=float, default=100,
        help="Set slicewise extract upper fraction (default: %(default)s)")
parser.add_argument ("--value_in_range", type=float, default=127,
        help="Set value in range (default: %(default)s)")
        
parser.add_argument ("input")
parser.add_argument ("output")

args = parser.parse_args()

input = args.input	
output = args.output
lower = args.lo_vol_fract_in_perc
upper = args.up_vol_fract_in_perc
value_in = args.value_in_range

settings(lower, upper, value_in)
		
print "Reading: ", input
reader = vtkn88.vtkn88AIMReader()
reader.SetFileName(input)
reader.GlobalWarningDisplayOff()
#reader.DataOnCellsOn()
reader.Update()

connect = vtkn88.vtkn88ImageConnectivityFilter()
connect.SetInput(reader.GetOutput())
connect.SetExtractionModeToLargestRegion()
connect.Update()
	
writer = vtkn88.vtkn88AIMWriter()
writer.SetInputConnection(connect.GetOutputPort())
writer.SetFileName(output)
#writer.SetAimOffset( offset[0], offset[1], offset[2] )
writer.Update()

print "Writing: ", output

quit()