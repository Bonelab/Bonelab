import sys
import argparse
import vtk
import vtkn88

def settings(dim_num, test, pos, dim_pix):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/gauss_lp"
    print "  -%-26s%s" % ("input","in")
    print "  -%-26s%d %d %d"  % ("supdim_numbers",dim_num[0], dim_num[1], dim_num[2])
    print "  -%-26s%d %d %d"  % ("testoff_pixels",test[0], test[1], test[2])
    print "  -%-26s%d %d %d"  ("suppos_pixels_local", pos[0], pos[1], pos[2])
    print "  -%-26s%d %d %d"  ("subdim_pixels", dim_pix[0], dim_pix[1], dim_pix[2])
    print "!-------------------------------------------------------------------------"

parser = argparse.ArgumentParser (
    description="""Performs the equivalent IPL function using VTK classes:
sup_divide""")

parser.add_argument ("--supdim_numbers", nargs = 3, type=int, default=[-1,-1,-1],
        help="Set offset (default: %(default)s)")
parser.add_argument ("--testoff_pixels", nargs = 3, type=int, default=[0,0,0],
        help="Set offset (default: %(default)s)")
parser.add_argument ("--suppos_pixels_local", nargs = 3, type=int, default=[-1,-1,-1],
        help="Set offset (default: %(default)s)")
parser.add_argument ("--subdim_pixels", nargs = 3, type=int, default=[-1,-1,-1],
        help="Set offset (default: %(default)s)")

parser.add_argument ("input")
parser.add_argument ("output")

args = parser.parse_args()

input = args.input	
output = args.output
dim_num = args.supdim_numbers
test = args.testoff_pixels
pos = args.suppos_pixels_local
dim_pix = args.subdim_pixels

print "Reading: ", input
reader = vtkn88.vtkn88AIMReader()
reader.SetFileName(input)
reader.GlobalWarningDisplayOff()
#reader.DataOnCellsOn()

settings(dim_num, test, pos, dim_pix)

writer = vtkn88.vtkn88AIMWriter()
writer.SetInputConnection(reader.GetOutputPort())
writer.SetFileName(output)
#writer.SetAimOffset( offset[0], offset[1], offset[2] )
writer.Update()

print "Writing: ", output

quit()