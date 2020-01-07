import sys
import argparse
import vtk
import vtkn88

def settings(peel_iter):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/maskaimpeel"
    print "  -%-26s%s" % ("input_output","in")
    print "  -%-26s%s" % ("filename","in1")
    print "  -%-26s%d" % ("peel_iter",peel_iter)
    print "!-------------------------------------------------------------------------"

parser = argparse.ArgumentParser (
    description="""Performs the equivalent IPL function using VTK classes:
maskaimpeel""")

parser.add_argument ("--peel_iter", type=int, default=2,
        help="Set upper threshold (default: %(default)s)")        
parser.add_argument ("input1")
parser.add_argument ("input2")
parser.add_argument ("output")

args = parser.parse_args()

input1 = args.input1
input2 = args.input2
peel_iter = args.peel_iter
output = args.output

settings(peel_iter)
		
print "Reading: ", input
reader1 = vtkn88.vtkn88AIMReader()
reader1.SetFileName(input1)
reader1.GlobalWarningDisplayOff()
#reader1.DataOnCellsOn()
reader1.Update()

print "Reading: ", input
reader2 = vtkn88.vtkn88AIMReader()
reader2.SetFileName(input2)
reader2.GlobalWarningDisplayOff()
#reader2.DataOnCellsOn()
reader2.Update()

shift = vtk.vtkImageShiftScale()
shift.SetInputConnection(reader1.GetOutputPort())
shift.SetOutputScalarTypeToUnsignedChar()

mask = vtk.vtkImageMask()
mask.SetImageInput(reader2.GetOutput())
mask.SetMaskInput(shift.GetOutput())
mask.SetMaskedOutputValue(0)

if peel_iter != 0:
	erode = vtk.vtkImageResize()
	erode.SetKernelSize(2*peel_iter,2*peel_iter,2*peel_iter)
	erode.SetInputConnection(mask.GetOutputPort())
	erode.Update()
	
	writer = vtkn88.vtkn88AIMWriter()
	writer.SetInputConnection(erode.GetOutputPort())
	writer.SetFileName(output)
	#writer.SetAimOffset( offset[0], offset[1], offset[2] )
	writer.Update()

	print "Writing: ", output
	
else:
	writer = vtkn88.vtkn88AIMWriter()
	writer.SetInputConnection(mask.GetOutputPort())
	writer.SetFileName(output)
	#writer.SetAimOffset( offset[0], offset[1], offset[2] )
	writer.Update()

	print "Writing: ", output


quit()