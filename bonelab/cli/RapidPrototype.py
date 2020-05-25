#Imports
import argparse
import os
import sys
import time
import vtk
import vtkbone

from bonelab.util.echo_arguments import echo_arguments
from bonelab.util.time_stamp import message

def CheckExt(choices):
    class Act(argparse.Action):
        def __call__(self,parser,namespace,fname,option_string=None):
            ext = os.path.splitext(fname)[1][1:]
            if ext not in choices:
                option_string = '({})'.format(option_string) if option_string else ''
                parser.error("File ext must be {}{}".format(choices,option_string))
            else:
                setattr(namespace,self.dest,fname)

    return Act

def CreateSTL(input_filename, output_filename, gaussian, radius, 
              marching_cubes, decimation, visualize, overwrite):
  
  # Check if output exists and should overwrite
  if os.path.isfile(output_filename) and not overwrite:
    result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_filename))
    if result.lower() not in ['y', 'yes']:
      print('Not overwriting. Exiting...')
      os.sys.exit()
  
  # Read input
  if not os.path.isfile(input_filename):
    os.sys.exit('[ERROR] Cannot find file \"{}\"'.format(input_filename))

  message("Reading AIM file " + input_filename)
  reader = vtkbone.vtkboneAIMReader()
  reader.SetFileName(input_filename)
  reader.DataOnCellsOff()
  reader.Update()

  image = reader.GetOutput()
  message("Read %d points from AIM file." % image.GetNumberOfPoints())
  image_bounds = image.GetBounds()
  message("Image bounds:", (" %.4f"*6) % image_bounds)
  image_extent = image.GetExtent()
  message("Image extent:", (" %d"*6) % image_extent)

  message("Gaussian smoothing.")
  gauss = vtk.vtkImageGaussianSmooth()
  gauss.SetStandardDeviation(gaussian)
  gauss.SetRadiusFactor(radius)
  gauss.SetInputConnection(reader.GetOutputPort())
  gauss.Update()
  message("Total of %d voxels" % gauss.GetOutput().GetNumberOfCells())
  
  log ("Padding the data.")
  pad = vtk.vtkImageConstantPad()
  pad.SetConstant(0)
  pad.SetOutputWholeExtent(image_extent[0]-1,image_extent[1]+1,
                           image_extent[2]-1,image_extent[3]+1,
                           image_extent[4]-1,image_extent[5]+1)
  pad.SetInputConnection(gauss.GetOutputPort())
  pad.Update()
  message("Total of %d padded voxels" % pad.GetOutput().GetNumberOfCells())

  message("Extracting isosurface.")
  mcube = vtk.vtkImageMarchingCubes()
  mcube.SetValue(0,marching_cubes)
  mcube.SetInputConnection(pad.GetOutputPort())
  mcube.Update()
  message("Generated %d triangles" % mcube.GetOutput().GetNumberOfCells())
  #message(" mcube %s" % mcube.GetOutput())
  
  if (decimation>0.0 and decimation<1.0):
    message("Decimating the isosurface.")
    deci = vtk.vtkDecimatePro()
    deci.SetInputConnection(mcube.GetOutputPort())
    deci.SetTargetReduction(decimation) # 0 to 1, 0 is no decimation.
    deci.Update()
    message("Decimated to %d triangles" % deci.GetOutput().GetNumberOfCells())
    mesh = deci.GetOutputPort()
  else:
    message("No decimation of the isosurface will be performed.")
    mesh = mcube.GetOutputPort()
      
  if (visualize):
    
    ren = vtk.vtkRenderer()
    renWin = vtk.vtkRenderWindow()
    renWin.AddRenderer(ren)
    renWin.SetSize(600,600)
    renWin.SetWindowName("Bone Imaging Laboratory")
    
    iren = vtk.vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWin)
    
    mapper = vtk.vtkPolyDataMapper()
    mapper.ScalarVisibilityOff()
    mapper.SetInputConnection(mesh)
    #mapper.SetInputConnection(mcube.GetOutputPort())
    actor = vtk.vtkActor()
    #actor.GetProperty().SetColor(.5,.5,.5)
    actor.SetMapper(mapper)
    
    ren.AddActor(actor)
    ren.SetBackground(.8,.8,.8)
     
    iren.Initialize()
    renWin.Render()
    iren.Start()

  message("Writing STL file.")
  writer = vtk.vtkSTLWriter()
  writer.SetFileName(output_filename)
  writer.SetFileTypeToBinary()
  #writer.SetFileTypeToASCII()
  writer.SetInputConnection(mesh)
  #writer.SetInputConnection(mcube.GetOutputPort())
  message("Writing mesh to " + output_filename)
  writer.Write()
  
  message("Done.")

def aim2stl(input_file, output_file):

  if os.path.isfile(output_file) and not overwrite:
    result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_file))
    if result.lower() not in ['y', 'yes']:
      print('Not overwriting. Exiting...')
      os.sys.exit()
  
  writer = vtk.vtkSTLWriter()
  writer.SetFileName(output_file)
  writer.SetFileTypeToASCII()
  #writer.SetInputConnection( transformSignFilter.GetOutputPort() )
  #writer.Write()
  
def stl2aim(input_file, output_file):

  if os.path.isfile(output_file) and not overwrite:
    result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_file))
    if result.lower() not in ['y', 'yes']:
      print('Not overwriting. Exiting...')
      os.sys.exit()

  writer = vtkbone.vtkboneAIMWriter()
  writer.SetFileName(output_file)
  #writer.SetInputData( imgstenc.GetOutput() )
  #writer.SetProcessingLog(reader.GetProcessingLog())
  #writer.Update()
  
def add_stl(input_file1, input_file2, output_file):

  if os.path.isfile(output_file) and not overwrite:
    result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_file))
    if result.lower() not in ['y', 'yes']:
      print('Not overwriting. Exiting...')
      os.sys.exit()
  
  writer = vtk.vtkSTLWriter()
  writer.SetFileName(output_file)
  writer.SetFileTypeToASCII()
  #writer.SetInputConnection( transformSignFilter.GetOutputPort() )
  #writer.Write()
  
def subtract_stl(input_file1, input_file2, output_file):

  if os.path.isfile(output_file) and not overwrite:
    result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_file))
    if result.lower() not in ['y', 'yes']:
      print('Not overwriting. Exiting...')
      os.sys.exit()
  
  writer = vtk.vtkSTLWriter()
  writer.SetFileName(output_file)
  writer.SetFileTypeToASCII()
  #writer.SetInputConnection( transformSignFilter.GetOutputPort() )
  #writer.Write()
  
def create_sphere(output_file, radius, phi, theta, phi_start, phi_end, theta_start, theta_end, center, overwrite, func):

  if os.path.isfile(output_file) and not overwrite:
    result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_file))
    if result.lower() not in ['y', 'yes']:
      print('Not overwriting. Exiting...')
      os.sys.exit()

  sphere = vtk.vtkSphereSource()
  sphere.SetRadius( radius )
  sphere.SetPhiResolution( phi )
  sphere.SetThetaResolution( theta )
  sphere.SetStartPhi( phi_start )
  sphere.SetEndPhi( phi_end )
  sphere.SetStartTheta( theta_start )
  sphere.SetEndTheta( theta_end )
  sphere.SetCenter( center )
  sphere.Update()
  
  message('Sphere attributes:',
          '{:16s} = {:8.2f} mm'.format('radius',radius),
          '{:16s} = {:8d}'.format('phi resolution',phi),
          '{:16s} = {:8d}'.format('theta resolution',theta),
          '{:16s} = {:8d} degrees'.format('phi start',phi_start),
          '{:16s} = {:8d} degrees'.format('phi end',phi_end),
          '{:16s} = {:8d} degrees'.format('theta start',theta_start),
          '{:16s} = {:8d} degrees'.format('theta end',theta_end),
          '{:16s} = {:8.2f}, {:8.2f}, {:8.2f} mm'.format('center',center[0],center[1],center[2]))
  
  writer = vtk.vtkSTLWriter()
  writer.SetFileName(output_file)
  writer.SetFileTypeToASCII()
  writer.SetInputConnection( sphere.GetOutputPort() )
  writer.Write()
  message("Writing file " + output_file)
  
def create_cylinder(output_file, radius, height, resolution, capping, center, overwrite, func):

  if os.path.isfile(output_file) and not overwrite:
    result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_file))
    if result.lower() not in ['y', 'yes']:
      print('Not overwriting. Exiting...')
      os.sys.exit()

  cylinder = vtk.vtkCylinderSource()
  cylinder.SetHeight( height )
  cylinder.SetResolution( resolution )
  cylinder.SetCapping( capping )
  cylinder.SetCenter( center )
  cylinder.Update()
  
  message('Cylinder attributes:',
          '{:16s} = {:8.2f} mm'.format('radius',radius),
          '{:16s} = {:8.2f} mm'.format('height',height),
          '{:16s} = {:8d}'.format('resolution',resolution),
          '{:16s} = {:>8s}'.format('capping',('True' if capping else 'False')),
          '{:16s} = {:8.2f}, {:8.2f}, {:8.2f} mm'.format('center',center[0],center[1],center[2]))
    
  writer = vtk.vtkSTLWriter()
  writer.SetFileName(output_file)
  writer.SetFileTypeToASCII()
  writer.SetInputConnection( cylinder.GetOutputPort() )
  writer.Write()
  message("Writing file " + output_file)
  
def create_cube(output_file, bounds, overwrite, func):

  if os.path.isfile(output_file) and not overwrite:
    result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_file))
    if result.lower() not in ['y', 'yes']:
      print('Not overwriting. Exiting...')
      os.sys.exit()

  cube = vtk.vtkCubeSource()
  cube.SetBounds( bounds )
  cube.Update()
  
  message('Cube attributes:',
          '{:16s}'.format('bounds'),
          '{:16s} = {:8.2f}, {:8.2f} mm'.format('  X  min, max',bounds[0],bounds[1]),
          '{:16s} = {:8.2f}, {:8.2f} mm'.format('  Y  min, max',bounds[2],bounds[3]),
          '{:16s} = {:8.2f}, {:8.2f} mm'.format('  Z  min, max',bounds[4],bounds[5]),
          '{:16s}'.format('length'),
          '{:16s} = {:8.2f} mm'.format('  X',(bounds[1]-bounds[0])),
          '{:16s} = {:8.2f} mm'.format('  Y',(bounds[3]-bounds[2])),
          '{:16s} = {:8.2f} mm'.format('  Z',(bounds[5]-bounds[4])))
  
  writer = vtk.vtkSTLWriter()
  writer.SetFileName(output_file)
  writer.SetFileTypeToASCII()
  writer.SetInputConnection( cube.GetOutputPort() )
  writer.Write()
  
def main():
    # Setup description
    description='''
A general utility for creating STL files used for rapid prototyping from 
AIMs and back again.

This is a collection of utilities that together provide significant 
opportunities for creating complex STL files from input AIMs as well
as conversion back to an AIM format. 

aim2stl         : takes a thresholded AIM file and applies isosurface for STL
stl2aim         : takes an STL and converts to a thresholded AIM
add_stl         : add two STL files together
subtract_stl    : subtract one STL file from another
create_sign     : make a sign with text

create_sphere   : make a sphere
create_cylinder : make a cylinder
create_cube     : make a cube

Input AIM must be type 'char'. STL mesh properties can be controlled 
by setting gaussian smoothing and isosurface. The number of polygons
can be reduced (decimation).

For now only AIM files can be used as input.
'''
    epilog='''
To see the options for each of the utilities, type something like this:
$ blRapidPrototype create_cube --help
'''
    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blRapidPrototype",
        description=description,
        epilog=epilog
    )
    subparsers = parser.add_subparsers()
    
    # parser for create_sphere
    parser_create_sphere = subparsers.add_parser('create_sphere')
    parser_create_sphere.add_argument('output_file', help='Output STL image file name')
    parser_create_sphere.add_argument('--radius', type=float, default=0.5, help='Sphere radius (default: %(default)s)')
    parser_create_sphere.add_argument('--phi', type=int, default=8, metavar='RES', help='Sphere phi_resolution (default: %(default)s)')
    parser_create_sphere.add_argument('--theta', type=int, default=8, metavar='RES', help='Sphere theta_resolution (default: %(default)s)')
    parser_create_sphere.add_argument('--phi_start', type=int, default=0, choices=range(0,180), metavar='RES', help='Sphere phi start angle (default: %(default)s)')
    parser_create_sphere.add_argument('--phi_end', type=int, default=180, choices=range(0,180), metavar='RES', help='Sphere phi end angle (default: %(default)s)')
    parser_create_sphere.add_argument('--theta_start', type=int, default=0, choices=range(0,360), metavar='RES', help='Sphere theta start angle (default: %(default)s)')
    parser_create_sphere.add_argument('--theta_end', type=int, default=360, choices=range(0,360), metavar='RES', help='Sphere theta end angle (default: %(default)s)')
    parser_create_sphere.add_argument('--center', type=float, nargs=3, default=[0,0,0], metavar='0', help='Sphere center (default: %(default)s)')
    parser_create_sphere.add_argument('--overwrite', action='store_true', help='Overwrite output without asking (default: %(default)s)')
    parser_create_sphere.set_defaults(func=create_sphere)
        
    # parser for create_cylinder
    parser_create_cylinder = subparsers.add_parser('create_cylinder')
    parser_create_cylinder.add_argument('output_file', action=CheckExt({'stl','STL'}), help='Output STL image file name')
    parser_create_cylinder.add_argument('--radius', type=float, default=0.5, help='Cylinder radius (default: %(default)s)')
    parser_create_cylinder.add_argument('--height', type=float, default=1.0, help='Cylinder height (default: %(default)s)')
    parser_create_cylinder.add_argument('--resolution', type=int, default=6, metavar='RES', help='Cylinder resolution (default: %(default)s)')
    parser_create_cylinder.add_argument('--capping', action='store_false', help='Cylinder capping (default: %(default)s)')
    parser_create_cylinder.add_argument('--center', type=float, nargs=3, default=[0,0,0], metavar='0', help='Cylinder center (default: %(default)s)')
    parser_create_cylinder.add_argument('--overwrite', action='store_true', help='Overwrite output without asking (default: %(default)s)')
    parser_create_cylinder.set_defaults(func=create_cylinder)
    
    # parser for create_cube
    parser_create_cube = subparsers.add_parser('create_cube')
    parser_create_cube.add_argument('output_file', help='Output STL image file name')
    parser_create_cube.add_argument('--bounds', type=float, nargs=6, default=[0,1,0,1,0,1], metavar='0', help='Cube bounds (default: %(default)s)')
    parser_create_cube.add_argument('--overwrite', action='store_true', help='Overwrite output without asking (default: %(default)s)')
    parser_create_cube.set_defaults(func=create_cube)
    
    
    #parser.add_argument('input_filename', help='Input image file')
    #parser.add_argument('output_filename', help='Output image file')
    #parser.add_argument('-g', '--gaussian', type=float, default=0.7, help='Gaussian standard deviation (default: %(default)s)')
    #parser.add_argument('-r', '--radius', type=float, default=1.0, help='Gaussian radius support (default: %(default)s)')
    #parser.add_argument('-m', '--marching_cubes', type=float, default=50.0, help='Marching cubes threshold (default: %(default)s)')
    #parser.add_argument('-d', '--decimation', type=float, default=0.85, help='Decimation 0 to 1. To skip set to 1 (default: %(default)s)')
    #parser.add_argument('-v', '--visualize', action='store_false', help='Visualize the STL mesh (default: %(default)s)')
    #parser.add_argument('-o', '--overwrite', action='store_true', help='Overwrite output without asking (default: %(default)s)')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('RapidPrototype', vars(args)))
        
    # Run program
    #print(args)
    args.func(**vars(args))

    #CreateSTL(**vars(args))

if __name__ == '__main__':
    main()
