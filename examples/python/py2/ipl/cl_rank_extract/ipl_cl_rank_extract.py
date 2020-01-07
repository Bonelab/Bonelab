import sys
import argparse
import vtk
import vtkn88

def settings(first_rank,last_rank):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/cl_rank_extract"
    print "  -%-26s%s" % ("input","in")
    print "  -%-26s%s" % ("first_rank",first_rank)
    print "  -%-26s%s" % ("last_rank",last_rank)
    print "  -%-26s%s" % ("connect_boundary","false")
    print "  -%-26s%d" % ("value_in_range ",127)
    print "!-------------------------------------------------------------------------"

parser = argparse.ArgumentParser (
    description="""Performs the equivalent IPL function using VTK classes:
cl_rank_extract""")

parser.add_argument ("input")
parser.add_argument ("output")
parser.add_argument ("--first_rank", type=int, default=1,
        help="Set extract filter first_rank (default: %(default)s)")
parser.add_argument ("--last_rank", type=int, default=1,
        help="Set extract filter last_rank (default: %(default)s)")


args = parser.parse_args()

input = args.input	
output = args.output
first_rank = args.first_rank
last_rank = args.last_rank

settings(first_rank,last_rank)

print "Reading: ", input
reader = vtkn88.vtkn88AIMReader()
reader.SetFileName(input)
reader.GlobalWarningDisplayOff()
#reader.DataOnCellsOn()
reader.Update()

step1 = reader
temp = vtk.vtkImageMathematics()
temp.SetInput1(step1.GetOutput())
temp.SetConstantC(127)
temp.SetConstantK(0)
temp.SetOperationToReplaceCByK()

for x in range(first_rank,last_rank+1):

	connect = vtkn88.vtkn88ImageConnectivityFilter()
	connect.SetInput(reader.GetOutput())
	connect.SetExtractionModeToLargestRegion()
	connect.Update()

	sub = vtk.vtkImageMathematics()
	sub.SetInput1(reader.GetOutput())
	sub.SetInput2(connect.GetOutput())
	sub.SetOperationToSubtract()

	add = vtk.vtkImageMathematics()
	add.SetInput1(temp.GetOutput())
	add.SetInput2(connect.GetOutput())
	add.SetOperationToAdd()

	temp = add

	reader = sub

writer = vtkn88.vtkn88AIMWriter()
writer.SetInputConnection(temp.GetOutputPort())
writer.SetFileName(output)
#writer.SetAimOffset( support, support, support )
writer.Update()

print "Writing: ", output

quit()