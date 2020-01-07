import sys
import argparse
import vtk
import vtkn88

def settings(sigma,support):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/gauss_lp"
    print "  -%-26s%s" % ("input","in")
    print "  -%-26s%s" % ("output","gauss")
    print "  -%-26s%.5f" % ("sigma",sigma)
    print "  -%-26s%d" % ("support",support)
    print "!-------------------------------------------------------------------------"

parser = argparse.ArgumentParser (
    description="""Performs the equivalent IPL function using VTK classes:
gauss_lp""")

parser.add_argument ("--sigma", type=float, default=1.0,
        help="Set Gaussian filter sigma (default: %(default)s)")
parser.add_argument ("--support", type=int, default=2,
        help="Set Gaussian filter support (default: %(default)s)")

parser.add_argument ("input")
parser.add_argument ("output")

args = parser.parse_args()

input = args.input	
output = args.output
sigma = args.sigma
support = args.support

print "Reading: ", input
reader = vtkn88.vtkn88AIMReader()
reader.SetFileName(input)
reader.GlobalWarningDisplayOff()
#reader.DataOnCellsOn()

settings(sigma,support)

gauss = vtk.vtkImageGaussianSmooth()
gauss.SetInputConnection(reader.GetOutputPort())
gauss.SetDimensionality(3)
gauss.SetStandardDeviation( sigma ) 
gauss.SetRadiusFactors( support, support, support )
gauss.Update()

writer = vtkn88.vtkn88AIMWriter()
writer.SetInputConnection(gauss.GetOutputPort())
writer.SetFileName(output)
writer.SetAimOffset( support, support, support )
writer.Update()

print "Writing: ", output

quit()