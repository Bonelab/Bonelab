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
  
def ImageCentroids(input_filename,rapidprototyping,scantype):

    # Read input
    if not os.path.isfile(input_filename):
        os.sys.exit('[ERROR] Cannot find file \"{}\"'.format(input_filename))
    
    workingdir = os.path.dirname(input_filename)
    filename_base = os.path.splitext(os.path.splitext(os.path.basename(input_filename))[0])[0]
    
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
    print(formatter_int.format('!> N Labels  =',len(labels),'[1]'))
    for label in labels:
      print(formatter_int.format('!> Label  ',label,''))
    print(guard)
    
    centroid_dict = {} # dictionary
    
    print('!> Centroids')
    for label in labels:
      #if label != 0 and (label ==10 or label==9):
      if label != 0:
        centroid = get_centroid(img,label)
        print('!> Label {:3d}: {:8.4f} {:8.4f} {:8.4f}'.format(label,centroid[0],centroid[1],centroid[2]))
        centroid_dict[label] = centroid
    print(guard)
    
    if rapidprototyping:
      print('!> Helpful commands for rapid prototyping:')
      print('!> Type = {}'.format(scantype))
      print('!>')
      
      if scantype is "KUB":
        print('\n# Create the skeleton STL')
        print('{:s} '.format('blRapidPrototype img2stl --marching_cubes 0.5 --gaussian 1.2 --radius 2.0 ') + '{:s} {:s}/{:s}.stl'.format(input_filename,workingdir,filename_base))
        
        print('\n# Create cylinders to link bones')
        if centroid_dict.get(10) and centroid_dict.get(9):
          print('{:s} '.format('blRapidPrototype create_cylinder --scale 0.9 --endpoints')+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(10))+' '+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(9)) + '{:s} {:s}{:s}'.format(' --resolution 20 --radius 5.0',workingdir,'/rod_l1_to_l2.stl'))
        if centroid_dict.get(9) and centroid_dict.get(8):
          print('{:s} '.format('blRapidPrototype create_cylinder --scale 0.9 --endpoints')+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(9))+' '+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(8)) +  '{:s} {:s}{:s}'.format(' --resolution 20 --radius 5.0',workingdir,'/rod_l2_to_l3.stl'))
        if centroid_dict.get(8) and centroid_dict.get(7):
          print('{:s} '.format('blRapidPrototype create_cylinder --scale 0.9 --endpoints')+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(8))+' '+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(7)) +  '{:s} {:s}{:s}'.format(' --resolution 20 --radius 5.0',workingdir,'/rod_l3_to_l4.stl'))
        if centroid_dict.get(7) and centroid_dict.get(6):
          print('{:s} '.format('blRapidPrototype create_cylinder --scale 0.9 --endpoints')+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(7))+' '+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(6)) +  '{:s} {:s}{:s}'.format(' --resolution 20 --radius 5.0',workingdir,'/rod_l4_to_l5.stl'))
        if centroid_dict.get(6) and centroid_dict.get(5):
          print('{:s} '.format('blRapidPrototype create_cylinder --scale 0.9 --endpoints')+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(6))+' '+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(5)) +  '{:s} {:s}{:s}'.format(' --resolution 20 --radius 5.0',workingdir,'/rod_l5_to_sacrum.stl'))
        if centroid_dict.get(5) and centroid_dict.get(4):
          print('{:s} '.format('blRapidPrototype create_cylinder --scale 0.9 --endpoints')+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(5))+' '+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(4)) +  '{:s} {:s}{:s}'.format(' --resolution 20 --radius 5.0',workingdir,'/rod_sacrum_left_pelvis.stl'))
        if centroid_dict.get(5) and centroid_dict.get(3):
          print('{:s} '.format('blRapidPrototype create_cylinder --scale 0.9 --endpoints')+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(5))+' '+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(3)) +  '{:s} {:s}{:s}'.format(' --resolution 20 --radius 5.0',workingdir,'/rod_sacrum_right_pelvis.stl'))
        if centroid_dict.get(3) and centroid_dict.get(1):
          print('{:s} '.format('blRapidPrototype create_cylinder --scale 0.9 --endpoints')+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(3))+' '+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(1)) +  '{:s} {:s}{:s}'.format(' --resolution 20 --radius 5.0',workingdir,'/rod_right_pelvis_femur.stl'))
        if centroid_dict.get(4) and centroid_dict.get(2):
          print('{:s} '.format('blRapidPrototype create_cylinder --scale 0.9 --endpoints')+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(4))+' '+' '.join('{:8.2f}'.format(x) for x in centroid_dict.get(2)) +  '{:s} {:s}{:s}'.format(' --resolution 20 --radius 5.0',workingdir,'/rod_left_pelvis_femur.stl'))
        
        # find center from L1 (label 10) and extent of the image
        if centroid_dict.get(10):
          print('\n# Create base plate')
          center_base = [centroid_dict.get(10)[0],centroid_dict.get(10)[1],phys_dim[2]]
          plate_thickness = 10 # thickness in mm
          center_base_top = [center_base[0],center_base[1],phys_dim[2]-plate_thickness]
          print('{:s} '.format('blRapidPrototype create_cylinder --endpoints')+' '.join('{:8.2f}'.format(x) for x in center_base)+' '+' '.join('{:8.2f}'.format(x) for x in center_base_top) + '{:s}'.format(' --resolution 200 --radius 150.0 /Users/skboyd/Desktop/test/baseplate.stl'))
          
        print('\n# Connect the parts')
        print('{:s}'.format('blRapidPrototype add_stl \\'))
        print('  {:s}/{:s}.stl \\'.format(workingdir,filename_base))
        print('  {:s}{:s}'.format(workingdir,'/rod_l1_to_l2.stl \\'))
        print('  {:s}{:s}'.format(workingdir,'/rod_l2_to_l3.stl \\'))
        print('  {:s}{:s}'.format(workingdir,'/rod_l3_to_l4.stl \\'))
        print('  {:s}{:s}'.format(workingdir,'/rod_l4_to_l5.stl \\'))
        print('  {:s}{:s}'.format(workingdir,'/rod_l5_to_sacrum.stl \\'))
        print('  {:s}{:s}'.format(workingdir,'/rod_left_pelvis_femur.stl \\'))
        print('  {:s}{:s}'.format(workingdir,'/rod_right_pelvis_femur.stl \\'))
        #print('  {:s}{:s}'.format(workingdir,'/rod_sacrum_left_pelvis.stl \\'))
        #print('  {:s}{:s}'.format(workingdir,'/rod_sacrum_right_pelvis.stl \\'))
        print('  {:s}{:s}'.format(workingdir,'/baseplate.stl \\'))
        print('  {:s}/{:s}_model.stl'.format(workingdir,filename_base))
        
        print('\n# View the results')
        print('{:s}'.format('blRapidPrototype view_stl {}/{}_model.stl'.format(workingdir,filename_base)))
        
        
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
    parser.add_argument('--rapidprototyping', action='store_true', help='Print convenient commands (default: %(default)s)')
    parser.add_argument('--scantype', default='KUB', choices=['KUB', 'Chest'],help='Specify scan type (default: %(default)s)')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('ImageCentroids', vars(args)))

    # Run program
    ImageCentroids(**vars(args))

if __name__ == '__main__':
    main()
