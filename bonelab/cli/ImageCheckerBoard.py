
# Imports
import argparse
import os
import vtk
import vtkbone
import numpy as np
import math

from bonelab.util.echo_arguments import echo_arguments
from vtk.util.numpy_support import vtk_to_numpy

def ImageCheckerBoard(input_image1, input_image2, divisions, outfile):

  if not os.path.isfile(input_image1):
      os.sys.exit('[ERROR] Cannot find file \"{}\"'.format(input_image1))

  if not os.path.isfile(input_image2):
      os.sys.exit('[ERROR] Cannot find file \"{}\"'.format(input_image2))

  if input_image1.lower().endswith('.nii'):
      im1_reader = vtk.vtkNIFTIImageReader()
  elif input_image1.lower().endswith('.nii.gz'):
      im1_reader = vtk.vtkNIFTIImageReader()
  else:
      os.sys.exit('[ERROR] Cannot find reader for file \"{}\"'.format(input_image1))
  print('{:20s} = {:s}'.format('!> Input Image 1:',input_image1))

  if input_image2.lower().endswith('.nii'):
      im2_reader = vtk.vtkNIFTIImageReader()
  elif input_image2.lower().endswith('.nii.gz'):
      im2_reader = vtk.vtkNIFTIImageReader()
  else:
      os.sys.exit('[ERROR] Cannot find reader for file \"{}\"'.format(input_image2))
  print('{:20s} = {:s}'.format('!> Input Image 2:',input_image2))
  
  im1_reader.SetFileName(input_image1)
  im1_reader.Update()

  im2_reader.SetFileName(input_image2)
  im2_reader.Update()

  # Get the common extent
  im1_extent = im1_reader.GetOutput().GetExtent()
  im2_extent = im2_reader.GetOutput().GetExtent()
  common_extent = [0 for x in range(6)]

  for i in [0,2,4]: # min
    common_extent[i] = min(im1_extent[i], im2_extent[i])

  for i in [1,3,5]: # max
    common_extent[i] = max(im1_extent[i], im2_extent[i])

  print('{:20s} = '.format('!> Image 1 extent:')+' '.join('{:3d}'.format(x) for x in im1_extent))
  print('{:20s} = '.format('!> Image 2 extent:')+' '.join('{:3d}'.format(x) for x in im2_extent))
  print('{:20s} = '.format('!> Common extent:')+' '.join('{:3d}'.format(x) for x in common_extent))
  
  # Pad images to the same extent
  im1_padder = vtk.vtkImageConstantPad()
  im1_padder.SetInputConnection(im1_reader.GetOutputPort())
  im1_padder.SetOutputWholeExtent(common_extent)
  im1_padder.SetConstant(im1_reader.GetOutput().GetScalarRange()[0])
  im1_padder.Update()
  
  im2_padder = vtk.vtkImageConstantPad()
  im2_padder.SetInputConnection(im2_reader.GetOutputPort())
  im2_padder.SetOutputWholeExtent(common_extent)
  im2_padder.SetConstant(im2_reader.GetOutput().GetScalarRange()[0])
  im2_padder.Update()
  
  # Checker board
  checker = vtk.vtkImageCheckerboard()
  checker.SetInput1Data(im1_padder.GetOutput())
  checker.SetInput2Data(im2_padder.GetOutput())
  checker.SetNumberOfDivisions(divisions)
  checker.Update()
  print('{:20s} = {:d} x {:d} x {:d}'.format('!> Divisions',divisions[0],divisions[1],divisions[2]))

  # Set up some values for displaying the data
  middle = int((common_extent[4]+common_extent[5])/2)
  print('{:20s} = {:d}'.format('!> Middle slice',middle))
  im_range = checker.GetOutput().GetScalarRange()
  print('{:20s} = {:12.3f} {:12.3f}'.format('!> Image range',im_range[0],im_range[1]))
  window = im_range[1] - im_range[0]
  level = (im_range[1] + im_range[0])/2
  print('{:20s} = {:12.3f} {:12.3f}'.format('!> Window/level',window,level))

  # Resize image
  resize = vtk.vtkImageResize()
  resize.SetInputConnection(checker.GetOutputPort())
  resize.SetResizeMethodToOutputDimensions()
  resize.SetOutputDimensions(1024,1024,1024)
  # resize.SetResizeMethodToMagnificationFactors()
  # resize.SetMagnificationFactors(4,4,4)
  
  # Display using image viewer convenience class
  viewer = vtk.vtkImageViewer()
  viewer.SetInputConnection(resize.GetOutputPort())
  viewer.SetZSlice(middle)
  viewer.SetColorLevel(level)
  viewer.SetColorWindow(window)
  viewer.Render()

  # Connect an interactor to the image viewer
  iren = vtk.vtkRenderWindowInteractor()
  iren.SetInteractorStyle(vtk.vtkInteractorStyleImage())
  viewer.SetupInteractor(iren)

  # Add observers for mouse wheel events to scroll through slices
  def wheelForward(obj, event):
  	zSlice = viewer.GetZSlice()
  	if (zSlice < viewer.GetWholeZMax()):
  		viewer.SetZSlice(zSlice + 1)

  def wheelBackward(obj, event):
  	zSlice = viewer.GetZSlice()
  	if (zSlice > viewer.GetWholeZMin()):
  		viewer.SetZSlice(zSlice - 1)

  iren.AddObserver("MouseWheelForwardEvent", wheelForward)
  iren.AddObserver("MouseWheelBackwardEvent", wheelBackward)

  # Draw stuff to the screen!
  viewer.Render()
  iren.Start()
  
  if outfile is not None:
    if outfile.lower().endswith('.nii'):
        writer = vtk.vtkNIFTIImageWriter()
    elif outfile.lower().endswith('.nii.gz'):
        writer = vtk.vtkNIFTIImageWriter()
    elif outfile.lower().endswith('.aim'):
        writer = vtkbone.vtkboneAIMWriter()
    else:
        os.sys.exit('[ERROR] Cannot find reader for file \"{}\"'.format(input_image1))
    
    # writer = vtk.vtkNIFTIImageWriter()
    writer.SetFileName(outfile)
    writer.SetInputConnection(checker.GetOutputPort())
    writer.Write()
    print('Writing {}'.format(outfile))


  
def main():
    # Setup description
    description='''
Shows two images in checkerboard style. Typically used to qualitatively check 
3D image registration results.

Extents of the two input images do not need to be the same. The divisions in
all three dimensions sometimes results in strange effects. Better to set the 
Z dimension to 1 usually.

Valid input and output formats include: .nii, .nii.gz

Currently only accepts NIFTI file formats as input and output.

'''
    epilog='''
To see the options for each of the utilities, type something like this:
$ blImageCheckerBoard image1.nii.gz image2.nii.gz --divisions 5 5 5

'''

    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blImageCheckerBoard",
        description=description,
        epilog=epilog
    )
    
    parser.add_argument('input_image1', help='Input image 1')
    parser.add_argument('input_image2', help='Input image 2')
    parser.add_argument('-d', '--divisions', type=int, nargs=3, metavar='N', default=[10,10,1], help='Checker board divisions (default: %(default)s)')
    parser.add_argument('-o','--outfile', default=None, metavar='FN', help='Output image file (*.tif) (default: %(default)s)')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('ImageCheckerBoard', vars(args)))

    # Run program
    ImageCheckerBoard(**vars(args))

if __name__ == '__main__':
    main()
