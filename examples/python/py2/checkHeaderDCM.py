# History:
#   2017.03.10  babesler@ucalgary.ca    Created
#
# Description:
#   Print the header of a DCM file
#
# Notes:
#   - The real way to do this is to use the GDCM vtk DICOM class

# Imports
import vtk
import argparse
import os

# Create a map between functions and
dicomMap = {}
dicomMap['Pixel Spacing'] = 'GetPixelSpacing'
dicomMap['Width'] = 'GetWidth'
dicomMap['Height'] = 'GetHeight'
dicomMap['Patient Position'] = 'GetImagePositionPatient'
dicomMap['Patient Orientation'] = 'GetImageOrientationPatient'
dicomMap['Bits Allocated'] = 'GetBitsAllocated'
dicomMap['Pixel Representation'] = 'GetPixelRepresentation'
dicomMap['Number of Components'] = 'GetNumberOfComponents'
dicomMap['Transfer Syntax UID'] = 'GetTransferSyntaxUID'
dicomMap['Rescale Slope'] = 'GetRescaleSlope'
dicomMap['Rescale Offset'] = 'GetRescaleOffset'
dicomMap['Patient Name'] = 'GetPatientName'
dicomMap['Study UID'] = 'GetStudyUID'
dicomMap['Study ID'] = 'GetStudyID'
dicomMap['Gantry Angle'] = 'GetGantryAngle'

imageMap = {}
imageMap['Dimensions'] = 'GetDimensions'
imageMap['Scalar Type'] = 'GetScalarType'
imageMap['Extent'] = 'GetExtent'
imageMap['Spacing'] = 'GetSpacing'
imageMap['Origin'] = 'GetOrigin'

# Arguments
parser = argparse.ArgumentParser(
    description='Print dicom file info'
    )
parser.add_argument(
    'inputImage',
    help='The input DICOM file'
    )
args = parser.parse_args()

# Check that the input (file or directory) exists
if not os.path.exists(args.inputImage):
    os.sys.exit('Input \"{inputImage}\" does not exist. Exiting...'.format(inputImage=args.inputImage))

# Set reader and read
reader = vtk.vtkDICOMImageReader()
reader.SetFileName(args.inputImage)
reader.Update()

# Print info
for key, value in dicomMap.iteritems():
    print 'DICOM - {key}: {value}'.format(
            key=key,
            value=eval('reader.{}()'.format(value)))

# Print info
for key, value in imageMap.iteritems():
    print 'Image - {key}: {value}'.format(
            key=key,
            value=eval('reader.GetOutput().{}()'.format(value)))
