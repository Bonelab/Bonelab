
# Imports
import argparse
import os
import vtk
import vtkbone
import numpy as np
import math

from bonelab.util.echo_arguments import echo_arguments
from vtk.util.numpy_support import vtk_to_numpy

def histogram(image):
    array = vtk_to_numpy(image.GetPointData().GetScalars()).ravel()
    guard = '!-------------------------------------------------------------------------------'

    if (array.min() < -128):
      range_min = -32768
    elif (array.min() < 0):
      range_min = -128
    else:
      range_min = 0
    
    if (array.max() > 255):
      range_max = 32767
    elif (array.max() > 127):
      range_max = 255
    else:
      range_max = 127

    nRange = [range_min, range_max]
    nBins = 128
    
    # https://numpy.org/doc/stable/reference/generated/numpy.histogram.html
    hist,bin_edges = np.histogram(array,nBins,nRange,None,None,False)
    nValues = sum(hist)

    print(guard)
    print('!>  {:4s} ({:.3s}) : {:s}'.format('Lab','Qty','#Voxels'))
    for bin in range(nBins):
      index = nRange[0] + int(bin * (nRange[1]-nRange[0])/(nBins-1))
      count = hist[bin]/nValues # We normalize so total count = 1
      nStars = int(count*100)
      if (count>0 and nStars==0): # Ensures at least one * if the histogram bin is not zero
        nStars = 1
      if (nStars > 60):
        nStars = 60 # just prevents it from wrapping in the terminal
      if (count>0):
        print('!> {:4d} ({:.3f}): {:d}'.format(index,count,hist[bin]))
#    print(guard)

def aix(infile,image):
    guard = '!-------------------------------------------------------------------------------'
    phys_dim = [x*y for x,y in zip(image.GetDimensions(), image.GetSpacing())]
    position = [math.floor(x/y) for x,y in zip(image.GetOrigin(), image.GetSpacing())]
    size = os.path.getsize(infile) # gets size of file; used to calculate K,M,G bytes
    names = ['Bytes', 'KBytes', 'MBytes', 'GBytes']
    n_image_voxels = image.GetDimensions()[0] * image.GetDimensions()[1] * image.GetDimensions()[2]
    voxel_volume = image.GetSpacing()[0] * image.GetSpacing()[1] * image.GetSpacing()[2]
    i = 0
    while int(size) > 1024 and i < len(names):
        i+=1
        size = size / 2.0**10
    
    # Print header
    print('')
    print(guard)
    print('!>')
    print('!> dim                            {: >6}  {: >6}  {: >6}'.format(*image.GetDimensions()))
    print('!> off                                 x       x       x')
    print('!> pos                            {: >6}  {: >6}  {: >6}'.format(*position))
    print('!> element size in mm             {:.4f}  {:.4f}  {:.4f}'.format(*image.GetSpacing()))
    print('!> phys dim in mm                 {:.4f}  {:.4f}  {:.4f}'.format(*phys_dim))
    print('!>')
    print('!> Type of data               {}'.format(image.GetScalarTypeAsString()))
    print('!> Total memory size          {:.1f} {: <10}'.format(size, names[i]))
    print(guard)

def thres(input_filename, output_filename, range, overwrite, func):
    # Python 2/3 compatible input
    from six.moves import input

    # Check if output exists and should overwrite
    if os.path.isfile(output_filename) and not overwrite:
        result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_filename))
        if result.lower() not in ['y', 'yes']:
            print('Not overwriting. Exiting...')
            os.sys.exit()

    # Check valid range
    if (range[0]>range[1] or range[0]<0):
        os.sys.exit('[ERROR] Invalid range: {:d} {:d}'.format(range[0],range[1]))

    # Read input
    if not os.path.isfile(input_filename):
        os.sys.exit('[ERROR] Cannot find file \"{}\"'.format(input_filename))

    if input_filename.lower().endswith('.nii'):
        reader = vtk.vtkNIFTIImageReader()
    elif input_filename.lower().endswith('.nii.gz'):
        reader = vtk.vtkNIFTIImageReader()
    else:
        os.sys.exit('[ERROR] Cannot find reader for file \"{}\"'.format(input_filename))

    print('Reading input image ' + input_filename)
    reader.SetFileName(input_filename)
    reader.Update()

    scalarType = reader.GetOutput().GetScalarType()
    print('Input image scalar type: {:s}'.format(reader.GetOutput().GetScalarTypeAsString()))
    print('\n!> Input image labels')
    histogram(reader.GetOutput())
    aix(input_filename,reader.GetOutput())
    
    thres = vtk.vtkImageThreshold()
    thres.SetInputConnection(reader.GetOutputPort())
    thres.SetOutputScalarType(scalarType)
    thres.ThresholdBetween(1,10)
    thres.ReplaceOutOn()
    thres.SetOutValue(0)
    thres.Update()
    
    print('\n!> Output image labels')
    histogram(thres.GetOutput())
    aix(input_filename,thres.GetOutput())
    
    # Create writer
    if output_filename.lower().endswith('.nii'):
        writer = vtk.vtkNIFTIImageWriter()
    elif output_filename.lower().endswith('.nii.gz'):
        writer = vtk.vtkNIFTIImageWriter()
    else:
        os.sys.exit('[ERROR] Cannot find writer for file \"{}\"'.format(output_filename))
        
    writer.SetInputConnection(thres.GetOutputPort())
    writer.SetFileName(output_filename)
    writer.SetTimeDimension(reader.GetTimeDimension())
    writer.SetTimeSpacing(reader.GetTimeSpacing())
    writer.SetRescaleSlope(reader.GetRescaleSlope())
    writer.SetRescaleIntercept(reader.GetRescaleIntercept())
    writer.SetQFac(reader.GetQFac())
    writer.SetQFormMatrix(reader.GetQFormMatrix())
    writer.SetNIFTIHeader(reader.GetNIFTIHeader())

    print('Saving image ' + output_filename)
    writer.Update()

def subvol(input_filename, output_filename, voi, overwrite, func):

  if os.path.isfile(output_filename) and not overwrite:
    result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_filename))
    if result.lower() not in ['y', 'yes']:
      print('Not overwriting. Exiting...')
      os.sys.exit()
  
  if not os.path.isfile(input_filename):
      os.sys.exit('[ERROR] Cannot find file \"{}\"'.format(input_filename))

  if input_filename.lower().endswith('.nii'):
      reader = vtk.vtkNIFTIImageReader()
  elif input_filename.lower().endswith('.nii.gz'):
      reader = vtk.vtkNIFTIImageReader()
  else:
      os.sys.exit('[ERROR] Cannot find reader for file \"{}\"'.format(input_filename))

  print('Reading input image ' + input_filename)
  reader.SetFileName(input_filename)
  reader.Update()

  print('\n!> Input image')
  aix(input_filename,reader.GetOutput())

  extract = vtk.vtkExtractVOI()
  extract.SetInputConnection(reader.GetOutputPort())
  extract.SetVOI(voi)
  extract.SetSampleRate(1,1,1)
  extract.IncludeBoundaryOn()
  extract.Update()

  # Create writer
  if output_filename.lower().endswith('.nii'):
      writer = vtk.vtkNIFTIImageWriter()
  elif output_filename.lower().endswith('.nii.gz'):
      writer = vtk.vtkNIFTIImageWriter()
  else:
      os.sys.exit('[ERROR] Cannot find writer for file \"{}\"'.format(output_filename))
      
  writer.SetInputConnection(extract.GetOutputPort())
  writer.SetFileName(output_filename)
  writer.SetTimeDimension(reader.GetTimeDimension())
  writer.SetTimeSpacing(reader.GetTimeSpacing())
  writer.SetRescaleSlope(reader.GetRescaleSlope())
  writer.SetRescaleIntercept(reader.GetRescaleIntercept())
  writer.SetQFac(reader.GetQFac())
  writer.SetQFormMatrix(reader.GetQFormMatrix())
  writer.SetNIFTIHeader(reader.GetNIFTIHeader())
      
  print('Saving image ' + output_filename)
  writer.Update()
  
  print('\n!> Output image')
  aix(output_filename,extract.GetOutput())

def exam(input_filename, func):

  if not os.path.isfile(input_filename):
      os.sys.exit('[ERROR] Cannot find file \"{}\"'.format(input_filename))
  
  if input_filename.lower().endswith('.nii'):
     reader = vtk.vtkNIFTIImageReader()
  elif input_filename.lower().endswith('.nii.gz'):
     reader = vtk.vtkNIFTIImageReader()
  else:
     os.sys.exit('[ERROR] Cannot find reader for file \"{}\"'.format(input_filename))
     
  print('Reading input image ' + input_filename)
  reader.SetFileName(input_filename)
  reader.Update()
  
  print('\n!> Input image information')
  histogram(reader.GetOutput())
  aix(input_filename,reader.GetOutput())
  
def main():
    # Setup description
    description='''
A utility to perform various filter operations on image data.

Valid input and output formats include: 
.nii, .nii.gz

Currently only accepts NIFTI file formats as input and output.

subvol          : takes a subvolume from the input file
thres           : thresholds input within range provided (replaces with zero)
exam            : reads an input file and provides a report of size and content
'''
    epilog='''
To see the options for each of the utilities, type something like this:
$ blImageFilter thres --help

'''

    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blImageFilter",
        description=description,
        epilog=epilog
    )
    subparsers = parser.add_subparsers()
    
    # parser for thres
    parser_thres = subparsers.add_parser('thres')
    parser_thres.add_argument('input_filename', help='Input image file (*.nii, *.nii.gz)')
    parser_thres.add_argument('output_filename', help='Output image file (*.nii, *.nii.gz)')
    parser_thres.add_argument('--range', type=int, nargs=2, default=[0,10], metavar='0', help='Set range of scalars to keep (default: %(default)s)')
    parser_thres.add_argument('--overwrite', action='store_true', help='Overwrite output without asking (default: %(default)s)')
    parser_thres.set_defaults(func=thres)

    # parser for subvol
    parser_subvol = subparsers.add_parser('subvol')
    parser_subvol.add_argument('input_filename', help='Input image file (*.nii, *.nii.gz)')
    parser_subvol.add_argument('output_filename', help='Output image file (*.nii, *.nii.gz)')
    parser_subvol.add_argument('--voi', type=int, nargs=6, default=[0,1,0,1,0,1], metavar='0', help='VOI bounds in units pixels (default: %(default)s)')
    parser_subvol.add_argument('--overwrite', action='store_true', help='Overwrite output without asking (default: %(default)s)')
    parser_subvol.set_defaults(func=subvol)
    
    # parser for exam
    parser_exam = subparsers.add_parser('exam')
    parser_exam.add_argument('input_filename', help='Input image file (*.nii, *.nii.gz)')
    parser_exam.set_defaults(func=exam)
    
    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('ImageFilter', vars(args)))

    # Run program
    args.func(**vars(args))

if __name__ == '__main__':
    main()
