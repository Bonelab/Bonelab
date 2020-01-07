import sys
import argparse
import vtk
import vtkn88

def settings(dilate, boundary):
    print "!-------------------------------------------------------------------------"
    print "! Equivalent IPL settings"
    print "/dilation"
    print "  -%-26s%s" % ("input","in")
    print "  -%-26s%s" % ("output","out")
    print "  -%-26s%s" % ("dilate_distance",dilate)
    print "  -%-26s%d %d %d" % ("continuous_at_boundary",boundary[0], boundary[1], boundary[2] )
    print "  -%-26s%s" % ("use_previous_margin","false")
    print "!-------------------------------------------------------------------------"

parser = argparse.ArgumentParser (
    description="""Performs the equivalent IPL function using VTK classes:
dilation""")

parser.add_argument ("--dilate_distance", type=int, default=2,
        help="Set dilation filter distance (default: %(default)s)")
parser.add_argument ("--continuous_at_boundary", nargs= 3, type=int ,default=[0,0,0],
        help="Set continous boundary (default: %(default)s)")
        
parser.add_argument ("input")
parser.add_argument ("output")

args = parser.parse_args()

input = args.input	
output = args.output
boundary = args.continuous_at_boundary
dilate_distance = args.dilate_distance

settings(dilate_distance, boundary)
		
print "Reading: ", input
reader = vtkn88.vtkn88AIMReader()
reader.SetFileName(input)
reader.GlobalWarningDisplayOff()
#reader.DataOnCellsOn()
reader.Update()

image_in = reader.GetOutput()
   
extent = image_in.GetExtent()

#Actual distance of pixel dilation
distance = dilate_distance + 1
	
pad = vtk.vtkImageReslice()
pad.SetInput(image_in)
pad.SetOutputExtent(extent[0]-distance-1, extent[1]+distance+1, 
    	            extent[2]-distance-1, extent[3]+distance+1, 
   	                extent[4]-distance-1, extent[5]+distance+1)
pad.Update()

#Kernel size is twice the dilation distance plus one for the center voxel

dilate1 = vtk.vtkImageContinuousDilate3D()
dilate1.SetInputConnection(pad.GetOutputPort())
dilate1.SetKernelSize(5,5,5)
dilate1.Update()
'''
dilate2 = vtk.vtkImageContinuousDilate3D()
dilate2.SetInputConnection(dilate1.GetOutputPort())
dilate2.SetKernelSize(2,2,2)
dilate2.Update()
'''
ext = dilate1.GetOutput().GetExtent()

border = vtk.vtkExtractVOI()
border.SetInput(dilate1.GetOutput())
border.SetVOI( ext[0]+boundary[0]*distance, ext[1]-boundary[0]*distance, 
   	   	       ext[2]+boundary[1]*distance, ext[3]-boundary[1]*distance, 
   		       ext[4]+boundary[2]*distance, ext[5]-boundary[2]*distance)
border.Update()

clip = vtk.vtkImageReslice()
clip.SetInput(border.GetOutput())
clip.SetOutputExtent( ext[0], ext[1]-2, 
    	              ext[2], ext[3]-2, 
   	                  ext[4], ext[5]-2)
clip.SetResliceAxesOrigin( 0.32 , 0.32 , 0.32)
clip.MirrorOn()
clip.Update()
		
writer = vtkn88.vtkn88AIMWriter()
writer.SetInputConnection(clip.GetOutputPort())
writer.SetFileName(output)
#writer.SetAimOffset( offset[0], offset[1], offset[2] )
writer.Update()

print "Writing: ", output

quit()