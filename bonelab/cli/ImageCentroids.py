# Imports
import argparse
import os
import vtk
import math
import numpy as np

from vtk.util.numpy_support import vtk_to_numpy

from bonelab.util.echo_arguments import echo_arguments
from bonelab.io.vtk_helpers import get_vtk_reader

def get_centroid(image,label):
  
  if label == 0:
    return (0,0,0)
    
  origin = image.GetOrigin()
  spacing = image.GetSpacing()
  dim = image.GetDimensions()

  img = vtk_to_numpy(image.GetPointData().GetScalars())
  
  # vtk arrays are slice (z), row (y), column (x)
  img = img.reshape([dim[2],dim[1],dim[0]]).transpose() # remove the transpose if necessary
  matches = np.transpose((img == label).nonzero())
  centroid = np.mean(matches, axis=0) # measured in voxels
  centroid = [m*x+b for m,x,b in zip(centroid,spacing,origin)] # measured in global coordinates
  
  return centroid
  
def ImageCentroids(input_filename,links):

    # Read input
    for filename in [input_filename]:
        if not os.path.isfile(filename):
            os.sys.exit('[ERROR] Cannot find file \"{}\"'.format(filename))
    
    image_reader = get_vtk_reader(input_filename)
    if image_reader is None:
        os.sys.exit('[ERROR] Cannot find reader for file \"{}\"'.format(input_filename))
    
    print('Reading input image ' + input_filename)
    image_reader.SetFileName(input_filename)
    image_reader.Update()
    
    img = image_reader.GetOutput()
    
    # Check if valid data type
    # It only works with VTK_CHAR and VTK_UNSIGNED_CHAR file types (for now)
    if (img.GetScalarType() != vtk.VTK_CHAR | img.GetScalarType() != vtk.VTK_UNSIGNED_CHAR):
      os.sys.exit('\n[ERROR] Only image type VTK_CHAR or VTK_UNSIGNED_CHAR is valid for input.\n        Input file is type is {}.'.format(img.GetScalarTypeAsString()))
      
    # Provide information about the input file
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
    formatter_float='{{:<{}}} {{:>15.4f}} {{}}'.format(max_length)
    formatter_int  ='{{:<{}}} {{:>15d}} {{}}'.format(max_length)
    for measure, outcome in data.items():
        if measure == '!> TV        =':
          unit = '[mm^3]'
        else:
          unit = '[1]'
        print(formatter_float.format(measure, outcome, unit))
    print(guard)
    
    labels = np.unique(array)
    print(formatter_int.format('!> Labels    =',len(labels),'[1]'))
    for label in labels:
      print(formatter_int.format('!> Label  ',label,''))
    print(guard)
    
    centroid_dict = {} # dictionary
    
    print('!> Centroids')
    for label in labels:
      if label != 0:
        centroid = get_centroid(img,label)
        print('!> Label {:3d}: {:8.4f} {:8.4f} {:8.4f}'.format(label,centroid[0],centroid[1],centroid[2]))
        centroid_dict[label] = centroid
    print(guard)
    
    formatter_two_tuples ='{:>20s} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f} {:.3f}'
    
    if links:
      # Make any links we can
      if centroid_dict.get(10) and centroid_dict.get(9):
        print('{:>20s}: '.format('l1_to_l2')+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(10))+' '+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(9)))
      if centroid_dict.get(9) and centroid_dict.get(8):
        print('{:>20s}: '.format('l2_to_l3')+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(9))+' '+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(8)))
      if centroid_dict.get(8) and centroid_dict.get(7):
        print('{:>20s}: '.format('l3_to_l4')+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(8))+' '+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(7)))
      if centroid_dict.get(7) and centroid_dict.get(6):
        print('{:>20s}: '.format('l4_to_l5')+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(7))+' '+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(6)))
      if centroid_dict.get(6) and centroid_dict.get(5):
        print('{:>20s}: '.format('l5_to_sacrum')+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(6))+' '+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(5)))
      if centroid_dict.get(5) and centroid_dict.get(4):
        print('{:>20s}: '.format('sacrum_left_pelvis')+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(5))+' '+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(4)))
      if centroid_dict.get(5) and centroid_dict.get(3):
        print('{:>20s}: '.format('sacrum_right_pelvis')+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(5))+' '+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(3)))
      if centroid_dict.get(3) and centroid_dict.get(1):
        print('{:>20s}: '.format('right_pelvis_femur')+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(3))+' '+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(1)))
      if centroid_dict.get(4) and centroid_dict.get(2):
        print('{:>20s}: '.format('left_pelvis_femur')+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(4))+' '+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(2)))
      
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
    parser.add_argument('--links', action='store_true', help='Output links for rapid prototyping (default: %(default)s)')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('ImageCentroids', vars(args)))

    # Run program
    ImageCentroids(**vars(args))

if __name__ == '__main__':
    main()
