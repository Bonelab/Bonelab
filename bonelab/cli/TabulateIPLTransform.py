# Import packages:
import os
import sys
import time
import csv
import numpy as np
import argparse
import vtk
import vtkbone

from bonelab.util.echo_arguments import echo_arguments

# Utility Functions:


def message(msg, *additionalLines):
    """Print message with time stamp.

    The first argument is printed with the a time stamp.
    Subsequent arguments are printed one to a line without a timestamp.
    """
    print(('{0:8.2f} {1:s}'.format(time.time() - start_time, msg)))
    for line in additionalLines:
        print((" " * 9 + line))


def read_transform(IPL_transform_file):
    file = open(IPL_transform_file, 'r')
    data = file.read()
    split_data = data.split()
    array_data = np.array(split_data)
    i = [0, 1, 2, 3, 4, 5]
    mat = np.delete(array_data, i)
    mat = mat.astype(float)
    mat = mat.reshape(4, 4)
    rot = mat[:-1, :-1]

    return rot


start_time = time.time()


def TransformTabulateResults(transform_files, output_file):

    writer = csv.writer(open(output_file, 'w'), delimiter=',')
    writer.writerow(['filename',
                     'r11', 'r12', 'r13',
                     'r21', 'r22', 'r23',
                     'r31', 'r32', 'r33'])
    for file in transform_files:

        rot_mat = read_transform(file)
        writer.writerow([file,
                         rot_mat[0][0], rot_mat[0][1], rot_mat[0][2],
                         rot_mat[1][0], rot_mat[1][1], rot_mat[1][2],
                         rot_mat[2][0], rot_mat[2][1], rot_mat[2][2]])

    # for transform in transform_files:


def main():

    description = '''Tabulates all transformation matrices from 3D registration.'''

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog='blRegN88TabulateTransform',
        description=description
    )
    parser.add_argument('transform_files', nargs='*',
                        help='Array of transformation matrices (*.txt).')
    parser.add_argument('-o', '--output_file', default='REPO_transforms.csv',
                        help='Output file name.')

    # Parse and display arguments:
    args = parser.parse_args()
    print((echo_arguments('RegN88TabulateTransform', vars(args))))

    # Run program HERE
    TransformTabulateResults(**vars(args))


# Call main function
if __name__ == '__main__':
    main()
