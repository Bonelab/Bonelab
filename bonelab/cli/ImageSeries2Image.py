
# Imports
import argparse
import os
import vtk
import glob

from bonelab.util.echo_arguments import echo_arguments
from bonelab.io.vtk_helpers import get_vtk_reader, get_vtk_writer, handle_filetype_writing_special_cases


def ImageSeries2Image(input_directory, output_filename, expression, overwrite=False, verbose=False, multi_component=False):
    # Python 2/3 compatible input
    from six.moves import input

    # Check if output exists and should overwrite
    if os.path.isfile(output_filename) and not overwrite:
        result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_filename))
        if result.lower() not in ['y', 'yes']:
            print('Not overwriting. Exiting...')
            os.sys.exit()

    # Determine input type
    filenames = glob.glob(os.path.join(input_directory, expression))
    filenames.sort()
    print('Found {} files'.format(len(filenames)))
    if len(filenames) < 0:
        os.sys.exit('Found no files')
    if verbose:
        print('Filenames: {}'.format(filenames))
    reader = get_vtk_reader(filenames[0])
    if reader is None:
        os.sys.exit('[ERROR] Cannot find reader for file \"{}\"'.format(input_filename))

    if type(reader) == type(vtk.vtkDICOMImageReader()):
        # Found DICOM
        print('Reading DICOM from directory ' + input_directory)
        reader.SetDirectoryName(input_directory)
        reader.Update()
        output_filter = reader

        if verbose:
            print('DICOM Information')
            print('  Pixel Spacing:             {}'.format(reader.GetPixelSpacing()))
            print('  Width:                     {}'.format(reader.GetWidth()))
            print('  Height:                    {}'.format(reader.GetHeight()))
            print('  Image Orientation Patient: {}'.format(reader.GetImageOrientationPatient()))
            print('  Image Position Patient:    {}'.format(reader.GetImagePositionPatient()))
            print('  Bits Allocated:            {}'.format(reader.GetBitsAllocated()))
            print('  Pixel Representation:      {}'.format(reader.GetPixelRepresentation()))
            print('  Number of Components:      {}'.format(reader.GetNumberOfComponents()))
            print('  Transfer Syntax UID:       {}'.format(reader.GetTransferSyntaxUID()))
            print('  Rescale Slope:             {}'.format(reader.GetRescaleSlope()))
            print('  Rescale Offset:            {}'.format(reader.GetRescaleOffset()))
            print('  Patient Name:              {}'.format(reader.GetPatientName()))
            print('  Study UID:                 {}'.format(reader.GetStudyUID()))
            print('  Study ID:                  {}'.format(reader.GetStudyID()))
            print('  Gantry Angle:              {}'.format(reader.GetGantryAngle()))
            print('')
    else:
        # Found anything else
        vtk_filenames = vtk.vtkStringArray()
        for filename in filenames:
            vtk_filenames.InsertNextValue(filename)
        reader.SetFileNames(vtk_filenames)
        reader.SetFileDimensionality(2)
        reader.SetNumberOfScalarComponents(1)
        reader.Update()
        output_filter = reader

        if not multi_component:
            extractor = vtk.vtkImageExtractComponents()
            extractor.SetInputConnection(reader.GetOutputPort())
            extractor.SetComponents(1)
            output_filter = extractor

    # Create writer
    writer = get_vtk_writer(output_filename)
    if writer is None:
        os.sys.exit('[ERROR] Cannot find writer for file \"{}\"'.format(output_filename))
    writer.SetInputConnection(output_filter.GetOutputPort())
    writer.SetFileName(output_filename)

    # Handle edge cases for each output file type
    handle_filetype_writing_special_cases(writer)

    print('Saving image ' + output_filename)
    writer.Update()

def main():
    # Setup description
    description='''Convert a series of 2D images to one 3D image

Example usage:
    blImageSeries2Image ~/.bldata/dicom dicom.nii

There are a great deal of details in the DICOM standard of while not
all are handled by this function. For projects larger than, say, 10
subjects, one may want to go with a commercial DICOM importer.

Stacking of slices will be determined by an alpha-numeric sort.
'''

    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blImageSeries2Image",
        description=description
    )
    parser.add_argument('input_directory', help='Input image')
    parser.add_argument('output_filename', help='Output converted image (typically .nii)')
    parser.add_argument( '-e', '--expression', default='*', type=str,
                        help='An expression for matching files (default: %(default)s)')
    parser.add_argument('-o', '--overwrite', action='store_true', help='Overwrite output without asking')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-m', '--multi_component', action='store_true',
                        help='Set to export all components of the image. By default, only the first component is exported.')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('ImageSeries2Image', vars(args)))

    # Run program
    ImageSeries2Image(**vars(args))

if __name__ == '__main__':
    main()
