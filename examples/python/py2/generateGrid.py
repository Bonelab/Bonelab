# History:
#   2017.04.10  babesler@ucalgary.ca    Created
#
# Description:
#   Generate a grid image using another image as a template
#
# Notes:
#   - The output is always NIfTY and a short becasue this works best with Elastix
#   - See http://www.vtk.org/Wiki/VTK/Examples/Cxx/Images/ImageGridSource for Examples
#   - See http://lists.bigr.nl/pipermail/elastix/2011-January/000331.html for a
#       discussion by the Elastix's people
#
# Usage:
#   python generateGrid.py

# Imports
import os
import math
import vtk
import vtkbone
import argparse

# Parse arguments
parser = argparse.ArgumentParser(
    description='Generate grid image',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
parser.add_argument(
    'inputImage',
    help='The input file'
    )
parser.add_argument(
    'outputImage',
    help='The output image (*.nii)'
    )
parser.add_argument('-g', '--gridSpacing',
                    default=[10,10,10], type=int, nargs=3,
                    help='The grid spacing in units of pixels')
parser.add_argument('--fillValue',
                    default=float(0), type=float,
                    help='Fill value for the grid')
parser.add_argument('--lineValue',
                    default=float(127), type=float,
                    help='Line value for the grid')
parser.add_argument('-f', '--force',
                    action='store_true',
                    help='Set to overwrite output without asking')
args = parser.parse_args()

# Check input arguments
# Check that input files exist
if not os.path.isfile(args.inputImage):
    os.sys.exit('Input file \"{fileName}\" does not exist. Exiting...'.format(fileName=args.inputImage))

# Validate that the output is .nii and does not exist already
if not args.outputImage.lower().endswith('.nii'):
    os.sys.exit('Output file \"{outputImage}\" is not a .nii file. Exiting...'.format(outputImage=args.outputImage))
if os.path.isfile(args.outputImage):
    if not args.force:
        answer = raw_input('Output file \"{outputImage}\" exists. Overwrite? [Y/n]'.format(outputImage=args.outputImage))
        if str(answer).lower() not in set(['yes','y', 'ye', '']):
            os.sys.exit('Will not overwrite \"{inputFile}\". Exiting...'.
            format(inputFile=args.outputImage))

# Check grid spacing is valid
for spacing in args.gridSpacing:
    if spacing < 0:
        os.sys.exit('Grid spacing must be an integer greater than zero. Given {}.Exiting...'.format(spacing))

# Read in inputs
reader = vtk.vtkImageReader2Factory.CreateImageReader2(args.inputImage)
if reader is None:
    if args.inputImage.lower().endswith('.aim'):
        reader = vtkbone.vtkboneAIMReader()
        reader.DataOnCellsOff()
    elif args.inputImage.lower().endswith('.nii'):
        reader = vtk.vtkNIFTIImageReader()
    elif args.inputImage.lower().endswith('.dcm'):
        reader = vtk.vtkDICOMImageReader()
    else:
        os.sys.exit('Unable to find a reader for \"{fileName}\". Exiting...'.format(fileName=args.inputImage))
reader.SetFileName(args.inputImage)
print('Loading {}...'.format(args.inputImage))
reader.Update()

# Grid source
gridSource = vtk.vtkImageGridSource()
gridSource.SetDataOrigin(reader.GetOutput().GetOrigin())
gridSource.SetDataSpacing(reader.GetOutput().GetSpacing())
gridSource.SetDataExtent(reader.GetOutput().GetExtent())
gridSource.SetDataScalarTypeToShort()
gridSource.SetGridSpacing(args.gridSpacing)
gridSource.SetLineValue(args.lineValue)
gridSource.SetFillValue(args.fillValue)
print('Generating grid image with fill/line values of {}/{}'.format(args.fillValue,args.lineValue))
gridSource.Update()

# Writer
writer = vtk.vtkNIFTIImageWriter()
writer.SetFileName(args.outputImage)
writer.SetInputConnection(gridSource.GetOutputPort())
print("Writing to {}".format(args.outputImage))
writer.Update()
