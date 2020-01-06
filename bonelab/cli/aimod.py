
# Imports
import argparse
import os
import vtkbone
from vtk.util.numpy_support import vtk_to_numpy
import numpy as np

from bonelab.util.echo_arguments import echo_arguments

def aimod(input_aim, output_aim):
    # Python 2/3 compatible input
    from six.moves import input

    # Read file
    print('Reading file: {}.....'.format(input_aim))
    reader = vtkbone.vtkboneAIMReader()
    reader.DataOnCellsOff()
    reader.SetFileName(input_aim)
    reader.Update()
    image = reader.GetOutput()

    spacing = np.array(image.GetSpacing())
    origin = np.array(image.GetOrigin())
    dim = np.array(image.GetDimensions())

    def set(x, index, value):
        x[index] = value

    mapping = [
        ['el_size_mm.x',    lambda: spacing[0], lambda x: set(spacing, 0, x), float],
        ['el_size_mm.y',    lambda: spacing[1], lambda x: set(spacing, 1, x), float],
        ['el_size_mm.z',    lambda: spacing[2], lambda x: set(spacing, 2, x), float],
        ['pos.x',           lambda: origin[0],  lambda x: set(origin, 0, x),  float],
        ['pos.y',           lambda: origin[1],  lambda x: set(origin, 1, x),  float],
        ['pos.z',           lambda: origin[2],  lambda x: set(origin, 2, x),  float],
        ['dim.x',           lambda: dim[0],     lambda x: set(dim, 0, x),     int],
        ['dim.y',           lambda: dim[1],     lambda x: set(dim, 1, x),     int],
        ['dim.z',           lambda: dim[2],     lambda x: set(dim, 2, x),     int]
    ]

    max_length = 0
    for line in mapping:
        max_length = max(max_length, len(line[0]))
    formatter_float = '{{: <{}}} [{{:0.3f}}] ? '.format(max_length)
    formatter_int = '{{: <{}}} [{{}}] ? '.format(max_length)
    formatter_switch = lambda x: formatter_int if x == int else formatter_float
    

    for i in range(len(mapping)):
        # Grab this input
        line = mapping[i]
        formatter = formatter_switch(line[3])
        
        # Prompt user
        result = input(formatter.format(line[0], line[1]()))

        # Enter == continue
        if result == '':
            continue

        # q, quit, no save
        # e, exit, save
        if len(result) > 0:
            if result[0] == 'q':
                print('Quit: not saved.')
                os.sys.exit()
            if result[0] == 'e':
                print('Exit.')
                break

        # Otherwise, set value
        line[2](line[3](result))

    # Set results
    image.SetSpacing(spacing)
    image.SetOrigin(origin)
    image.SetDimensions(dim)

    # Write
    writer = vtkbone.vtkboneAIMWriter()
    writer.SetInputData(image)
    writer.SetFileName(output_aim)
    writer.Update()

def main():
    # Setup argument parsing
    parser = argparse.ArgumentParser(
        prog="aimod",
        description='''AIM information examine

Reads an AIM and allows user to modify image information.
The following characters are options during modification.
    'q' - Quit
    'e' - Exit modification mode (write the AIM)

A reimplementation of the seminal SCANCO program `aimod`. All
efforts have been made to preserve the style.

vtk only supports modification of spacing, origin, and dimensions.
'''
    )
    parser.add_argument('input_aim', help='Input aim')
    parser.add_argument('output_aim', help='Output aim')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('aimod', vars(args)))

    # Run program
    aimod(**vars(args))

if __name__ == '__main__':
    main()
