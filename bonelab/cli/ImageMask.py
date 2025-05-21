
# Imports
import argparse
import os
import vtk
import vtkbone
import numpy as np
import math

from bonelab.util.echo_arguments import echo_arguments
from vtk.util.numpy_support import vtk_to_numpy

def ImageMask(input_image, input_mask, output_image, kernel, overwrite):

  if os.path.isfile(output_image) and not overwrite:
    result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_image))
    if result.lower() not in ['y', 'yes']:
      print('Not overwriting. Exiting...')
      os.sys.exit()
  print('{:20s} = {:s}'.format('!> Output image:',output_image))
  
  if not os.path.isfile(input_image):
      os.sys.exit('[ERROR] Cannot find file \"{}\"'.format(input_image))

  if not os.path.isfile(input_mask):
      os.sys.exit('[ERROR] Cannot find file \"{}\"'.format(input_mask))

  if input_image.lower().endswith('.nii'):
      img_reader = vtk.vtkNIFTIImageReader()
  elif input_image.lower().endswith('.nii.gz'):
      img_reader = vtk.vtkNIFTIImageReader()
  else:
      os.sys.exit('[ERROR] Cannot find reader for file \"{}\"'.format(input_image))
  print('{:20s} = {:s}'.format('!> Input Image:',input_image))
  
  if input_mask.lower().endswith('.nii'):
      mask_reader = vtk.vtkNIFTIImageReader()
  elif input_mask.lower().endswith('.nii.gz'):
      mask_reader = vtk.vtkNIFTIImageReader()
  else:
      os.sys.exit('[ERROR] Cannot find reader for file \"{}\"'.format(input_mask))
  print('{:20s} = {:s}'.format('!> Input Mask:',input_mask))
  print('{:20s} = {:s}'.format('!> Output image:',output_image))
  
  print('Reading input image ' + input_image)
  img_reader.SetFileName(input_image)
  img_reader.Update()

  print('Reading input mask ' + input_mask)
  mask_reader.SetFileName(input_mask)
  mask_reader.Update()

  # Check that extents are equal
  img_extent = img_reader.GetOutput().GetExtent()
  mask_extent = mask_reader.GetOutput().GetExtent()
  
  print('{:20s} = '.format('!> Image extent:')+' '.join('{:3d}'.format(x) for x in img_extent))
  print('{:20s} = '.format('!> Mask extent:')+' '.join('{:3d}'.format(x) for x in mask_extent))
  
  for i in range(6):
    if img_extent[i] != mask_extent[i]:
      os.sys.exit('[ERROR] Image and mask must have same extents.')

  # Find range of input mask
  [imdata_range_min,imdata_range_max] = mask_reader.GetOutput().GetPointData().GetScalars().GetRange()
  print('{:20s} = {:.1f}'.format('!> Mask value min',imdata_range_min))
  print('{:20s} = {:.1f}'.format('!> Mask value max',imdata_range_max))

  # Check kernel for dilation (if any are non-zero perform dilation)
  print('{:20s} = {:3d} {:3d} {:3d}'.format('!> Kernel',kernel[0],kernel[1],kernel[2]))
  perform_dilation = False
  for i in range(3):
    if kernel[i]>0:
      perform_dilation = True
    if kernel[i]<1:
      os.sys.exit('[ERROR] Kernel values must be positive integers.')
  print('{:20s} = {}'.format('!> Perform dilation',perform_dilation))

  if perform_dilation:
    dilate = vtk.vtkImageDilateErode3D()
    dilate.SetInputConnection(mask_reader.GetOutputPort())
    dilate.SetDilateValue(imdata_range_max) # dilation occurs at border of dilate/erode; dilate value is mask
    dilate.SetErodeValue(imdata_range_min) # erode value is background
    dilate.SetKernelSize(kernel[0],kernel[1],kernel[2]) # amount of dilation
    dilate.Update()

  # Apply the mask to the image
  mask = vtk.vtkImageMask()
  mask.SetImageInputData(img_reader.GetOutput())
  if perform_dilation:
    mask.SetMaskInputData(dilate.GetOutput())
  else:
    mask.SetMaskInputData(mask_reader.GetOutput())
  mask.SetMaskedOutputValue(0.0)
  mask.Update()

  # Write result
  if output_image.lower().endswith('.nii'):
      writer = vtk.vtkNIFTIImageWriter()
  elif output_image.lower().endswith('.nii.gz'):
      writer = vtk.vtkNIFTIImageWriter()
  else:
      os.sys.exit('[ERROR] Cannot find writer for file \"{}\"'.format(output_image))
      
  # writer.SetInputConnection(mask.GetOutputPort())
  writer.SetInputData(mask.GetOutput())
  writer.SetFileName(output_image)
  writer.SetTimeDimension(img_reader.GetTimeDimension())
  writer.SetTimeSpacing(img_reader.GetTimeSpacing())
  writer.SetRescaleSlope(img_reader.GetRescaleSlope())
  writer.SetRescaleIntercept(img_reader.GetRescaleIntercept())
  writer.SetQFac(img_reader.GetQFac())
  writer.SetQFormMatrix(img_reader.GetQFormMatrix())
  writer.SetNIFTIHeader(img_reader.GetNIFTIHeader())
      
  print('Saving image ' + output_image)
  writer.Update()
  exit()
  # print('\n!> Output image')
  # aix(output_filename,extract.GetOutput())
  
def main():
    # Setup description
    description='''
Masks an image with a provided mask. 

Dilation of mask is optional. The size of the kernel
determines the amount of dilation.

Extents of the image and mask must be the same.

Valid input and output formats include: 
.nii, .nii.gz

Currently only accepts NIFTI file formats as input and output.

'''
    epilog='''
To see the options for each of the utilities, type something like this:
$ blImageMask input_image.nii.gz input_mask.nii.gz output_image.nii.gz --dilation 2

'''

    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blImageMask",
        description=description,
        epilog=epilog
    )
    
    parser.add_argument('input_image', help='Input image')
    parser.add_argument('input_mask', help='Input mask')
    parser.add_argument('output_image', help='Output image')
    parser.add_argument('-k', '--kernel', type=int, nargs=3, metavar='N', default=[0,0,0], help='Dilation kernel (default: %(default)s)')
    parser.add_argument('-ow', '--overwrite', action='store_true', help='Overwrite output without asking (default: %(default)s)')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('ImageMask', vars(args)))

    # Run program
    ImageMask(**vars(args))

if __name__ == '__main__':
    main()
