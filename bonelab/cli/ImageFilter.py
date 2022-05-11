
# Imports
import argparse
import os
import vtk
import vtkbone
import numpy as np

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
    print(guard)

def ImageFilter(input_filename, output_filename, range, overwrite=False):
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
    print('Input image labels:')
    histogram(reader.GetOutput())
    
    thres = vtk.vtkImageThreshold()
    thres.SetInputConnection(reader.GetOutputPort())
    thres.SetOutputScalarType(scalarType)
    thres.ThresholdBetween(1,10)
    thres.ReplaceOutOn()
    thres.SetOutValue(0)
    thres.Update()
    
    print('Output image labels:')
    histogram(thres.GetOutput())
    
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

def main():
    # Setup description
    description='''Reads segmented image and writes specified labels.

Valid input and output formats include: 
.nii, .nii.gz

Currently only accepts NIFTI file formats as input and output.

'''

    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blImageFilter",
        description=description
    )
    parser.add_argument('input_filename', help='Input image file (*.nii, *.nii.gz)')
    parser.add_argument('output_filename', help='Output image file (*.nii, *.nii.gz)')
    parser.add_argument('--range', type=int, nargs=2, default=[0,10], metavar='0', help='Set range of scalars to keep (default: %(default)s)')
    parser.add_argument('-o', '--overwrite', action='store_true', help='Overwrite output without asking')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('ImageFilter', vars(args)))

    # Run program
    ImageFilter(**vars(args))

if __name__ == '__main__':
    main()
