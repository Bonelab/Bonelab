
# Imports
import argparse
import os
import vtkbone
from vtk.util.numpy_support import vtk_to_numpy
import numpy as np

def aix(aim_file, log, stat, verbose):
    # Python 2/3 compatible input
    try:
        input = raw_input
    except NameError:
        pass

    # Read input file
    if not os.path.isfile(aim_file):
        print("!%  Can't open file {} for reading".format(aim_file))
        print("File read error: {}".format(aim_file))
    reader = vtkbone.vtkboneAIMReader()
    reader.DataOnCellsOff()
    reader.SetFileName(aim_file)
    reader.Update()
    image = reader.GetOutput()

    # Precompute some values
    guard = '!-------------------------------------------------------------------------------'
    phys_dim = [x*y for x,y in zip(image.GetDimensions(), reader.GetElementSize())]
    size = os.path.getsize(aim_file)
    names = ['Bytes', 'KBytes', 'MBytes', 'GBytes']
    i = 0
    while int(size) > 1024 and i < len(names):
        i+=1
        size = size / 2.0**10

    # Print header
    print('')
    print(guard)
    print('!>')
    print('!> dim                            {: >6}  {: >6}  {: >6}'.format(*image.GetDimensions()))
    print('!> off                                 x       x       x')
    print('!> pos                            {: >6}  {: >6}  {: >6}'.format(*reader.GetPosition()))
    print('!> element size in mm             {:.4f}  {:.4f}  {:.4f}'.format(*reader.GetElementSize()))
    print('!> phys dim in mm                 {:.4f}  {:.4f}  {:.4f}'.format(*phys_dim))
    print('!>')
    print('!> Type of data               {}'.format(image.GetScalarTypeAsString()))
    print('!> Total memory size          {:.1f} {: <10}'.format(size, names[i]))
    print(guard)

    # Print log
    if log:
        print(reader.GetProcessingLog())

    # Print Stat
    if stat:
        array = vtk_to_numpy(image.GetPointData().GetScalars()).ravel()
        data = {
            'Max':      array.max(),
            'Min':      array.min(),
            'Mean':     array.mean(),
            'SD':       array.std()
        }
        max_length = 0
        for measure, outcome in data.items():
            max_length = max(max_length, len(measure))
        formatter='{{:<{}}} {{:0.2f}}'.format(max_length)
        for measure, outcome in data.items():
            print(formatter.format(measure, outcome))
        print(guard)

    # Print verbose
    if verbose:
        array = vtk_to_numpy(image.GetPointData().GetScalars())
        array = array.reshape(image.GetDimensions()).transpose(2, 1, 0)
        i = 1
        it = np.nditer(array, flags=['multi_index'])
        while not it.finished:
            print("{} {}".format(it.multi_index, it[0]))

            # Print every 100
            if i%100 == 0:
                result = input('Continue printing results? (y/n)')
                if result not in ['y', 'yes']:
                    print('')
                    print('Aborting...')
                    break
                print('')

            it.iternext()
            i+=1

def main():
    # Setup argument parsing
    parser = argparse.ArgumentParser(
        prog="aix",
        description='''AIM information examine

A reimplementation of the seminal SCANCO program `aix`. All
efforts have been made to preserve the exact output beyond
the description but some differences are bound to arise.
'''
    )
    parser.add_argument('aim_file', help='Input aim')
    parser.add_argument('-log', '-l', action='store_true', help='show processing log')
    parser.add_argument('-stat', '-s', action='store_true', help='show processing log')
    parser.add_argument('-verbose', '-v', action='store_true', help='show processing log')

    # Parse and display
    args = parser.parse_args()

    # Run program
    aix(**vars(args))

if __name__ == '__main__':
    main()
