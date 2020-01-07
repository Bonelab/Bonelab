import os
import time
import sys
import argparse
import vtk
import vtkn88


#===========================================================
# Print Stats
#===========================================================

def diff(im1,im2):

        #Takes the differences of two aim files and adds them together
    
	shift1 = vtk.vtkImageShiftScale()
	shift1.SetInputConnection(im1.GetOutputPort())
	shift1.SetOutputScalarTypeToChar()
	
	shift2 = vtk.vtkImageShiftScale()
	shift2.SetInputConnection(im2.GetOutputPort())
	shift2.SetOutputScalarTypeToChar()
	
	box1 = vtk.vtkImageReslice()
	box1.SetInput(shift1.GetOutput())
	box1.SetResliceAxesOrigin(im2.GetOutput().GetOrigin())
	box1.Update()
	
	sub1 = vtk.vtkImageMathematics()
	sub1.SetInput1(box1.GetOutput())
	sub1.SetInput2(shift2.GetOutput())
	sub1.SetOperationToSubtract()
	
	sub2 = vtk.vtkImageMathematics()
	sub2.SetInput1(shift2.GetOutput())
	sub2.SetInput2(shift1.GetOutput())
	sub2.SetOperationToSubtract()
	
	step1 = vtk.vtkImageMathematics()
	step1.SetInput1(sub1.GetOutput())
	step1.SetConstantC(-127)
	step1.SetConstantK(0)
	step1.SetOperationToReplaceCByK()
	
	step2 = vtk.vtkImageMathematics()
	step2.SetInput1(sub2.GetOutput())
	step2.SetConstantC(-127)
	step2.SetConstantK(0)
	step2.SetOperationToReplaceCByK()
	
	add = vtk.vtkImageMathematics()
	add.SetInput1(step2.GetOutput())
	add.SetInput2(step1.GetOutput())
	add.SetOperationToAdd()

	return add

def render(im,dim):

        #Definition for lookup table required for mapper
	ul = 127 
	ll = 0
	lut = vtk.vtkLookupTable()
	lut.SetNumberOfColors(256)
	lut.SetTableRange(ll,ul)

	colorMap = vtk.vtkImageMapToColors()
	colorMap.SetInput(im)
	colorMap.SetLookupTable(lut)
	
	mapper = vtk.vtkImageMapper()
	mapper.SetInput(colorMap.GetOutput())
	mapper.SetColorWindow(ul-ll)
	mapper.SetColorLevel((ul-ll)/2)
	
	actor = vtk.vtkActor2D()
	actor.SetMapper(mapper)
	
	ren = vtk.vtkRenderer()
	ren.AddActor(actor)
	#ren.SetBackground(.8,.8,.8)

	renWin = vtk.vtkRenderWindow()
	renWin.AddRenderer(ren)
	renWin.SetSize(800,800)
	renWin.SetWindowName("Bone Imaging Laboratory")
	renWin.SetSize(dim.GetDimension()[0],dim.GetDimension()[1])
	renWin.SetPosition(50,50)

	iren = vtk.vtkRenderWindowInteractor()
	iren.SetRenderWindow(renWin)

	for i in range(dim.GetDimension()[2]):
  		mapper.SetZSlice(i)
  		renWin.Render()


	iren.Initialize()
	renWin.Render()
	iren.Start()
	
def stats(im):
    print "	"
    print "!- Statistics ------------------------------------------------------------"
    print "  dim                   %8d %8d %8d" % (im.GetDimensions())
    print "  origin                %8.2f %8.2f %8.2f" % (im.GetOrigin())
    print "  spacing               %8.2f %8.2f %8.2f" % (im.GetSpacing())
    print "  extent                %8d %8d %8d %8d %8d %8d" % (im.GetExtent())
    print "  scalar type           %s" % (im.GetScalarTypeAsString())
    print "!-------------------------------------------------------------------------"

def histo(im):
    accumulate = vtk.vtkImageAccumulate()
    accumulate.SetInput(im)
    accumulate.SetComponentSpacing( 1, 0, 0 )
    accumulate.SetComponentOrigin( 0, 0, 0 )
    accumulate.SetComponentExtent( 0, 12000, 0, 0, 0, 0 )
    accumulate.Update()
    
    print "!- Histogram -------------------------------------------------------------"
    print "  min                %8.2f" % (accumulate.GetMin()[0])
    print "  max                %8.2f" % (accumulate.GetMax()[0])
    print "  mean               %8.2f" % (accumulate.GetMean()[0])
    print "  SD                 %8.2f" % (accumulate.GetStandardDeviation()[0])
    print "  voxel count        %8d" % (accumulate.GetVoxelCount())
    print "!-------------------------------------------------------------------------"
    print " "

parser = argparse.ArgumentParser (
    description="""Reads in and compares two AIM files.""")

parser.add_argument('--statistics',dest='statistics',action='store_true', default=True,
    help="Calculate statistics on both input files (default: %(default)s)")
parser.add_argument('--difference',dest='difference',action='store_true', default=True,
    help="Calculate statistics on both input files (default: %(default)s)")

parser.add_argument ("input1")
parser.add_argument ("input2")

args = parser.parse_args()

#===========================================================
# Read in and call stats and histogram functions
#===========================================================

statistics = args.statistics
difference = args.difference
input1 = args.input1
input2 = args.input2

print "Reading input1: ", input1
reader1 = vtkn88.vtkn88AIMReader()
reader1.SetFileName(input1)
reader1.GlobalWarningDisplayOff()
#reader1.DataOnCellsOn()
reader1.Update()

if (statistics):
    stats(reader1.GetOutput())
    histo(reader1.GetOutput())

print "Reading input2: ", input2
reader2 = vtkn88.vtkn88AIMReader()
reader2.SetFileName(input2)
reader2.GlobalWarningDisplayOff()
#reader2.DataOnCellsOn()
reader2.Update()

if (statistics):
    stats(reader2.GetOutput())
    histo(reader2.GetOutput())

if (difference):
	render(reader1.GetOutput(),reader1)
	render(reader2.GetOutput(),reader2)
	
	diff = diff(reader1,reader2)
	
	print "Outputing difference histogram:"
	print " "
	
	histo(diff.GetOutput())
	render(diff.GetOutput(),reader2)
	
	
	
quit()

#===========================================================
# Rendering the difference of the 2D Slices
#===========================================================


