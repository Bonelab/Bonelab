
# Imports
import argparse
import os
import vtk

from bonelab.util.echo_arguments import echo_arguments
from bonelab.io.points import write_points
from bonelab.io.vtk_helpers import get_vtk_reader

def PointPicker(input_filename, output_filename, overwrite=False):
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

    # TODO: Matt's **crazy** work

def main():
    # Setup description
    description='''Pick points on an image

This function allows one to pick points on an image. Points are written to a plain
text file for use in other programs
'''

    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blPointPicker",
        description=description
    )
    parser.add_argument('input_filename', help='Input image file')
    parser.add_argument('output_filename', help='Output textfile listing picked points')
    parser.add_argument('-o', '--overwrite', action='store_true', help='Overwrite output without asking')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('PointPicker', vars(args)))

    # Run program
    PointPicker(**vars(args))

if __name__ == '__main__':
    main()
