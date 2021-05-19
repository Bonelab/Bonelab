
# Imports
import argparse
import os
import vtkbone
from vtk.util.numpy_support import vtk_to_numpy
from bonelab.io.vtk_helpers import get_vtk_reader
import numpy as np
import re
import math

# vtkNIFTIImageReader
# vtkboneAIMReader

def aix(infile, log, stat, histo, verbose, meta):
    # Python 2/3 compatible input
    from six.moves import input

    debug = False
    
    # Read input
    if not os.path.isfile(infile):
        os.sys.exit('[ERROR] Cannot find file \"{}\"'.format(input_filename))

    reader = get_vtk_reader(infile)
    if reader is None:
        os.sys.exit('[ERROR] Cannot find reader for file \"{}\"'.format(input_filename))

    #print('Reading input image ' + infile)
    reader.SetFileName(infile)
    reader.Update()
    image = reader.GetOutput()

    # Precompute some values
    guard = '!-------------------------------------------------------------------------------'
    phys_dim = [x*y for x,y in zip(image.GetDimensions(), image.GetSpacing())]
    position = [math.floor(x/y) for x,y in zip(image.GetOrigin(), image.GetSpacing())]
    size = os.path.getsize(infile)
    names = ['Bytes', 'KBytes', 'MBytes', 'GBytes']
    n_image_voxels = image.GetDimensions()[0] * image.GetDimensions()[1] * image.GetDimensions()[2]
    voxel_volume = image.GetSpacing()[0] * image.GetSpacing()[1] * image.GetSpacing()[2]
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
      print('!> pos                            {: >6}  {: >6}  {: >6}'.format(*position))
      print('!> element size in mm             {:.4f}  {:.4f}  {:.4f}'.format(*image.GetSpacing()))
      print('!> phys dim in mm                 {:.4f}  {:.4f}  {:.4f}'.format(*phys_dim))
      print('!>')
      print('!> Type of data               {}'.format(image.GetScalarTypeAsString()))
      print('!> Total memory size          {:.1f} {: <10}'.format(size, names[i]))
      print(guard)

    # Print log
    if log:
        if (reader.GetClassName() == "vtkboneAIMReader"):
          print(reader.GetProcessingLog())
        else:
          print('!- No log available.')

    # Print meta data information
    if meta:
        if (reader.GetClassName() == "vtkboneAIMReader"):
          log = reader.GetProcessingLog()
        
        if (not log):
          print('!- No meta data available.')
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

    # Print Histogram
    if histo:
        array = vtk_to_numpy(image.GetPointData().GetScalars()).ravel()

        # The range of values and number of bins are hard-coded. If fewer bins
        # or a different range (i.e. 0 to 127 for char) are wanted then simply 
        # adjust these settings
        if (image.GetScalarTypeAsString()=="char"):
          nRange = [-128,127]
          nBins = 128
        elif (image.GetScalarTypeAsString()=="short"):
          nRange = [-32768,32767]
          nBins = 128
        else:
          print('!- Unknown data type: {}'.format(image.GetScalarTypeAsString()))
      
        # https://numpy.org/doc/stable/reference/generated/numpy.histogram.html
        hist,bin_edges = np.histogram(array,nBins,nRange,None,None,False)
        nValues = sum(hist)

        print('!>  {:4s} ({:.3s}) : Showing {:d} histogram bins over range of {:d} to {:d}.'.format('IND','QTY',nBins,*nRange))
        for bin in range(nBins):
          index = nRange[0] + int(bin * (nRange[1]-nRange[0])/(nBins-1))
          count = hist[bin]/nValues # We normalize so total count = 1
          nStars = int(count*100)
          if (nStars > 60):
            nStars = 60 # just prevents it from wrapping in the terminal
          print('!> {:4d} ({:.3f}): {:s}'.format(index,count,nStars*'*'))
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
  
    # Setup description
    description='''AIM information examine.

A reimplementation of the seminal SCANCO program `aix`. All
efforts have been made to preserve the exact output beyond
the description but some differences are bound to arise.

Allowed inputs include .aim, .nii
'''
    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="aix",
        description=description
    )
    parser.add_argument('infile', help='Input file')
    parser.add_argument('--log', action='store_true', help='show processing log')
    parser.add_argument('--stat', action='store_true', help='show statistics on data')
    parser.add_argument('--histo', action='store_true', help='show histogram of data')
    parser.add_argument('--verbose', action='store_true', help='show data values')
    parser.add_argument('--meta', action='store_true', help='show scan meta data')

    # Parse and display
    args = parser.parse_args()
    
    # Run program
    aix(**vars(args))

if __name__ == '__main__':
    main()
