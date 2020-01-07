# History:
#   2017.04.03  babesler@ucalgary.ca    Created
#
# Description:
#   Print information about an image
#
# Notes:
#   - None
#
# Usage:
#   python checkImageInfo.py

# Libraries
import argparse
import os
import vtk
try:
    import vtkbone
    vtkboneImported = True
    vtkbonelabImported = False
except ImportError:
    vtkboneImported = False
    try:
        import vtkbonelab
        vtkbonelabImported = True
    except ImportError:
        vtkbonelabImported = False

# Setup and parse command line arguments
parser = argparse.ArgumentParser(
    description='Print image info'
    )
parser.add_argument(
    'inputImage',
    help='The input file'
    )
args = parser.parse_args()

# Check that the input exists
if not os.path.exists(args.inputImage):
    os.sys.exit('Input \"{inputImage}\" does not exist. Exiting...'.format(inputImage=args.inputImage))

# Read the input
reader = vtk.vtkImageReader2Factory.CreateImageReader2(args.inputImage)
if reader is None:
    if args.inputImage.lower().endswith('.nii'):
        reader = vtk.vtkNIFTIImageReader()
    elif args.inputImage.lower().endswith('.dcm'):
        reader = vtk.vtkDICOMImageReader()
    elif vtkboneImported and args.inputImage.lower().endswith('.aim'):
        reader = vtkbone.vtkboneAIMReader()
        reader.DataOnCellsOff()
    elif vtkbonelabImported and args.inputImage.lower().endswith('.aim'):
        reader = vtkbonelab.vtkbonelabAIMReader()
        reader.DataOnCellsOff()
    else:
        os.sys.exit('Unable to find a reader for \"{fileName}\". Exiting...'.format(fileName=args.inputImage))
reader.SetFileName(args.inputImage)
print('Loading {}...'.format(args.inputImage))
reader.Update()

# Print information
imageMap = {}
imageMap['Dimensions'] = 'GetDimensions'
imageMap['Scalar Type'] = 'GetScalarTypeAsString'
imageMap['Extent'] = 'GetExtent'
imageMap['Spacing'] = 'GetSpacing'
imageMap['Origin'] = 'GetOrigin'

# Print info
for key, value in imageMap.iteritems():
    print 'Image - {key}: {value}'.format(
            key=key,
            value=eval('reader.GetOutput().{}()'.format(value))
            )
