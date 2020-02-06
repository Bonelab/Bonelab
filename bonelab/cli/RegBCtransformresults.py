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

# Utility functions:


def ReadTransform2Matrix():
    x = 1


def ReadResults2Vector():
    y = 2


def TransformResults(data_file, transform_file, output_file):
    z = 3


def main():

    description = '''Transforms FE results from the '''

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog='blRegN88TransformResults',
        description=description
    )
    parser.add_argument('data_file', help='File containing data from registered FE analysis.')
    parser.add_argument('transform_file',
                        help='File containing transformations from 3D registration (.csv).')
    parser.add_argument('-o', '--output_file', default='REPO_transformed_results.csv',
                        help='Transformed output file (.csv).')

    # Parse and display arguments:
    args = parser.parse_args()
    print((echo_arguments('RegN88TransformResults', vars(args))))

    # Run program HERE
    TransformResults(**vars(args))


# Call main function
if __name__ == '__main__':
    main()
