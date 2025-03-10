# This script calculates the angle between z-axes of baseline and follow-up
# scans based on the transformation file from IPL_REGISTER_XT2
#
# Author: Tannis Kemp
# Date: Feb 12 2020
#
# Example command line use:
#
#   python ZAxisOffset.py -H -o output_dir/output_file.txt
#                                               input_dir/input_file.txt

# Import packages:

import numpy as np
import argparse
import math
import sys

from bonelab.util.echo_arguments import echo_arguments

# Calculate angle from dot product of two vectors


def calculate_angle(v1, v2):
    return math.acos(np.dot(v1, v2) /
                     (np.linalg.norm(v1) * np.linalg.norm(v2)))

# Calculate offset angle between z axes of baseline & follow-up images & print
# to .TXT file


def offset(header, delimiter, input_files, output_file):

    # If no output file is specified, write the output to the command window
    if output_file == None:
        out = sys.stdout
    else:
        out = open(output_file, "wt")

    out.write('! This file was created with ZAxisOffset.py\n')

    print("Reading files...")

    count = 0
    for input_file in input_files:
        count = count + 1

        with open(input_file) as searchfile:
            entry = []
            print(input_file)

            substring1 = "/"
            substring2 = "_REG.TXT"

            # Get the subject ID
            parameter = 'Filename'
            value = (input_file[input_file.rfind(substring1)+1:
                                input_file.find(substring2)])
            unit = '[name]'
            entry.append([parameter, value, unit])

            # Load 4x4 transformation matrix from IPL .TXT file
            transformation = np.loadtxt(fname=input_file, skiprows=2)
            rotation = transformation[:3, :3]

            # Unit vector in the z direction
            baseline_z = np.array([0, 0, 1])

            # Follow-up image z-axis in baseline coordinate frame
            transformed_z = np.dot(rotation, baseline_z)

            # Calculate angle in degrees
            offset = np.rad2deg(calculate_angle(transformed_z, baseline_z))

            # Parameters for printing to .TXT file
            parameter = 'Offset'
            value = '%.6f' % offset
            unit = '[degrees]'

            entry.append([parameter, value, unit])

            # Print the output
            entry = list(zip(*entry))
            if header & (count == 1):
                out.write(delimiter.join(entry[0]) + "\n")
                out.write(delimiter.join(entry[2]) + "\n")
            out.write(delimiter.join(entry[1]) + "\n")


def main():
    description = '''Calculate the offset angle between z axes from IPL
                  transformation file.'''

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog='blZAxisOffset',
        description=description
    )

    parser = argparse.ArgumentParser(
        description="""Reads in .TXT file resulting from IPL_REGISTER_XT2
                    containing the transformation from follow_up to baseline
                    scans. The script calculates the offset in degrees between
                    the z-axes of baseline and follow-up scans""")

    parser.add_argument("--header", "-H",
                        action="store_true",
                        help="""Print a header line first.""")

    parser.add_argument("--delimiter", "-d",
                        default="\t",
                        help="""Delimiter character to separate columns.
                             Default is a tab ('\\t').""")

    parser.add_argument("--output_file", "-o",
                        help="Output file. If not specified, output will go to STDOUT.")

    parser.add_argument("input_files", nargs='*',
                        help="Files to process. Any number may be specified.")

    # Parse and display arguments
    args = parser.parse_args()

    print((echo_arguments('ZAxisOffset', vars(args))))

    # Run program
    offset(**vars(args))


# Call main function
if __name__ == '__main__':
    main()
