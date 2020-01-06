
# Imports
import argparse
import os

from bonelab.util.echo_arguments import echo_arguments
from bonelab.io.vtk_helpers import get_vtk_reader, get_vtk_writer, handle_filetype_writing_special_cases

def ImageConverter(input_filename, output_filename, processing_log='', overwrite=False):
    # Python 2/3 compatible input
    from six.moves import input

    # Check if output exists and should overwrite
    if os.path.isfile(output_filename) and not overwrite:
        result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_filename))
        if result.lower() not in ['y', 'yes']:
            print('Not overwriting. Exiting...')
            os.sys.exit()

    # Read input
    if not os.path.isfile(input_filename):
        os.sys.exit('[ERROR] Cannot find file \"{}\"'.format(input_filename))

    reader = get_vtk_reader(input_filename)
    if reader is None:
        os.sys.exit('[ERROR] Cannot find reader for file \"{}\"'.format(input_filename))

    print('Reading input image ' + input_filename)
    reader.SetFileName(input_filename)
    reader.Update()

    # Create writer
    writer = get_vtk_writer(output_filename)
    if writer is None:
        os.sys.exit('[ERROR] Cannot find writer for file \"{}\"'.format(output_filename))
    writer.SetInputConnection(reader.GetOutputPort())
    writer.SetFileName(output_filename)

    # Handle edge cases for each output file type
    handle_filetype_writing_special_cases(
        reader, writer,
        processing_log=processing_log
    )

    print('Saving image ' + output_filename)
    writer.Update()

def main():
    # Setup description
    description='''Convert from one image type to another

If a processing log is set, it is appended to the processing log of the
input AIM file. If the input is not an AIM file, then the processing log
is set as given.

Patient positioning in MINC and NIFTI file formats is not explicitely
handled.
'''

    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blImageConverter",
        description=description
    )
    parser.add_argument('input_filename', help='Input image file')
    parser.add_argument('output_filename', help='Output image file')
    parser.add_argument('-l', '--processing_log', default='', help='Processing log to add to AIM images')
    parser.add_argument('-o', '--overwrite', action='store_true', help='Overwrite output without asking')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('ImageConverter', vars(args)))

    # Run program
    ImageConverter(**vars(args))

if __name__ == '__main__':
    main()
