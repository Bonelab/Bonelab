import sys
import argparse
import vtk
import vtkn88

def settings(open):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/open"
    print "  -%-26s%s" % ("input","in")
    print "  -%-26s%s" % ("output","out")
    print "  -%-26s%s" % ("open_distance",open)
    print "!-------------------------------------------------------------------------"

parser = argparse.ArgumentParser (
    description="""Performs the equivalent IPL function using VTK classes:
open""")

parser.add_argument ("--open_distance", type=int, default=1,
        help="Set dilation filter distance (default: %(default)s)")
        
parser.add_argument ("input")
parser.add_argument ("output")

args = parser.parse_args()

input = args.input	
output = args.output
open = args.open_distance

settings(open)
		
print "Reading: ", input
reader = vtkn88.vtkn88AIMReader()
reader.SetFileName(input)
reader.GlobalWarningDisplayOff()
#reader.DataOnCellsOn()
reader.Update()

extent = reader.GetOutput().GetExtent()	

clip = vtk.vtkImageReslice()
clip.SetInput(reader.GetOutput())
clip.SetOutputExtent(extent[0]-2, extent[1]+2, 
                     extent[2]-2, extent[3]+2, 
                     extent[4]-2, extent[5]+2)
clip.MirrorOn()
clip.Update()

erode = vtk.vtkImageContinuousErode3D()
erode.SetInputConnection(clip.GetOutputPort())
erode.SetKernelSize(2*open+1,2*open+1,2*open+1)
erode.Update()

#Kernel size is twice the dilation distance plus one for the center voxel

dilate = vtk.vtkImageContinuousDilate3D()
dilate.SetInputConnection(erode.GetOutputPort())
dilate.SetKernelSize(2*open+2,2*open+2,2*open+2)
dilate.Update()

ext = dilate.GetOutput().GetExtent()

pad = vtk.vtkImageReslice()
pad.SetInput(dilate.GetOutput())
pad.SetOutputExtent(extent[0], extent[1], 
                    extent[2], extent[3], 
                    extent[4], extent[5])
pad.Update()

writer = vtkn88.vtkn88AIMWriter()
writer.SetInputConnection(pad.GetOutputPort())
writer.SetFileName(output)
#writer.SetAimOffset( offset[0], offset[1], offset[2] )
writer.Update()

print "Writing: ", output

quit()