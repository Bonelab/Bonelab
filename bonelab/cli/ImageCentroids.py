# Imports
import argparse
import os
import vtk
import math
import numpy as np

from vtk.util.numpy_support import vtk_to_numpy

from bonelab.util.echo_arguments import echo_arguments
from bonelab.io.vtk_helpers import get_vtk_reader


#def ImageCentroids(input_filename, segmentation_filename, window, level, nThreads, opacity):
def ImageCentroids(input_filename):
    # Read input
    for filename in [input_filename]:
        if not os.path.isfile(filename):
            os.sys.exit('[ERROR] Cannot find file \"{}\"'.format(filename))
    
    # Read the input
    image_reader = get_vtk_reader(input_filename)
    if image_reader is None:
        os.sys.exit('[ERROR] Cannot find reader for file \"{}\"'.format(input_filename))

    print('Reading input image ' + input_filename)
    image_reader.SetFileName(input_filename)
    image_reader.Update()
    
    img = image_reader.GetOutput()
    
    # Only works with VTK_CHAR file type (for now)
    if (img.GetScalarType() != vtk.VTK_CHAR | img.GetScalarType() != vtk.VTK_UNSIGNED_CHAR):
      os.sys.exit('[ERROR] Only image type VTK_CHAR or VTK_UNSIGNED_CHAR is valid for input. Type is {}.'.format(img.GetScalarTypeAsString()))
      
    print('Image data:')
    print(' type = {}'.format(img.GetScalarTypeAsString()))
    print(' type min = {}, max = {}'.format(img.GetScalarTypeMin(),img.GetScalarTypeMax()))
    print(' origin = {}'.format(img.GetOrigin()))
    print(' spacing = {}'.format(img.GetSpacing()))
    
    guard = '!-------------------------------------------------------------------------------'
    phys_dim = [x*y for x,y in zip(img.GetDimensions(), img.GetSpacing())]
    position = [math.floor(x/y) for x,y in zip(img.GetOrigin(), img.GetSpacing())]
    size = os.path.getsize(input_filename)
    names = ['Bytes', 'KBytes', 'MBytes', 'GBytes']
    n_image_voxels = img.GetDimensions()[0] * img.GetDimensions()[1] * img.GetDimensions()[2]
    voxel_volume = img.GetSpacing()[0] * img.GetSpacing()[1] * img.GetSpacing()[2]
    i = 0
    while int(size) > 1024 and i < len(names):
        i+=1
        size = size / 2.0**10
    
    
    print(guard)
    print('!>')
    print('!> dim                            {: >6}  {: >6}  {: >6}'.format(*img.GetDimensions()))
    print('!> off                                 x       x       x')
    print('!> pos                            {: >6}  {: >6}  {: >6}'.format(*position))
    print('!> element size in mm             {:.4f}  {:.4f}  {:.4f}'.format(*img.GetSpacing()))
    print('!> phys dim in mm                 {:.4f}  {:.4f}  {:.4f}'.format(*phys_dim))
    print('!>')
    print('!> Type of data               {}'.format(img.GetScalarTypeAsString()))
    print('!> Total memory size          {:.1f} {: <10}'.format(size, names[i]))
    print(guard)
    
    
    array = vtk_to_numpy(img.GetPointData().GetScalars()).ravel()
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
    
    labels = np.unique(array)
    print('number of labels is {}'.format(len(labels)))
    
    for i in labels:
      print('label is {}'.format(i))
    #print(img.GetPointData().GetScalars())
    
    components = vtk.vtkImageExtractComponents()
    #com = vtk.vtkCenterOfMass()
    components.SetInputConnection(image_reader.GetOutputPort())
    components.Update()
    print('number of components is {}'.format(components.GetNumberOfComponents()))
    
    ar = vtk_to_numpy(img.GetPointData().GetScalars())
    print(ar.ndim)
    
    #vtkExtractSelection()
    #vtkThresholdFilter()
    
    #segLUT = vtk.vtkLookupTable()
    
    #pack = vtk.vtkPackLabels()
    
    
def main():
    # Setup description
    description='''Calculate centroids of segmented components

Reads in a segmented file and outputs the centroid of each label
in the image.
'''

    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blImageCentroids",
        description=description
    )
    parser.add_argument('input_filename', help='Input image')
#    parser.add_argument('--level',
#                        default=float(0), type=float,
#                        help='The initial level')
#    parser.add_argument('--nThreads', '-n',
#                        default=int(1), type=int,
#                        help='Number of threads for each image slice visualizer (default: %(default)s)')
#    parser.add_argument('--opacity', '-o',
#                        default=float(0.25), type=float,
#                        help='The opacity of the segmentation between zero and one (default: %(default)s)')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('ImageCentroids', vars(args)))

    # Run program
    ImageCentroids(**vars(args))

if __name__ == '__main__':
    main()
