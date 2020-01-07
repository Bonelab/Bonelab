import sys
import argparse
import vtk
import vtkn88

def settings(object, background):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/dilation"
    print "  -%-26s%s" % ("input","in")
    print "  -%-26s%s" % ("value_object",object)
    print "  -%-26s%s" % ("value_background",background)
    print "!-------------------------------------------------------------------------"

parser = argparse.ArgumentParser (
    description="""Performs the equivalent IPL function using VTK classes:
gauss_lp""")

parser.add_argument ("--value_object", type=float, default=0,
        help="Set object value (default: %(default)s)")
parser.add_argument ("--value_background", type=float, default=127,
        help="Set background value (default: %(default)s)")
        
parser.add_argument ("input")
parser.add_argument ("output")

args = parser.parse_args()

input = args.input	
output = args.output
value_object = args.value_object
value_background = args.value_background

settings(value_object, value_background)
		
print "Reading: ", input
reader = vtkn88.vtkn88AIMReader()
reader.SetFileName(input)
reader.GlobalWarningDisplayOff()
#reader.DataOnCellsOn()
reader.Update()

temp = reader

if value_object == 0 and value_background == 127:
	invert = vtk.vtkImageMathematics()
	invert.SetInput1(reader.GetOutput())
	invert.SetOperationToInvert()
	invert.Update()
	
	set_back = vtk.vtkImageMathematics()
	set_back.SetInput1(invert.GetOutput())
	set_back.SetConstantC(32767)
	set_back.SetConstantK(127)
	set_back.SetOperationToReplaceCByK()
	
	temp = set_back
	
elif value_object == 0:
	set_back = vtk.vtkImageMathematics()
	set_back.SetInput1(reader.GetOutput())
	set_back.SetConstantC(0)
	set_back.SetConstantK(value_background)
	set_back.SetOperationToReplaceCByK()

	set_obj = vtk.vtkImageMathematics()
	set_obj.SetInput1(set_back.GetOutput())
	set_obj.SetConstantC(127)
	set_obj.SetConstantK(value_object)
	set_obj.SetOperationToReplaceCByK()
	
	temp = set_obj

else:
	set_obj = vtk.vtkImageMathematics()
	set_obj.SetInput1(reader.GetOutput())
	set_obj.SetConstantC(127)
	set_obj.SetConstantK(value_object)
	set_obj.SetOperationToReplaceCByK()
	
	set_back = vtk.vtkImageMathematics()
	set_back.SetInput1(set_obj.GetOutput())
	set_back.SetConstantC(0)
	set_back.SetConstantK(value_background)
	set_back.SetOperationToReplaceCByK()
	
	temp = set_back
	
writer = vtkn88.vtkn88AIMWriter()
writer.SetInputConnection(temp.GetOutputPort())
writer.SetFileName(output)
#writer.SetAimOffset( offset[0], offset[1], offset[2] )
writer.Update()
print "Writing: ", output

quit()