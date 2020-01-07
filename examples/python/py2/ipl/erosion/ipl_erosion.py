import sys
import argparse
import vtk
import vtkn88

def settings(erode):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/erosion"
    print "  -%-26s%s" % ("input","in")
    print "  -%-26s%s" % ("output","out")
    print "  -%-26s%s" % ("erode_distance",erode)
    print "  -%-26s%s" % ("use_previous_margin","false")
    print "!-------------------------------------------------------------------------"

parser = argparse.ArgumentParser (
    description="""Performs the equivalent IPL function using VTK classes:
erosion""")

parser.add_argument ("--erode_distance", type=int, default=5,
        help="Set erosion filter distance (default: %(default)s)")
        
parser.add_argument ("input")
parser.add_argument ("output")

args = parser.parse_args()

input = args.input	
output = args.output
erode_distance = args.erode_distance

settings(erode_distance)

print "Reading: ", input
reader = vtkn88.vtkn88AIMReader()
reader.SetFileName(input)
reader.GlobalWarningDisplayOff()
#reader.DataOnCellsOn()
reader.Update()

extent = reader.GetOutput().GetExtent()

#Actual distance of pixel erosion
distance = erode_distance + 1

#Kernel size is twice the dilation distance plus one for the center voxel
erode = vtk.vtkImageContinuousErode3D()
erode.SetInputConnection(reader.GetOutputPort())
erode.SetKernelSize(2*distance+1,2*distance+1,2*distance+1)
erode.Update()

clip = vtk.vtkImageReslice()
clip.SetInput(erode.GetOutput())
clip.SetOutputExtent(extent[0]+distance, extent[1]-distance, 
                     extent[2]+distance, extent[3]-distance, 
                     extent[4]+distance, extent[5]-distance)
clip.Update()

writer = vtkn88.vtkn88AIMWriter()
writer.SetInputConnection(clip.GetOutputPort())
writer.SetFileName(output)
#writer.SetAimOffset( offset[0], offset[1], offset[2] )
writer.Update()

print "Writing: ", output

quit()