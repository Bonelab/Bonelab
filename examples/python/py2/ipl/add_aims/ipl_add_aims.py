import sys
import argparse
import vtk
import vtkn88

def settings():
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/add_aims"
    print "  -%-26s%s" % ("input1","in")
    print "  -%-26s%s" % ("input2","in1")
    print "  -%-26s%s" % ("output","out")
    print "!-------------------------------------------------------------------------"

parser = argparse.ArgumentParser (
    description="""Performs the equivalent IPL function using VTK classes:
add_aims""")
        
parser.add_argument ("input1")
parser.add_argument ("input2")
parser.add_argument ("output")

args = parser.parse_args()

input1 = args.input1
input2 = args.input2
output = args.output

settings()
		
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

shift1 = vtk.vtkImageShiftScale()
shift1.SetInputConnection(reader1.GetOutputPort())
shift1.SetOutputScalarTypeToChar()

shift2 = vtk.vtkImageShiftScale()
shift2.SetInputConnection(reader2.GetOutputPort())
shift2.SetOutputScalarTypeToChar()

add = vtk.vtkImageMathematics()
add.SetInput1(shift1.GetOutput())
add.SetInput2(shift2.GetOutput())
add.SetOperationToAdd()

temp = vtk.vtkImageMathematics()
temp.SetInput1(add.GetOutput())
temp.SetConstantC(-2)
temp.SetConstantK(127)
temp.SetOperationToReplaceCByK()
	
writer = vtkn88.vtkn88AIMWriter()
writer.SetInputConnection(temp.GetOutputPort())
writer.SetFileName(output)
#writer.SetAimOffset( offset[0], offset[1], offset[2] )
writer.Update()

print "Writing: ", output

quit()