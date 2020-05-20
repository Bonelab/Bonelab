import argparse
import os
import sys
import time
import math
import vtk
import vtkbone

from bonelab.util.echo_arguments import echo_arguments
from bonelab.util.time_stamp import message

def printMatrix4x4(m):
    print('[ {:8.4f}, {:8.4f}, {:8.4f}, {:8.4f} ]'.format(m.GetElement(0,0),m.GetElement(0,1),m.GetElement(0,2),m.GetElement(0,3)))
    print('[ {:8.4f}, {:8.4f}, {:8.4f}, {:8.4f} ]'.format(m.GetElement(1,0),m.GetElement(1,1),m.GetElement(1,2),m.GetElement(1,3)))
    print('[ {:8.4f}, {:8.4f}, {:8.4f}, {:8.4f} ]'.format(m.GetElement(2,0),m.GetElement(2,1),m.GetElement(2,2),m.GetElement(2,3)))
    print('[ {:8.4f}, {:8.4f}, {:8.4f}, {:8.4f} ]'.format(m.GetElement(3,0),m.GetElement(3,1),m.GetElement(3,2),m.GetElement(3,3)))
    
def keypress(obj, ev):
    renderer = obj.GetRenderWindow().GetRenderers().GetFirstRenderer()
    actorCollection = renderer.GetActors()
    actorCollection.InitTraversal()
    
    key = obj.GetKeySym()
    if key in 'h':
      print('Press the \'u\' key to see the actor transform matrix.')
    if key in 'u':
      for index in range(actorCollection.GetNumberOfItems()):
        nextActor = actorCollection.GetNextActor()
        if (nextActor.GetPickable()==1):
          printMatrix4x4(nextActor.GetMatrix())
          #message('nextActor: {:.0f}'.format(index))

def visualize_actors( pd1, pd2 ):

  mapper = vtk.vtkDataSetMapper()
  mapper.SetInputConnection( pd1 )

  actor = vtk.vtkActor()
  actor.SetMapper(mapper)
  actor.GetProperty().SetColor(0.8900, 0.8100, 0.3400)
  
  renderWindow = vtk.vtkRenderWindow()
  
  renderer = vtk.vtkRenderer()
  renderer.SetBackground(.4, .5, .7)

  renderWindow.AddRenderer( renderer )
  renderWindow.SetSize(2000,2000)

  renderer.AddActor( actor )
  
  if pd2 is not None:
    mapper2 = vtk.vtkDataSetMapper()
    mapper2.SetInputConnection( pd2 )
    actor2 = vtk.vtkActor()
    actor2.SetMapper(mapper2)
    actor2.PickableOff()
    actor2.GetProperty().SetColor(0.9500, 0.9500, 0.9500)
    renderer.AddActor( actor2 )
  
  renderer.ResetCamera()
  renderer.GetActiveCamera().Azimuth(0)
  renderer.GetActiveCamera().Elevation(0)
  renderer.GetActiveCamera().Dolly(1.0)
  renderer.ResetCameraClippingRange()

  renderWindowInteractor = vtk.vtkRenderWindowInteractor()
  #renderWindowInteractor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())
  renderWindowInteractor.SetRenderWindow( renderWindow )
  renderWindow.Render()

  message('Press the \'u\' key to see the actor transform matrix.')
  renderWindowInteractor.AddObserver(vtk.vtkCommand.KeyPressEvent, keypress, 1.0)
  renderWindowInteractor.Initialize()
  renderWindowInteractor.Start()
  
  return (actor.GetMatrix())

def JoinPolyData(pd1,pd2):
  input1 = vtk.vtkPolyData()
  input2 = vtk.vtkPolyData()
  
  input1.ShallowCopy( pd1 )
  input2.ShallowCopy( pd2 )
  
  appendFilter = vtk.vtkAppendPolyData()
  appendFilter.AddInputData( input1 )
  appendFilter.AddInputData( input2 )
  
  cleanFilter = vtk.vtkCleanPolyData()
  cleanFilter.SetInputConnection( appendFilter.GetOutputPort() )
  cleanFilter.Update()
  
  return cleanFilter

def CreateTimeSeries():
  bonemask_file = "/Users/skboyd/Documents/projects/FormLabs/radius_time_series/bonemask_4_r02.stl"
  
  bone1234 = vtk.vtkSTLReader()
  bone1234.SetFileName(bonemask_file)
  bone1234.Update()
  
  o_width = bone1234.GetOutput().GetBounds()[1] - bone1234.GetOutput().GetBounds()[0]
  o_height = bone1234.GetOutput().GetBounds()[3] - bone1234.GetOutput().GetBounds()[2]
  o_depth = bone1234.GetOutput().GetBounds()[5] - bone1234.GetOutput().GetBounds()[4]
  message('Four bones:',
          '{:8s} = {:8.2f} mm'.format('width',o_width),
          '{:8s} = {:8.2f} mm'.format('height',o_height),
          '{:8s} = {:8.2f} mm'.format('depth',o_depth))
  o_center = bone1234.GetOutput().GetCenter()
  
  cube = vtk.vtkCubeSource()
  shift = 0.1
  cube.SetBounds(
    bone1234.GetOutput().GetBounds()[0] - o_width * 0.05,
    bone1234.GetOutput().GetBounds()[1] + o_width * 0.05,
    bone1234.GetOutput().GetBounds()[2] - o_height * 0.05,
    bone1234.GetOutput().GetBounds()[3] + o_height * 0.05,
    bone1234.GetOutput().GetBounds()[4] + o_depth * 0.4,
    bone1234.GetOutput().GetBounds()[5] - o_depth * 0.4
  )
  cube.Update()
  
  message('Cube:',
          '{:8s} = {:8.2f} mm'.format('Bounds 0',cube.GetOutput().GetBounds()[0]),
          '{:8s} = {:8.2f} mm'.format('Bounds 1',cube.GetOutput().GetBounds()[1]),
          '{:8s} = {:8.2f} mm'.format('Bounds 2',cube.GetOutput().GetBounds()[2]),
          '{:8s} = {:8.2f} mm'.format('Bounds 3',cube.GetOutput().GetBounds()[3]),
          '{:8s} = {:8.2f} mm'.format('Bounds 4',cube.GetOutput().GetBounds()[4]),
          '{:8s} = {:8.2f} mm'.format('Bounds 5',cube.GetOutput().GetBounds()[5]))
  
  radius = 1.0
  post = vtk.vtkCylinderSource()
  post.SetHeight(9.0)
  post.SetRadius(radius)
  post.SetResolution(20)
  post.CappingOn()
  
  transform = vtk.vtkTransform()
  transform.RotateX(90.0)

  transformPost = vtk.vtkTransformFilter()
  transformPost.SetInputConnection( post.GetOutputPort() )
  transformPost.SetTransform( transform )
  transformPost.Update()

  post_center = transformPost.GetOutput().GetCenter()
  message('Post center:',
          '{:8s} = {:8.2f} mm'.format('X',post_center[0]),
          '{:8s} = {:8.2f} mm'.format('Y',post_center[1]),
          '{:8s} = {:8.2f} mm'.format('Z',post_center[2]))

  transform1 = vtk.vtkTransform()
  transform1.Translate(cube.GetOutput().GetBounds()[0]+(radius*2), cube.GetOutput().GetBounds()[2]+(radius*2), 2)

  transform2 = vtk.vtkTransform()
  transform2.Translate(cube.GetOutput().GetBounds()[0]+(radius*2), cube.GetOutput().GetBounds()[3]-(radius*2), 2)
  
  transform3 = vtk.vtkTransform()
  transform3.Translate(cube.GetOutput().GetBounds()[1]-(radius*2), cube.GetOutput().GetBounds()[2]+(radius*2), 2)
  
  transform4 = vtk.vtkTransform()
  transform4.Translate(cube.GetOutput().GetBounds()[1]-(radius*2), cube.GetOutput().GetBounds()[3]-(radius*2), 2)
  
  transformPost1 = vtk.vtkTransformFilter()
  transformPost1.SetInputConnection( transformPost.GetOutputPort() )
  transformPost1.SetTransform( transform1 )
  transformPost1.Update()
  
  transformPost2 = vtk.vtkTransformFilter()
  transformPost2.SetInputConnection( transformPost.GetOutputPort() )
  transformPost2.SetTransform( transform2 )
  transformPost2.Update()
  
  transformPost3 = vtk.vtkTransformFilter()
  transformPost3.SetInputConnection( transformPost.GetOutputPort() )
  transformPost3.SetTransform( transform3 )
  transformPost3.Update()
  
  transformPost4 = vtk.vtkTransformFilter()
  transformPost4.SetInputConnection( transformPost.GetOutputPort() )
  transformPost4.SetTransform( transform4 )
  transformPost4.Update()
  
  post12 = JoinPolyData(transformPost1.GetOutput(),transformPost2.GetOutput())
  post123 = JoinPolyData(post12.GetOutput(),transformPost3.GetOutput())
  post1234 = JoinPolyData(post123.GetOutput(),transformPost4.GetOutput())
  post1234.Update()
  
  cube_and_posts = JoinPolyData(cube.GetOutput(),post1234.GetOutput())
  
  mat4x4 = visualize_actors( cube_and_posts.GetOutputPort(), bone1234.GetOutputPort()  )
  #mat4x4 = visualize_actors( cube_and_posts.GetOutputPort(), None  )
  
  #ofile = "/Users/skboyd/Documents/projects/FormLabs/radius_time_series/bone_mask_post_and_table.stl" 
  #message('Writing STL file: '+ofile)
  #writer = vtk.vtkSTLWriter()
  #writer.SetFileName(ofile)
  #writer.SetFileTypeToASCII()
  #writer.SetInputConnection( cube_and_posts.GetOutputPort() )
  #writer.Write()
  
  ofile = "/Users/skboyd/Documents/projects/FormLabs/radius_time_series/bone_table.aim" 
  el_size_mm = [0.0760,0.0760,0.0760]
  
  message('Writing AIM file: '+ofile)
  whiteImage = vtk.vtkImageData()
  whiteImage.SetSpacing(el_size_mm)
  bounds = cube_and_posts.GetOutput().GetBounds()
  dim = [1,1,1]
  for i in range(3):
    dim[i] = (math.ceil((bounds[i*2+1]-bounds[i*2]) / el_size_mm[i]))
  whiteImage.SetDimensions(dim)
  whiteImage.SetExtent(0, dim[0] - 1, 0, dim[1] - 1, 0, dim[2] - 1)
  origin = [1,1,1]
  origin[0] = bounds[0] + el_size_mm[0] / 2
  origin[1] = bounds[2] + el_size_mm[1] / 2
  origin[2] = bounds[4] + el_size_mm[2] / 2
  whiteImage.SetOrigin(origin)
  whiteImage.AllocateScalars(vtk.VTK_CHAR,1)
  for i in range(whiteImage.GetNumberOfPoints()):
    whiteImage.GetPointData().GetScalars().SetTuple1(i, 127)
  pol2stenc = vtk.vtkPolyDataToImageStencil()
  pol2stenc.SetInputData( cube_and_posts.GetOutput() )
  pol2stenc.SetOutputOrigin( origin )
  pol2stenc.SetOutputSpacing( el_size_mm )
  pol2stenc.SetOutputWholeExtent( whiteImage.GetExtent() )
  pol2stenc.Update()
  imgstenc = vtk.vtkImageStencil()
  imgstenc.SetInputData(whiteImage)
  imgstenc.SetStencilConnection( pol2stenc.GetOutputPort() )
  imgstenc.ReverseStencilOff()
  imgstenc.SetBackgroundValue(0)
  imgstenc.Update()
  writer = vtkbone.vtkboneAIMWriter()
  writer.SetInputData( imgstenc.GetOutput() )
  writer.SetFileName(ofile)
  writer.Update()
  
  exit()
  
def CreateShapes(ofile, stl, el_size_mm,
                 visualize, text, overwrite, height, width):
  
  message("Checking if output exists and should overwrite.")
  if os.path.isfile(ofile) and not overwrite:
    result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(ofile))
    if result.lower() not in ['y', 'yes']:
      print('Not overwriting. Exiting...')
      os.sys.exit()
  
  message("Create vector text.")
  vecText = vtk.vtkVectorText()
  vecText.SetText(text)
    
  message("Apply linear extrusion.")
  extrude = vtk.vtkLinearExtrusionFilter()
  extrude.SetInputConnection( vecText.GetOutputPort() )
  extrude.SetExtrusionTypeToNormalExtrusion()
  extrude.SetVector(0, 0, 1 )
  extrude.SetScaleFactor (0.5)
  
  message("Apply triangle filter.")
  triangleFilter = vtk.vtkTriangleFilter()
  triangleFilter.SetInputConnection( extrude.GetOutputPort() )
  triangleFilter.Update()
  
  i_width = triangleFilter.GetOutput().GetBounds()[1] - triangleFilter.GetOutput().GetBounds()[0]
  i_height = triangleFilter.GetOutput().GetBounds()[3] - triangleFilter.GetOutput().GetBounds()[2]
  i_depth = triangleFilter.GetOutput().GetBounds()[5] - triangleFilter.GetOutput().GetBounds()[4]
  message('Input text:',
          '{:8s} = {:8.2f} mm'.format('width',i_width),
          '{:8s} = {:8.2f} mm'.format('height',i_height),
          '{:8s} = {:8.2f} mm'.format('depth',i_depth))

  if (width is not None and height is not None):
    message('ERROR: User can scale width or height, but not both.',
            '{:8s} = {:8.2f} mm'.format('width',width),
            '{:8s} = {:8.2f} mm'.format('height',height))
    exit()
  
  transform = vtk.vtkTransform()
  scale = 1
  
  if (width is not None or height is not None):
    if (width is not None):
      message('Scaling to width of {:.2f} mm'.format(width))
      scale = width/i_width
    if (height is not None):
      message('Scaling to width of {:.2f} mm'.format(height))
      scale = height/i_height
  else:
    message('No scaling being performed.')
  transform.Scale(scale,scale,1)

  transformFilter = vtk.vtkTransformFilter()
  transformFilter.SetInputConnection( triangleFilter.GetOutputPort() )
  transformFilter.SetTransform( transform )
  transformFilter.Update()

  o_width = transformFilter.GetOutput().GetBounds()[1] - transformFilter.GetOutput().GetBounds()[0]
  o_height = transformFilter.GetOutput().GetBounds()[3] - transformFilter.GetOutput().GetBounds()[2]
  o_depth = transformFilter.GetOutput().GetBounds()[5] - transformFilter.GetOutput().GetBounds()[4]
  o_center = transformFilter.GetOutput().GetCenter()
  
  message('Output text:',
          '{:8s} = {:8.2f} mm'.format('width',o_width),
          '{:8s} = {:8.2f} mm'.format('height',o_height),
          '{:8s} = {:8.2f} mm'.format('depth',o_depth))

  message('Create a backing for the text.')
  cube = vtk.vtkCubeSource()
  shift = 0.1
  cube.SetBounds(
    transformFilter.GetOutput().GetBounds()[0] - o_width * 0.05,
    transformFilter.GetOutput().GetBounds()[1] + o_width * 0.05,
    transformFilter.GetOutput().GetBounds()[2] - o_height * 0.1,
    transformFilter.GetOutput().GetBounds()[3] + o_height * 0.1,
    transformFilter.GetOutput().GetBounds()[4] - shift,
    transformFilter.GetOutput().GetBounds()[5] - shift - o_depth * 0.65
  )
  cube.Update()
  
  message('Create the sign by appending text to backing.')
  signBlock = JoinPolyData(cube.GetOutput(),transformFilter.GetOutput())
  
  if (visualize):

    # If an additional STL file is loaded, visualize it in addition to the sign
    if stl != '':
      message('Visualizing the sign and additional STL file.')
      stlReader = vtk.vtkSTLReader()
      stlReader.SetFileName(stl)
      stlReader.Update()
      mat4x4 = visualize_actors( signBlock.GetOutputPort(), stlReader.GetOutputPort() )

    # Or just visualize the sign
    else:
      message('Visualizing the sign.')
      mat4x4 = visualize_actors( signBlock.GetOutputPort(), None )
  
  #m4x4 = vtk.vtkMatrix4x4()
  #m4x4.SetElement(0,0,-0.0004)
  #m4x4.SetElement(0,1,-0.0228)
  #m4x4.SetElement(0,2, 0.9997)
  #m4x4.SetElement(0,3,27.8426)
  #
  #m4x4.SetElement(1,0,1.0000)
  #m4x4.SetElement(1,1,-0.0016)
  #m4x4.SetElement(1,2,0.0004)
  #m4x4.SetElement(1,3,9.7905)
  #
  #m4x4.SetElement(2,0,0.0016)
  #m4x4.SetElement(2,1,0.9997)
  #m4x4.SetElement(2,2,0.0228)
  #m4x4.SetElement(2,3,4.3662)
  #
  #m4x4.SetElement(3,0, 0.0)
  #m4x4.SetElement(3,1, 0.0)
  #m4x4.SetElement(3,2, 0.0)
  #m4x4.SetElement(3,3, 1.0)
  
  # The visualization allows user to transform sign block actor if desired.
  
  transformSign = vtk.vtkTransform()
  transformSign.SetMatrix(mat4x4)
  #transformSign.SetMatrix(m4x4)
  transformSignFilter = vtk.vtkTransformFilter()
  transformSignFilter.SetInputConnection( signBlock.GetOutputPort() )
  transformSignFilter.SetTransform( transformSign )
  transformSignFilter.Update()
    
  # Output file  
  if ofile != '':
    if os.path.splitext(ofile)[1] in ('.stl' or '.STL'):
      message('Writing STL file: '+ofile)
      writer = vtk.vtkSTLWriter()
      writer.SetFileName(ofile)
      #writer.SetFileTypeToBinary()
      writer.SetFileTypeToASCII()
      if stl != '':
        signBlockAll = JoinPolyData(stlReader.GetOutput(),transformSignFilter.GetOutput())
        writer.SetInputConnection( signBlockAll.GetOutputPort() )
      else:
        writer.SetInputConnection( transformSignFilter.GetOutputPort() )
      writer.Write()
      
    elif os.path.splitext(ofile)[1] in ('.aim' or '.AIM'):
      message('Writing AIM file: '+ofile)
      whiteImage = vtk.vtkImageData()
      whiteImage.SetSpacing(el_size_mm)
      bounds = transformSignFilter.GetOutput().GetBounds()
      dim = [1,1,1]
      for i in range(3):
        dim[i] = (math.ceil((bounds[i*2+1]-bounds[i*2]) / el_size_mm[i]))
      whiteImage.SetDimensions(dim)
      whiteImage.SetExtent(0, dim[0] - 1, 0, dim[1] - 1, 0, dim[2] - 1)
      origin = [1,1,1]
      origin[0] = bounds[0] + el_size_mm[0] / 2
      origin[1] = bounds[2] + el_size_mm[1] / 2
      origin[2] = bounds[4] + el_size_mm[2] / 2
      whiteImage.SetOrigin(origin)
      whiteImage.AllocateScalars(vtk.VTK_CHAR,1)
      for i in range(whiteImage.GetNumberOfPoints()):
        whiteImage.GetPointData().GetScalars().SetTuple1(i, 127)
      pol2stenc = vtk.vtkPolyDataToImageStencil()
      pol2stenc.SetInputData( transformSignFilter.GetOutput() )
      pol2stenc.SetOutputOrigin( origin )
      pol2stenc.SetOutputSpacing( el_size_mm )
      pol2stenc.SetOutputWholeExtent( whiteImage.GetExtent() )
      pol2stenc.Update()
      imgstenc = vtk.vtkImageStencil()
      imgstenc.SetInputData(whiteImage)
      imgstenc.SetStencilConnection( pol2stenc.GetOutputPort() )
      imgstenc.ReverseStencilOff()
      imgstenc.SetBackgroundValue(0)
      imgstenc.Update()
      writer = vtkbone.vtkboneAIMWriter()
      writer.SetInputData( imgstenc.GetOutput() )
      writer.SetFileName(ofile)
      #writer.SetProcessingLog(reader.GetProcessingLog())
      writer.Update()
      
    else:
      message('Unknown file type. No file written.')
  else:
    message('No output file designated. No file written.')

  exit()

def main():
    # Setup description
    description='''Generates a 3D model for printing.

A utility that can combine a name plate with a bone model for 3D printing.

There are two ways to use this:

1. You can simply create a name plate and save it as an STL or AIM file.
   The STL file can be used to 3D print, and the AIM file whatever you need.
2. You can create a name plate and append it to an input STL file.
   For example, you may have an STL file of a bone, and you can append a
   name plate to that file. The output file is a merged STL file for 3D
   printing.

Manual orientation of the name plate is possible in the visualization option.
Important keys are:
 'a' - actor mode (mouse, shift, control to manipulate) [REQUIRED]
 'c' - camera mode  (mouse, shift, control to manipulate)
 't' - trackball
 'j' - joystick
 'w' - wireframe
 's' - solid surface
 'u' – a user-defined function that prints the 4x4 transform to the terminal.
 'q' - quits

When you quit from the visualization the model will be printed with the new 
transform if you have applied one.

'''

    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blRapidPrototypeLetters",
        description=description
    )
    #parser.add_argument('input_filename', help='Input image file')
    parser.add_argument('--ofile', default='', help='Output image file (.stl or .aim allowed).')
    parser.add_argument('--stl', default='', help='Input STL file to add to scene.')
    parser.add_argument('--el_size_mm', type=float, nargs=3, default=[0.0607,0.0607,0.0607], help='Set element size (default: %(default)s)')
    parser.add_argument('--visualize', action='store_false', help='Visualize the STL mesh (default: %(default)s)')
    parser.add_argument('--text', default="Hello!", help='Letters for 3D rendering (default: %(default)s)')
    parser.add_argument('--width', type=float, default=None, help='Set width of text (default: %(default)s mm)')
    parser.add_argument('--height', type=float, default=None, help='Set height of text (default: %(default)s mm)')
    parser.add_argument('--overwrite', action='store_true', help='Overwrite output without asking (default: %(default)s)')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('RapidPrototypeLetters', vars(args)))

    # Run program
    CreateShapes(**vars(args))
    #CreateTimeSeries()

if __name__ == '__main__':
    main()
