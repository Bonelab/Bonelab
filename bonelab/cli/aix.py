
# Imports
import argparse
import os
import vtkbone
from vtk.util.numpy_support import vtk_to_numpy
import numpy as np
import re

def aix(aim_file, log, stat, verbose, meta):
    # Python 2/3 compatible input
    from six.moves import input

    debug = False
    
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
    n_image_voxels = image.GetDimensions()[0] * image.GetDimensions()[1] * image.GetDimensions()[2]
    voxel_volume = reader.GetElementSize()[0] * reader.GetElementSize()[1] * reader.GetElementSize()[2]
    i = 0
    while int(size) > 1024 and i < len(names):
        i+=1
        size = size / 2.0**10

    if (not meta):
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

    # Print meta data information
    if meta:
        log = reader.GetProcessingLog()
        
        if (not log):
          print("None")
          exit(1)
          
        meta_list=[]

        p_site = re.compile('^Site[ ]+([0-9]+)')
        p_patient = re.compile('^Index Patient[ ]+([0-9]+)')
        p_measurement = re.compile('^Index Measurement[ ]+([0-9]+)')
        p_name = re.compile('^Patient Name[ ]+ ([\w\-\(\' ]+)')
        p_strip_trailing_zeros = re.compile('[ \t]+$')

        for line in iter(log.splitlines()):
          try:
              m = p_site.search(line)
              if (m):
                name = 'Site'
                value = m.group(1)
                if (value == '20'): value = 'RL'
                if (value == '21'): value = 'RR'
                if (value == '38'): value = 'TL'
                if (value == '39'): value = 'TR'      
                meta_list.append(value)            
                if (debug): print('{0:25s}[{1:s}]'.format("Site",value))

              m = p_patient.search(line)
              if (m):
                name = 'Index Patient'
                value = m.group(1)
                meta_list.append(value)            
                if (debug): print('{0:25s}[{1:s}]'.format("Index Patient",value))

              m = p_measurement.search(line)
              if (m):
                name = 'Index Measurement'
                value = m.group(1)
                meta_list.append(value)            
                if (debug): print('{0:25s}[{1:s}]'.format("Index Measurement",value))

              m = p_name.search(line)
              if (m):
                name = 'Patient Name'
                name_with_trailing_zeros = m.group(1)
                value = p_strip_trailing_zeros.sub('',name_with_trailing_zeros)
                meta_list.append(value)            
                if (debug): print('{0:25s}[{1:s}]'.format("Patient Name",value))
                
          except AttributeError:
              print("Error: Cannot find meta data.")
              exit(1)

        for item in meta_list:
          print('\"{0:s}\" '.format(item), end = '')
        print('\n',end='')
        #print('\"{0}\" \"{1}\" \"{2}\" \"{3}\"'.format(meta_list[0],meta_list[1],meta_list[2],meta_list[3]))

    # Print Stat
    if stat:
        array = vtk_to_numpy(image.GetPointData().GetScalars()).ravel()
        data = {
            '!> Max       =':      array.max(),
            '!> Min       =':      array.min(),
            '!> Mean      =':      array.mean(),
            '!> SD        =':      array.std(),
            '!> TV        =':      n_image_voxels*voxel_volume
        }

        max_length = 0
        for measure, outcome in data.items():
            max_length = max(max_length, len(measure))
        formatter='{{:<{}}} {{:>15.4f}} {{}}'.format(max_length)
        for measure, outcome in data.items():
            if measure == '!> TV        =':
              unit = '[mm^3]'
            else:
              unit = '[1]'
            print(formatter.format(measure, outcome, unit))
        print(guard)

    # Print verbose
    if verbose:
        half_slice_size = image.GetDimensions()[0] * image.GetDimensions()[1] * 0.5
        array = vtk_to_numpy(image.GetPointData().GetScalars())
        array = array.reshape(image.GetDimensions()).transpose(2, 1, 0)
        i = 1
        it = np.nditer(array, flags=['multi_index'])
        while not it.finished:
            print("{} {}".format(it.multi_index, it[0]))

            # Print a half slice at a time
            if i%half_slice_size == 0:
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
    parser.add_argument('--log', '--l', action='store_true', help='show processing log')
    parser.add_argument('--stat', '--s', action='store_true', help='show statistics on data')
    parser.add_argument('--verbose', '--v', action='store_true', help='show data values')
    parser.add_argument('--meta', '--m', action='store_true', help='show basic scan meta data')

    # Parse and display
    args = parser.parse_args()

    # Run program
    aix(**vars(args))

if __name__ == '__main__':
    main()
