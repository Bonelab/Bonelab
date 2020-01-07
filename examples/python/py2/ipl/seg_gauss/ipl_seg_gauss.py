import sys
import argparse
import vtk
import vtkn88

def settings(sigma,support,lower,upper,value_in_range):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/seg_gauss"
    print "  -%-26s%s" % ("input","in")
    print "  -%-26s%s" % ("output","gauss")
    print "  -%-26s%.5f" % ("sigma",sigma)
    print "  -%-26s%d" % ("support",support)
    print "  -%-26s%.5f" % ("lower_in_perm_aut_al",lower)
    print "  -%-26s%.5f" % ("upper_in_perm_aut_al",upper)
    print "  -%-26s%d" % ("value_in_range",value_in_range)
    print "  -%-26s%d" % ("unit",0)
    print "!-------------------------------------------------------------------------"

parser = argparse.ArgumentParser (
    description="""Performs the equivalent IPL function using VTK classes:
seg_gauss""")

parser.add_argument ("--sigma", type=float, default=1.0,
        help="Set Gaussian filter sigma (default: %(default)s)")
parser.add_argument ("--support", type=int, default=2,
        help="Set Gaussian filter support (default: %(default)s)")
parser.add_argument ("--lower_in_perm_aut_al", type=float, default=100.0,
        help="Set lower threshold (default: %(default)s)")
parser.add_argument ("--upper_in_perm_aut_al", type=float, default=100000.0,
        help="Set upper threshold (default: %(default)s)")
parser.add_argument ("--value_in_range", type=int, default=127,
        help="Set value in range (default: %(default)s)")

parser.add_argument ("input")
parser.add_argument ("output")

args = parser.parse_args()

input = args.input	
output = args.output
sigma = args.sigma
support = args.support
lower = args.lower_in_perm_aut_al
upper = args.upper_in_perm_aut_al
value_in_range = args.value_in_range

print "Reading: ", input
reader = vtkn88.vtkn88AIMReader()
reader.SetFileName(input)
reader.GlobalWarningDisplayOff()
#reader.DataOnCellsOn()
reader.Update()

settings(sigma,support,lower,upper,value_in_range)

gauss = vtk.vtkImageGaussianSmooth()
gauss.SetInputConnection(reader.GetOutputPort())
gauss.SetDimensionality(3)
gauss.SetStandardDeviation( sigma ) 
gauss.SetRadiusFactors( support, support, support )
gauss.Update()

# If there is an offset in the input file, we scrub 
# those layers from the image data (as does IPL during
# the thresholding function

extent = reader.GetOutput().GetExtent()

voi = vtk.vtkExtractVOI()
voi.SetInputConnection(gauss.GetOutputPort())
voi.SetVOI( extent[0]+support, extent[1]-support, 
            extent[2]+support, extent[3]-support, 
            extent[4]+support, extent[5]-support)
voi.Update()

# Scale the thresholds from 'per 1000' of maximum scalar value
max_scaler = gauss.GetOutput().GetScalarTypeMax()

scaled_lower = lower / 1000.0 * max_scaler
scaled_upper = upper / 1000.0 * max_scaler

thres = vtk.vtkImageThreshold()
thres.SetInputConnection(voi.GetOutputPort())
thres.ThresholdBetween(scaled_lower, scaled_upper)
thres.SetInValue( value_in_range ) 
thres.SetOutValue( 0 ) 
thres.SetOutputScalarTypeToChar()
thres.Update()

writer = vtkn88.vtkn88AIMWriter()
writer.SetInputConnection(thres.GetOutputPort())
writer.SetFileName(output)
writer.CompressDataOn()
#writer.SetAimOffset( support, support, support )
writer.Update()

print "Writing: ", output

quit()