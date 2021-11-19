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


def TransformResults(data_file, transform_file, output_file):

    # Read raw data file (Faim output):
    with open(data_file) as indat:
        reader = csv.DictReader(indat)
        raw_data = [r for r in reader]

    # Read in the rotation matrices from IPL 3D image registration:
    with open(transform_file) as inmat:
        reader = csv.DictReader(inmat)
        transforms = [r for r in reader]

    # Filter the data file to eliminate baseline scans:
    trafo_data = dict()
    i = 0
    for scan in raw_data:
        if "S1" in scan['filename']:
            continue
        trafo_data[i] = scan
        i = i + 1

    # Transform the reaction forces:
    for scan, mat in zip(trafo_data, transforms):

        R = np.array([[float(mat['r11']), float(mat['r12']), float(mat['r13'])],
                      [float(mat['r21']), float(mat['r22']), float(mat['r23'])],
                      [float(mat['r31']), float(mat['r32']), float(mat['r33'])]])
        f = np.array([float(trafo_data[scan]['fx_ns1']),
                      float(trafo_data[scan]['fy_ns1']),
                      float(trafo_data[scan]['fz_ns1'])])
        d = np.array([float(trafo_data[scan]['dx_avg_ns1']),
                      float(trafo_data[scan]['dy_avg_ns1']),
                      float(trafo_data[scan]['dz_avg_ns1'])])

        f_rot = np.dot(R, f)
        d_rot = np.dot(R, d)

        trafo_data[scan]['fx_ns1'] = f_rot[0]
        trafo_data[scan]['fy_ns1'] = f_rot[1]
        trafo_data[scan]['fz_ns1'] = f_rot[2]
        trafo_data[scan]['dx_avg_ns1'] = d_rot[0]
        trafo_data[scan]['dy_avg_ns1'] = d_rot[1]
        trafo_data[scan]['dz_avg_ns1'] = d_rot[2]

    # Write the transformed data to a new csv:
    trafo_data_keys = list(trafo_data[0].keys())
    with open(output_file, 'w') as outcsv:
        writer = csv.DictWriter(outcsv, fieldnames=trafo_data_keys)
        writer.writeheader()
        for data in trafo_data:
            writer.writerow(trafo_data[data])


def main():

    description = '''Transforms Faim outputs generated from solving a RegBC N88 model.'''

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
