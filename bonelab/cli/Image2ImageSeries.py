
# Imports
import argparse
import os
import vtk
import vtkbone

from bonelab.util.echo_arguments import echo_arguments
from bonelab.io.vtk_helpers import get_vtk_reader, get_vtk_writer, handle_filetype_writing_special_cases


def Image2ImageSeries(input_filename, output_filename, extension, number_of_digits):
    # Read input
    if not os.path.isfile(input_filename):
        os.sys.exit('[ERROR] Cannot find file \"{}\"'.format(input_filename))

    reader = get_vtk_reader(input_filename)
    if reader is None:
        os.sys.exit('[ERROR] Cannot find reader for file \"{}\"'.format(input_filename))

    print('Reading input image ' + input_filename)
    reader.SetFileName(input_filename)
    reader.Update()

    print('Writing to {} with extension {} and {} digits'.format(output_filename, extension, number_of_digits))
    formatter = '%s_%0{n}d.{s}'.format(n=number_of_digits,s=extension)
    try:
        fake_filename = formatter % (output_filename, 0)
    except TypeError:
        os.sys.exit('[ERROR] Given filename and extension cannot be formatted as expected. Is the extension valid?')
    except ValueError:
        os.sys.exit('[ERROR] Given filename and extension cannot be formatted as expected. Is the extension valid?')
    
    writer = get_vtk_writer(fake_filename)
    if writer is None:
        os.sys.exit('[ERROR] Cannot find writer for file \"{}\" with extension \{}\"'.format(output_filename, extension))
    writer.SetInputConnection(reader.GetOutputPort())
    writer.SetFileDimensionality(2)
    try:
        writer.SetFilePrefix(output_filename)
        writer.SetFilePattern(formatter)
    except:
        os.sys.exit('[ERROR] Output filetype not supported')

    # Handle edge cases for each output file type
    handle_filetype_writing_special_cases(writer)

    # Write
    writer.Write()

def main():
    # Setup description
    description='''Convert a 3D image to a series of 2D Images

Example usage:
    blImage2ImageSeries ~/.bldata/test25a.aim test25a

Output files will be overwritten if they exist. The string is
formatted by snprintf.

Care is taken to ensure the output image is of a type supported by
the file format. There may be rescaling of the image intensities
to fit inside the most appropriate data type supported by the
requested file type.

Supported extension include:
    bmp
    tif tiff
    png
    jpeg jpg
'''

    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blImage2ImageSeries",
        description=description
    )
    parser.add_argument('input_filename', help='Input image')
    parser.add_argument('output_filename', help='Output converted image (typically .nii)')
    parser.add_argument( '-e', '--extension', default='bmp', type=str,
                        help='Filename extension without a period (default: %(default)s)"')
    parser.add_argument( '-n', '--number_of_digits', default=4, type=int,
                        help='Number of digits to format with (default: %(default)d)"')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('Image2ImageSeries', vars(args)))

    # Run program
    Image2ImageSeries(**vars(args))

if __name__ == '__main__':
    main()
