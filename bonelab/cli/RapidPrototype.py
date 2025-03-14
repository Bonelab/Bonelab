#Imports
import argparse
import os
import sys
import time
import math
import vtk
import vtkbone
import numpy as np

from bonelab.util.echo_arguments import echo_arguments
from bonelab.util.time_stamp import message
from vtk.util.numpy_support import vtk_to_numpy
from bonelab.io.vtk_helpers import get_vtk_reader, get_vtk_writer, handle_filetype_writing_special_cases

def CheckExt(choices):
    class Act(argparse.Action):
        def __call__(self,parser,namespace,fname,option_string=None):
            if isinstance(fname,str): # case of a string argument
              ext = os.path.splitext(fname)[1][1:]
              if ext not in choices:
                  option_string = '({})'.format(option_string) if option_string else ''
                  parser.error("File extension must be {}{}".format(choices,option_string))
              else:
                  setattr(namespace,self.dest,fname)
            elif isinstance(fname,list): # case of a list argument containing strings (e.g., nargs='*')
              for f in fname:
                ext = os.path.splitext(f)[1][1:]
                if ext not in choices:
                    option_string = '({})'.format(option_string) if option_string else ''
                    parser.error("File extension must be {}{}".format(choices,option_string))
                else:
                    setattr(namespace,self.dest,fname)
              
            else:
              parser.error("Data type cannot be processed: {}".format(type(fname)))

    return Act

class Range(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __eq__(self, other):
        return self.start <= other <= self.end

    def __contains__(self, item):
        return self.__eq__(item)

    def __iter__(self):
        yield self

    def __str__(self):
        return '[{0},{1}]'.format(self.start, self.end)

def printMatrix4x4(m):
    precision = 4
    delimiter=','
    formatter = '{{:8.{}f}}'.format(precision)
        
    for i in range(4):
      row_data = delimiter.join([formatter.format(float(m.GetElement(i,j))) for j in range(4)])
      print('[ '+row_data+' ]')
        
def diagonal(x, y, z):
    return math.sqrt(math.pow(x,2)+math.pow(y,2)+math.pow(z,2))

def histogram(image):
    array = vtk_to_numpy(image.GetPointData().GetScalars()).ravel()
    guard = '!-------------------------------------------------------------------------------'

    if (array.min() < -128):
      range_min = -32768
    elif (array.min() < 0):
      range_min = -128
    else:
      range_min = 0
    
    if (array.max() > 255):
      range_max = 32767
    elif (array.max() > 127):
      range_max = 255
    else:
      range_max = 127

    nRange = [range_min, range_max]
    nBins = 128
    
    # https://numpy.org/doc/stable/reference/generated/numpy.histogram.html
    hist,bin_edges = np.histogram(array,nBins,nRange,None,None,False)
    nValues = sum(hist)

    print(guard)
    print('!>  {:4s} ({:.3s}) : Showing {:d} histogram bins over range of {:d} to {:d}.'.format('IND','QTY',nBins,*nRange))
    for bin in range(nBins):
      index = nRange[0] + int(bin * (nRange[1]-nRange[0])/(nBins-1))
      count = hist[bin]/nValues # We normalize so total count = 1
      nStars = int(count*100)
      if (count>0 and nStars==0): # Ensures at least one * if the histogram bin is not zero
        nStars = 1
      if (nStars > 60):
        nStars = 60 # just prevents it from wrapping in the terminal
      print('!> {:4d} ({:.3f}): {:s}'.format(index,count,nStars*'*'))
    print(guard)

def applyTransform(transform, polydata):
    
    if "None" in transform: # do nothing
      return polydata
    
    try:    
       mat4x4 = readTransform(transform)
    except OSError:
       raise SystemError('File could not be read: ' + transform)
    
    message('User supplied transform applied')
    printMatrix4x4(mat4x4)
    
    transform = vtk.vtkTransform()
    transform.SetMatrix(mat4x4)

    transformFilter = vtk.vtkTransformFilter()
    transformFilter.SetInputConnection( polydata.GetOutputPort() )
    transformFilter.SetTransform( transform )
    transformFilter.Update()
    
    return transformFilter

def readTransform(input_file):
    
    t_mat = np.loadtxt(fname=input_file, skiprows=2)
    rotation = t_mat[:4, :4]
    
    matrix = vtk.vtkMatrix4x4()
    for i in range(4):
      for j in range(4):
        matrix.SetElement(i,j,rotation[i,j])

    return matrix

def writeTransform(output_file,matrix,check_for_overwrite=True):
  
    if os.path.isfile(output_file) and check_for_overwrite:
      result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_file))
      if result.lower() not in ['y', 'yes']:
        print('Not overwriting. Exiting...')
        printMatrix4x4(matrix)
        os.sys.exit()
    
    precision = 7
    delimiter=' '
    formatter = '{{:14.{}e}}'.format(precision)
    
    with open(output_file, 'w') as fp:
      fp.write('SCANCO TRANSFORMATION DATA VERSION:   10\n')
      fp.write('R4_MAT:\n')
      for i in range(4):
        row_data = delimiter.join([formatter.format(float(matrix.GetElement(i,j))) for j in range(4)])
        fp.write(row_data+'\n')
    
    return
    
def keypress(obj, ev):
    interactor = obj
    renderer = interactor.GetRenderWindow().GetRenderers().GetFirstRenderer()
    actorCollection = renderer.GetActors()
    actorCollection.InitTraversal()
    
    key = obj.GetKeySym()

    if key in 'h':
      print('Press the \'u\' key to output actor transform matrix')
      print('Press the \'p\' key to pick a point')
      print('Press the \'d\' key to delete a point')
      print('Press the \'o\' key to output points')
      print('Press the \'a\' key for actor control mode')
      print('Press the \'c\' key for camera control mode')
      print('Press the \'q\' key to quit')

    if key in 'u':
      for index in range(actorCollection.GetNumberOfItems()):
        nextActor = actorCollection.GetNextActor()
        if (nextActor.GetPickable()==1):
          printMatrix4x4(nextActor.GetMatrix())
          message('File written: transform.txt')
          writeTransform('transform.txt',nextActor.GetMatrix(),False)
          
    if key in 'p':
      x, y = obj.GetEventPosition()

      cellPicker = vtk.vtkCellPicker()
      cellPicker.SetTolerance(0.0001)
      cellPicker.Pick(x, y, 0, renderer)

      points = cellPicker.GetPickedPositions()
      numPoints = points.GetNumberOfPoints()
      if numPoints < 1:
        return()
      i, j, k = points.GetPoint(0)
      

      # Get the size of the actor by measuring its diagonal
      b = actorCollection.GetNextActor().GetBounds()
      sphere_size = diagonal(b[1]-b[0],b[3]-b[2],b[5]-b[4]) * 0.005
      
      sphere = vtk.vtkSphereSource()
      sphere.SetRadius(sphere_size)
      sphere.SetThetaResolution(20)
      sphere.SetPhiResolution(20)
      sphere.SetCenter(i, j, k)
      
      mapper = vtk.vtkPolyDataMapper()
      mapper.SetInputConnection(sphere.GetOutputPort())
      
      marker = vtk.vtkActor()
      marker.SetMapper(mapper)
      renderer.AddActor(marker)
      marker.GetProperty().SetColor(1, 0, 0)
      interactor.Render()
      
      # updates the dictionaries where the point coordinates are stored
      if len(pointsDict.keys()) > 0:
          pointNum = max(pointsDict.keys())
      else:
          pointNum = 0
      
      pointsDict.update({pointNum + 1:[i, j, k]})
      actorDict.update({pointNum + 1:marker})
      
      print_points_to_screen(pointsDict.values(),',',4)
      
      
    if key in 'd':
      x, y = interactor.GetEventPosition()
      
      cellPicker = vtk.vtkCellPicker()
      cellPicker.SetTolerance(0.00001)
      cellPicker.Pick(x, y, 0, renderer)
      
      points = cellPicker.GetPickedPositions()
      numPoints = points.GetNumberOfPoints()
      if numPoints < 1:
        return()
      i, j, k = points.GetPoint(0)
      
      min_distance_to_point = 1e12
      for point, posn in pointsDict.items():
        distance_to_point = diagonal(posn[0]-i,posn[1]-j,posn[2]-k)
        if (distance_to_point < min_distance_to_point):
          min_distance_to_point = distance_to_point
          keyPoint = point
      
      try:    
         renderer.RemoveActor(actorDict[keyPoint])
         interactor.Render()
         
         del pointsDict[keyPoint]
         del actorDict[keyPoint]
         
         print("Deleted point #: ", keyPoint)
         print("Number of points remaining: ", str(len(pointsDict.keys())) )
         
      except KeyError:
         print("No point found at these coordinates")
         
      print_points_to_screen(pointsDict.values(),',',4)
      
      
    if key in 'o':
      #result = input('Output filename \"{}\" as .txt filetype. \n'.format(output_dir))
      #output_filename = str(output_dir) + str(result) + '.txt'
      output_file = "points.txt"
      
      precision = 4
      delimiter=','
      formatter = '{{:8.{}f}}'.format(precision)
      
      with open(output_file, 'w') as fp:
          for point in pointsDict.values():
              entry = delimiter.join([formatter.format(float(x)) for x in point])
              entry += os.linesep
              fp.write(entry)
      
      message('Wrote output file ',output_file)

def print_points_to_screen(points,delimiter,precision):
  formatter = '{{:8.{}f}}'.format(precision)
  print('|-------------------------')
  for point in points:
    entry = delimiter.join([formatter.format(float(x)) for x in point])
    #entry += os.linesep
    print(entry)
  print('|-------------------------')
  
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
  renderer.GetActiveCamera().Azimuth(0.0)
  renderer.GetActiveCamera().Elevation(0.0)
  renderer.GetActiveCamera().Dolly(1.0)
  renderer.ResetCameraClippingRange()

  renderWindowInteractor = vtk.vtkRenderWindowInteractor()
  renderWindowInteractor.SetRenderWindow( renderWindow )
  renderWindow.Render()

  message('Press the \'h\' key to get help on keyboard options')
  renderWindowInteractor.AddObserver(vtk.vtkCommand.KeyPressEvent, keypress, 1.0)
  renderWindowInteractor.Initialize()
  renderWindowInteractor.Start()
  
  return (actor.GetMatrix())

def joinPolyData(pd1,pd2):
  input1 = vtk.vtkPolyData()
  input2 = vtk.vtkPolyData()
  
  input1.ShallowCopy( pd1 )
  input2.ShallowCopy( pd2 )
  
  appendFilter = vtk.vtkAppendPolyData()
  appendFilter.AddInputData( input1 )
  appendFilter.AddInputData( input2 )
  
  return appendFilter

def cleanPolyData(pd):
  input = vtk.vtkPolyData()
  input.ShallowCopy( pd )
  
  tri = vtk.vtkTriangleFilter()
  tri.SetInputData( input )
  
  cleanFilter = vtk.vtkCleanPolyData()
  cleanFilter.SetInputConnection( tri.GetOutputPort() )
  cleanFilter.Update()
  
  return cleanFilter
    
def write_stl(model,output_file,mat4x4):
  
  transform = vtk.vtkTransform()
  transform.SetMatrix(mat4x4)

  transformFilter = vtk.vtkTransformFilter()
  transformFilter.SetInputConnection( model )
  transformFilter.SetTransform( transform )
  transformFilter.Update()
  
  writer = vtk.vtkSTLWriter()
  writer.SetFileName(output_file)
  writer.SetFileTypeToASCII()
  writer.SetInputConnection( transformFilter.GetOutputPort() )
  writer.Write()
  message("Writing file " + output_file)

def img2stl(input_file, output_file, transform_file, threshold, gaussian, radius, marching_cubes, decimation, visualize, overwrite, func):

  if os.path.isfile(output_file) and not overwrite:
    result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_file))
    if result.lower() not in ['y', 'yes']:
      print('Not overwriting. Exiting...')
      os.sys.exit()
  
  # We don't use CheckExt to check valid extensions prior to calling this function because it can't handle the .nii.gz
  # format. So, we rely on get_vtk_reader() to return a valid reader, and we check whether the file exists here. 
  if not os.path.isfile(input_file):
      os.sys.exit('[ERROR] Cannot find file \"{}\"'.format(input_file))
  reader = get_vtk_reader(input_file)
  if reader is None:
      os.sys.exit('[ERROR] Cannot find reader for file \"{}\"'.format(input_file))

  print('Reading input image ' + input_file)
  reader.SetFileName(input_file)
  reader.Update()
  
  image = reader.GetOutput()
  message("Read %d points from AIM file" % image.GetNumberOfPoints())
  image_bounds = image.GetBounds()
  message("Image bounds:", (" %.4f"*6) % image_bounds)
  image_extent = image.GetExtent()
  message("Image extent:", (" %d"*6) % image_extent)

  message("Histogram of input data:")
  histogram(image)
  
  # Apply threshold if requested
  if (threshold):
    message("Thresholding")
    thres = vtk.vtkImageThreshold()
    thres.SetInValue(127)
    thres.SetOutValue(0)
    thres.SetInputConnection(reader.GetOutputPort())
    thres.ThresholdByUpper(1) # Any values at or above 1 are in
    thres.Update()
    message("Histogram of thresholded data:")
    histogram(thres.GetOutput())
  
  message("Gaussian smoothing")
  gauss = vtk.vtkImageGaussianSmooth()
  gauss.SetStandardDeviation(gaussian)
  gauss.SetRadiusFactor(radius)
  if (not threshold):
    gauss.SetInputConnection(reader.GetOutputPort())
  else:
    gauss.SetInputConnection(thres.GetOutputPort())
  gauss.Update()
  message("Total of %d voxels" % gauss.GetOutput().GetNumberOfCells())
  
  message("Padding the data")
  pad = vtk.vtkImageConstantPad()
  pad.SetConstant(0)
  pad.SetOutputWholeExtent(image_extent[0]-1,image_extent[1]+1,
                           image_extent[2]-1,image_extent[3]+1,
                           image_extent[4]-1,image_extent[5]+1)
  pad.SetInputConnection(gauss.GetOutputPort())
  pad.Update()
  message("Total of %d padded voxels" % pad.GetOutput().GetNumberOfCells())

  message("Extracting isosurface")
  mcube = vtk.vtkImageMarchingCubes()
  mcube.ComputeScalarsOff()
  mcube.ComputeNormalsOff()
  mcube.SetValue(0,marching_cubes)
  mcube.SetInputConnection(pad.GetOutputPort())
  mcube.Update()
  message("Generated %d triangles" % mcube.GetOutput().GetNumberOfCells())
  
  if (decimation>0.0):
    message("Decimating the isosurface. Targeting {:.1f}%".format(decimation*100.0))
    deci = vtk.vtkDecimatePro()
    deci.SetInputConnection(mcube.GetOutputPort())
    deci.SetTargetReduction(decimation) # 0 is none, 1 is maximum decimation.
    deci.Update()
    message("Decimated to %d triangles" % deci.GetOutput().GetNumberOfCells())
    mesh = deci
  else:
    message("No decimation of the isosurface")
    mesh = mcube
  
  mesh = applyTransform(transform_file, mesh)
  
  if (visualize):
    mat4x4 = visualize_actors( mesh.GetOutputPort(), None )
  else:
    mat4x4 = vtk.vtkMatrix4x4()
  
  write_stl( mesh.GetOutputPort(), output_file, mat4x4 )
  
def stl2img(input_file, output_file, transform_file, el_size_mm, visualize, overwrite, func):

  if os.path.isfile(output_file) and not overwrite:
    result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_file))
    if result.lower() not in ['y', 'yes']:
      print('Not overwriting. Exiting...')
      os.sys.exit()

  model = vtk.vtkSTLReader()
  model.SetFileName(input_file)
  model.Update()
  
  model = applyTransform(transform_file, model)
  
  if (visualize):
    mat4x4 = visualize_actors( model.GetOutputPort(), None )
  else:
    mat4x4 = vtk.vtkMatrix4x4()
  
  transform = vtk.vtkTransform()
  transform.SetMatrix(mat4x4)

  transformFilter = vtk.vtkTransformFilter()
  transformFilter.SetInputConnection( model.GetOutputPort() )
  transformFilter.SetTransform( transform )
  transformFilter.Update()
  
  bounds = transformFilter.GetOutput().GetBounds()
  dim = [1,1,1]
  for i in range(3):
    dim[i] = (math.ceil((bounds[i*2+1]-bounds[i*2]) / el_size_mm[i]))
  origin = [1,1,1]
  origin[0] = bounds[0] + el_size_mm[0] / 2
  origin[1] = bounds[2] + el_size_mm[1] / 2
  origin[2] = bounds[4] + el_size_mm[2] / 2
  
  whiteImage = vtk.vtkImageData()
  whiteImage.SetSpacing(el_size_mm)
  whiteImage.SetDimensions(dim)
  whiteImage.SetExtent(0, dim[0] - 1, 0, dim[1] - 1, 0, dim[2] - 1)
  whiteImage.SetOrigin(origin)
  whiteImage.AllocateScalars(vtk.VTK_CHAR,1)
  for i in range(whiteImage.GetNumberOfPoints()):
    whiteImage.GetPointData().GetScalars().SetTuple1(i, 127)

  pol2stenc = vtk.vtkPolyDataToImageStencil()
  pol2stenc.SetInputData( transformFilter.GetOutput() )
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
  
  # We don't use CheckExt to check valid extensions prior to calling this function because it can't handle the .nii.gz
  # format. So, we rely on get_vtk_writer() to return a valid writer. 
  # Create writer
  writer = get_vtk_writer(output_file)
  if writer is None:
      os.sys.exit('[ERROR] Cannot find writer for file \"{}\"'.format(output_file))
  #writer.SetInputConnection(reader.GetOutputPort())
  writer.SetInputData(imgstenc.GetOutput())
  writer.SetFileName(output_file)
  
  # Setup processing log if writing an AIM file.
  final_processing_log = '!-------------------------------------------------------------------------------\n'+'Written by blRapidPrototype.'
  handle_filetype_writing_special_cases(
      writer,
      processing_log=final_processing_log
  )
  
  message("Writing file " + output_file)
  writer.Update()
  
  #writer = vtkbone.vtkboneAIMWriter()
  #writer.SetInputData( imgstenc.GetOutput() )
  #writer.SetFileName(output_file)
  #writer.SetProcessingLog('!-------------------------------------------------------------------------------\n'+'Written by blRapidPrototype.')
  #writer.Update()

  #message("Writing file " + output_file)

def view_stl(input_file, transform_file, func):

  model = vtk.vtkSTLReader()
  model.SetFileName(input_file)
  model.Update()
  
  model = applyTransform(transform_file, model)
  
  mat4x4 = visualize_actors( model.GetOutputPort(), None )
  
def add_stl(input_files, output_file, transform_file, visualize, overwrite, func):

  if os.path.isfile(output_file) and not overwrite:
    result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_file))
    if result.lower() not in ['y', 'yes']:
      print('Not overwriting. Exiting...')
      os.sys.exit()
  
  n_files = len(input_files)
  
  im1 = vtk.vtkSTLReader()
  im1.SetFileName(input_files[0])
  im1.Update()
  
  im = vtk.vtkSTLReader()
  transform = vtk.vtkTransform()
  transformFilter = vtk.vtkTransformFilter()
  
  for idx,file in enumerate(input_files):
    if idx>0:
      im.SetFileName(file)
      im.Update()
      
      im = applyTransform(transform_file, im)
      
      if (visualize):
        mat4x4 = visualize_actors( im.GetOutputPort(), im1.GetOutputPort() )
      else:
        mat4x4 = vtk.vtkMatrix4x4()
      
      transform.SetMatrix(mat4x4)
      
      transformFilter.SetInputConnection( im.GetOutputPort() )
      transformFilter.SetTransform( transform )
      transformFilter.Update()
      
      if idx==1:
        final_image = joinPolyData( transformFilter.GetOutput(), im1.GetOutput() )
        final_image.Update()
      else:
        final_image = joinPolyData( transformFilter.GetOutput(), final_image.GetOutput() )
        final_image.Update()
        
  write_stl( final_image.GetOutputPort(), output_file, vtk.vtkMatrix4x4() )
  
def boolean_stl(input_file1, input_file2, output_file, transform_file, operation, visualize, overwrite, func):

  if os.path.isfile(output_file) and not overwrite:
    result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_file))
    if result.lower() not in ['y', 'yes']:
      print('Not overwriting. Exiting...')
      os.sys.exit()
  
  im1 = vtk.vtkSTLReader()
  im1.SetFileName(input_file1)
  im1.Update()
  im1 = cleanPolyData( im1.GetOutput() )
  
  im2 = vtk.vtkSTLReader()
  im2.SetFileName(input_file2)
  im2.Update()
  im2 = cleanPolyData( im2.GetOutput() )
  
  im2 = applyTransform(transform_file, im2)
  
  if (visualize):
    mat4x4 = visualize_actors( im2.GetOutputPort(), im1.GetOutputPort() )
  else:
    mat4x4 = vtk.vtkMatrix4x4()

  transform = vtk.vtkTransform()
  transform.SetMatrix(mat4x4)
  
  transformFilter = vtk.vtkTransformFilter()
  transformFilter.SetInputConnection( im2.GetOutputPort() )
  transformFilter.SetTransform( transform )
  transformFilter.Update()

  booleanOperation = vtk.vtkBooleanOperationPolyDataFilter()
  booleanOperation.SetInputData( 0, im1.GetOutput() )
  booleanOperation.SetInputData( 1, transformFilter.GetOutput() )
  if "union" in operation:
    booleanOperation.SetOperationToUnion()
  elif "intersection" in operation:
    booleanOperation.SetOperationToIntersection()
  elif "difference" in operation:
    booleanOperation.SetOperationToDifference()
  else:
    raise ValueError('Invalid boolean operation: ' + operation)
  booleanOperation.Update()
    
  write_stl( booleanOperation.GetOutputPort(), output_file, vtk.vtkMatrix4x4() )

def create_sign(output_file, transform_file, text, height, width, depth, nobacking, visualize, overwrite, func):
  
  if os.path.isfile(output_file) and not overwrite:
    result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_file))
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
  
  scale = 1
  transform = vtk.vtkTransform()
  if (width is not None and height is None):
    message('Scaling to width of {:.2f} mm'.format(width))
    scale_width = width/i_width
    scale_height = scale_width
  elif (width is None and height is not None):
    message('Scaling to height of {:.2f} mm'.format(height))
    scale_height = height/i_height
    scale_width = scale_height
  elif (width is not None and height is not None):
    message('Scaling to height of {:.2f} mm and width of {:.2f} mm'.format(height,width),'Text may be distorted!')
    scale_width = width/i_width
    scale_height = height/i_height
  else:
    message('No scaling applied to text')
    scale_width = 1
    scale_height = 1
    
  if (depth is not None):
    message('Setting depth to {:.2f} mm'.format(depth))
    scale_depth = depth/i_depth
    
  transform.Scale(scale_width,scale_height,scale_depth)
  
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
  
  if (not nobacking):
    message('Create a backing for the text.')
    cube = vtk.vtkCubeSource()
    shift = o_depth/5.0
    cube.SetBounds(
      transformFilter.GetOutput().GetBounds()[0] - o_width * 0.05,
      transformFilter.GetOutput().GetBounds()[1] + o_width * 0.05,
      transformFilter.GetOutput().GetBounds()[2] - o_height * 0.1,
      transformFilter.GetOutput().GetBounds()[3] + o_height * 0.1,
      transformFilter.GetOutput().GetBounds()[4] - shift,
      transformFilter.GetOutput().GetBounds()[5] - shift - o_depth * 0.65
    )
    cube.Update()
    sign = joinPolyData( cube.GetOutput(), transformFilter.GetOutput() )
  else:
    sign = transformFilter
  
  sign = applyTransform(transform_file, sign)
  
  if (visualize):
    mat4x4 = visualize_actors( sign.GetOutputPort(), None )
  else:
    mat4x4 = vtk.vtkMatrix4x4()

  write_stl( sign.GetOutputPort(), output_file, mat4x4 )
  
  return

def create_sphere(output_file, transform_file, radius, phi, theta, phi_start, phi_end, theta_start, theta_end, center, visualize, overwrite, func):

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

  triangleFilter = vtk.vtkTriangleFilter()
  triangleFilter.SetInputConnection( sphere.GetOutputPort() )
  triangleFilter.Update()
  
  triangleFilter = applyTransform(transform_file, triangleFilter)

  message('Sphere attributes:',
          '{:16s} = {:8.2f} mm'.format('radius',radius),
          '{:16s} = {:8d}'.format('phi resolution',phi),
          '{:16s} = {:8d}'.format('theta resolution',theta),
          '{:16s} = {:8d} degrees'.format('phi start',phi_start),
          '{:16s} = {:8d} degrees'.format('phi end',phi_end),
          '{:16s} = {:8d} degrees'.format('theta start',theta_start),
          '{:16s} = {:8d} degrees'.format('theta end',theta_end),
          '{:16s} = {:8.2f}, {:8.2f}, {:8.2f} mm'.format('center',center[0],center[1],center[2]))
  
  if (visualize):
    mat4x4 = visualize_actors( triangleFilter.GetOutputPort(), None )
  else:
    mat4x4 = vtk.vtkMatrix4x4()

  write_stl( triangleFilter.GetOutputPort(), output_file, mat4x4 )
  
def create_cylinder(output_file, transform_file, radius, height, resolution, capping, center, rotate, endpoints, visualize, overwrite, func):

  if os.path.isfile(output_file) and not overwrite:
    result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_file))
    if result.lower() not in ['y', 'yes']:
      print('Not overwriting. Exiting...')
      os.sys.exit()

  # If there are end points defined we create the cylinder differently
  if np.count_nonzero(endpoints): # endpoints are defined
      line = vtk.vtkLineSource()
      line.SetPoint1(endpoints[0],endpoints[1],endpoints[2])
      line.SetPoint2(endpoints[3],endpoints[4],endpoints[5])
      line.Update()
  
      cylinder = vtk.vtkTubeFilter()
      cylinder.SetInputConnection( line.GetOutputPort() )
      cylinder.SetRadius( radius )
      cylinder.SetNumberOfSides( resolution )
      cylinder.SetCapping( capping )
  else:
      cylinder = vtk.vtkCylinderSource()
      cylinder.SetHeight( height )
      cylinder.SetRadius( radius )
      cylinder.SetResolution( resolution )
      cylinder.SetCapping( capping )
      cylinder.SetCenter( center )
      cylinder.Update()

  triangleFilter = vtk.vtkTriangleFilter()
  triangleFilter.SetInputConnection( cylinder.GetOutputPort() )
  triangleFilter.Update()
  
  triangleFilter = applyTransform(transform_file, triangleFilter)
  
  rotateTransform = vtk.vtkTransform()
  rotateTransform.RotateX(rotate[0])
  rotateTransform.RotateY(rotate[1])
  rotateTransform.RotateZ(rotate[2])
  
  transformFilter = vtk.vtkTransformFilter()
  transformFilter.SetInputConnection( triangleFilter.GetOutputPort() )
  transformFilter.SetTransform( rotateTransform )
  transformFilter.Update()
  
  message('Cylinder attributes:',
          '{:16s} = {:8.2f} mm'.format('radius',radius),
          '{:16s} = {:8.2f} mm'.format('height',height),
          '{:16s} = {:8d}'.format('resolution',resolution),
          '{:16s} = {:>8s}'.format('capping',('True' if capping else 'False')),
          '{:16s} = {:8.2f}, {:8.2f}, {:8.2f} mm'.format('center',center[0],center[1],center[2]),
          '{:16s} = {:8.2f}, {:8.2f}, {:8.2f} deg'.format('rotate',rotate[0],rotate[1],rotate[2]))

  if (visualize):
    mat4x4 = visualize_actors( transformFilter.GetOutputPort(), None )
  else:
    mat4x4 = vtk.vtkMatrix4x4()

  write_stl( transformFilter.GetOutputPort(), output_file, mat4x4 )

def create_tube(output_file, transform_file, inner_radius, outer_radius, height, resolution, rotate, visualize, overwrite, func):

  if os.path.isfile(output_file) and not overwrite:
    result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_file))
    if result.lower() not in ['y', 'yes']:
      print('Not overwriting. Exiting...')
      os.sys.exit()

  disk = vtk.vtkDiskSource()
  disk.SetInnerRadius( inner_radius )
  disk.SetOuterRadius( outer_radius )
  disk.SetRadialResolution( resolution )
  disk.SetCircumferentialResolution( resolution )
  disk.Update()
  
  extrude = vtk.vtkLinearExtrusionFilter()
  extrude.SetInputConnection( disk.GetOutputPort() )
  extrude.SetExtrusionTypeToNormalExtrusion()
  extrude.SetVector(0, 0, 1 )
  extrude.SetScaleFactor( height )
  
  triangleFilter = vtk.vtkTriangleFilter()
  triangleFilter.SetInputConnection( extrude.GetOutputPort() )
  triangleFilter.Update()

  triangleFilter = applyTransform(transform_file, triangleFilter)
  
  rotateTransform = vtk.vtkTransform()
  rotateTransform.RotateX(rotate[0])
  rotateTransform.RotateY(rotate[1])
  rotateTransform.RotateZ(rotate[2])
  
  transformFilter = vtk.vtkTransformFilter()
  transformFilter.SetInputConnection( triangleFilter.GetOutputPort() )
  transformFilter.SetTransform( rotateTransform )
  transformFilter.Update()
  
  message('Tube attributes:',
          '{:16s} = {:8.2f} mm'.format('inner_radius',inner_radius),
          '{:16s} = {:8.2f} mm'.format('outer_radius',outer_radius),
          '{:16s} = {:8.2f} mm'.format('height',height),
          '{:16s} = {:8d}'.format('resolution',resolution),
          '{:16s} = {:8.2f}, {:8.2f}, {:8.2f} deg'.format('rotate',rotate[0],rotate[1],rotate[2]))

  if (visualize):
    mat4x4 = visualize_actors( transformFilter.GetOutputPort(), None )
  else:
    mat4x4 = vtk.vtkMatrix4x4()

  write_stl( transformFilter.GetOutputPort(), output_file, mat4x4 )

def create_cube(output_file, transform_file, bounds, rotate, visualize, overwrite, func):

  if os.path.isfile(output_file) and not overwrite:
    result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_file))
    if result.lower() not in ['y', 'yes']:
      print('Not overwriting. Exiting...')
      os.sys.exit()

  cube = vtk.vtkCubeSource()
  cube.SetBounds( bounds )
  cube.Update()
  
  triangleFilter = vtk.vtkTriangleFilter()
  triangleFilter.SetInputConnection( cube.GetOutputPort() )
  triangleFilter.Update()

  triangleFilter = applyTransform(transform_file, triangleFilter)
  
  rotateTransform = vtk.vtkTransform()
  rotateTransform.RotateX(rotate[0])
  rotateTransform.RotateY(rotate[1])
  rotateTransform.RotateZ(rotate[2])
  
  transformFilter = vtk.vtkTransformFilter()
  transformFilter.SetInputConnection( triangleFilter.GetOutputPort() )
  transformFilter.SetTransform( rotateTransform )
  transformFilter.Update()
  
  message('Cube attributes:',
          '{:16s}'.format('bounds'),
          '{:16s} = {:8.2f}, {:8.2f} mm'.format('  X  min, max',bounds[0],bounds[1]),
          '{:16s} = {:8.2f}, {:8.2f} mm'.format('  Y  min, max',bounds[2],bounds[3]),
          '{:16s} = {:8.2f}, {:8.2f} mm'.format('  Z  min, max',bounds[4],bounds[5]),
          '{:16s}'.format('length'),
          '{:16s} = {:8.2f} mm'.format('  X',(bounds[1]-bounds[0])),
          '{:16s} = {:8.2f} mm'.format('  Y',(bounds[3]-bounds[2])),
          '{:16s} = {:8.2f} mm'.format('  Z',(bounds[5]-bounds[4])))
  
  if (visualize):
    mat4x4 = visualize_actors( transformFilter.GetOutputPort(), None )
  else:
    mat4x4 = vtk.vtkMatrix4x4()

  write_stl( transformFilter.GetOutputPort(), output_file, mat4x4 )

pointsDict = {}
actorDict = {}

# Here are some other VTK Source objects that may be of interest:
# vtkArcSource
# vtkArrowSource
# vtkBoundedPointSource
# vtkButtonSource
# vtkCapsuleSource
# vtkConeSource
# vtkDiskSource
# vtkEarthSource
# vtkEllipseArcSource
# vtkFrustumSource
# vtkLineSource
# vtkOutlineSource
# vtkParametricFunctionSource
# vtkPlaneSource
# vtkPlatonicSolidSource
# vtkPointSource
# vtkPolyPointSource
# vtkRegularPolygonSource
# vtkSectorSource
# vtkSuperquadricSource
# vtkTextSource
# vtkVolumeOutlineSource


def main():
    # Setup description
    description='''
A general utility for creating STL files used for rapid prototyping from 
AIMs or NIFTI and back again.

This is a collection of utilities that together provide significant 
opportunities for creating complex STL files from input images such as 
AIM or NIFTI and conversion back to image format.

(The following two functions were previously aim2stl and stl2aim)
img2stl         : takes a thresholded AIM or NIFTI file and creates STL
stl2img         : takes an STL model and converts to a thresholded AIM or NIFTI

view_stl        : view an STL model
boolean_stl     : union, intersect or difference of two STL models
add_stl         : add two or more STL models (see also boolean_stel 'union')

create_sign     : make a sign with text
create_sphere   : make a sphere
create_cylinder : make a cylinder
create_tube     : make a tube
create_cube     : make a cube

Input AIM must be type 'char'. STL model mesh properties can be controlled 
by setting gaussian smoothing and isosurface. The number of polygons
can be reduced (decimation).

Visualization can be performed to view STL models. Some useful keys:

 'a' - actor mode (mouse, shift, control to manipulate) [REQUIRED]
 'c' - camera mode  (mouse, shift, control to manipulate)
 't' - trackball
 'j' - joystick
 'w' - wireframe
 's' - solid surface
 'u' – a user-defined function prints 4x4 transform.
 'p' – a user-defined function picks a point.
 'd' – a user-defined function deletes a point.
 'o' – a user-defined function outputs file of points.
 'q' - quits
 
When you quit from the visualization the model will be printed with the new 
transform if you have applied one.
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
    
    # parser for img2stl
    parser_img2stl = subparsers.add_parser('img2stl')
    parser_img2stl.add_argument('input_file', help='Input AIM/NIFTI image file name')
    parser_img2stl.add_argument('output_file', action=CheckExt({'stl','STL'}), help='Output STL image file name')
    parser_img2stl.add_argument('--transform_file', default="None", action=CheckExt({'txt','TXT'}), metavar='FILE', help='Apply a 4x4 transform from a file (default: %(default)s)')
    parser_img2stl.add_argument('--threshold', action='store_true', help='Set all image values to 127 (default: %(default)s)')
    parser_img2stl.add_argument('--gaussian', type=float, default=0.7, metavar='GAUSS', help='Gaussian standard deviation (default: %(default)s)')
    parser_img2stl.add_argument('--radius', type=float, default=1.0, metavar='RADIUS', help='Gaussian radius support (default: %(default)s)')
    parser_img2stl.add_argument('--marching_cubes', type=float, default=50.0, metavar='MC', help='Marching cubes threshold (default: %(default)s)')
    parser_img2stl.add_argument('--decimation', type=float, default=0.0, metavar='DEC', choices=Range(0.0,1.0), help='Decimation is 0 (none) to 1 (max) (default: %(default)s)')
    parser_img2stl.add_argument('--visualize', action='store_true', help='Visualize the model (default: %(default)s)')
    parser_img2stl.add_argument('--overwrite', action='store_true', help='Overwrite output without asking (default: %(default)s)')
    parser_img2stl.set_defaults(func=img2stl)
    
    # parser for stl2img
    parser_stl2img = subparsers.add_parser('stl2img')
    parser_stl2img.add_argument('input_file', action=CheckExt({'stl','STL'}), help='Input STL image file name')
    parser_stl2img.add_argument('output_file', help='Output AIM/NIFTI image file name')
    parser_stl2img.add_argument('--transform_file', default="None", action=CheckExt({'txt','TXT'}), metavar='FILE', help='Apply a 4x4 transform from a file (default: %(default)s)')
    parser_stl2img.add_argument('--el_size_mm', type=float, nargs=3, default=[0.0607,0.0607,0.0607], metavar='0', help='Set element size (default: %(default)s)')
    parser_stl2img.add_argument('--visualize', action='store_true', help='Visualize the model (default: %(default)s)')
    parser_stl2img.add_argument('--overwrite', action='store_true', help='Overwrite output without asking (default: %(default)s)')
    parser_stl2img.set_defaults(func=stl2img)
    
    # parser for view_stl
    parser_view_stl = subparsers.add_parser('view_stl')
    parser_view_stl.add_argument('input_file', action=CheckExt({'stl','STL'}), help='Input STL image file name')
    parser_view_stl.add_argument('--transform_file', default="None", action=CheckExt({'txt','TXT'}), metavar='FILE', help='Apply a 4x4 transform from a file (default: %(default)s)')
    parser_view_stl.set_defaults(func=view_stl)

    # parser for add_stl
    parser_add_stl = subparsers.add_parser('add_stl')
    parser_add_stl.add_argument('input_files', action=CheckExt({'stl','STL'}), nargs='+', help='Input two or more STL image file names')
    parser_add_stl.add_argument('output_file', action=CheckExt({'stl','STL'}), help='Output STL image file name')
    parser_add_stl.add_argument('--transform_file', default="None", action=CheckExt({'txt','TXT'}), metavar='FILE', help='Apply a 4x4 transform to input_file2 to N (default: %(default)s)')
    parser_add_stl.add_argument('--visualize', action='store_true', help='Visualize the model (default: %(default)s)')
    parser_add_stl.add_argument('--overwrite', action='store_true', help='Overwrite output without asking (default: %(default)s)')
    parser_add_stl.set_defaults(func=add_stl)
    
    # parser for boolean_stl
    parser_boolean_stl = subparsers.add_parser('boolean_stl')
    parser_boolean_stl.add_argument('input_file1', action=CheckExt({'stl','STL'}), help='Input STL image file name')
    parser_boolean_stl.add_argument('input_file2', action=CheckExt({'stl','STL'}), help='Input STL image file name (allows transform)')
    parser_boolean_stl.add_argument('output_file', action=CheckExt({'stl','STL'}), help='Output STL image file name')
    parser_boolean_stl.add_argument('--operation', default="union", choices=['union', 'intersection', 'difference'], metavar='OP', help='Valid operations are union, intersection or difference (default: %(default)s)')
    parser_boolean_stl.add_argument('--transform_file', default="None", action=CheckExt({'txt','TXT'}), metavar='FILE', help='Apply a 4x4 transform from a file to input_file1 (default: %(default)s)')
    parser_boolean_stl.add_argument('--visualize', action='store_true', help='Visualize the model (default: %(default)s)')
    parser_boolean_stl.add_argument('--overwrite', action='store_true', help='Overwrite output without asking (default: %(default)s)')
    parser_boolean_stl.set_defaults(func=boolean_stl)
    
    # parser for create_sign
    parser_create_sign = subparsers.add_parser('create_sign')
    parser_create_sign.add_argument('output_file', action=CheckExt({'stl','STL'}), help='Output STL image file name')
    parser_create_sign.add_argument('--transform_file', default="None", action=CheckExt({'txt','TXT'}), metavar='FILE', help='Apply a 4x4 transform from a file (default: %(default)s)')
    parser_create_sign.add_argument('--text', default="Hello!", help='Letters for 3D rendering (default: %(default)s)')
    parser_create_sign.add_argument('--width', type=float, help='Set width of text')
    parser_create_sign.add_argument('--height', type=float, help='Set height of text')
    parser_create_sign.add_argument('--depth', type=float, default=0.5, help='Set depth of text (default: %(default)s mm)')
    parser_create_sign.add_argument('--nobacking', action='store_true', help='Suppress adding a backing to the text (default: %(default)s)')
    parser_create_sign.add_argument('--visualize', action='store_true', help='Visualize the model (default: %(default)s)')
    parser_create_sign.add_argument('--overwrite', action='store_true', help='Overwrite output without asking (default: %(default)s)')
    parser_create_sign.set_defaults(func=create_sign)
    
    # parser for create_sphere
    parser_create_sphere = subparsers.add_parser('create_sphere')
    parser_create_sphere.add_argument('output_file', action=CheckExt({'stl','STL'}), help='Output STL image file name')
    parser_create_sphere.add_argument('--transform_file', default="None", action=CheckExt({'txt','TXT'}), metavar='FILE', help='Apply a 4x4 transform from a file (default: %(default)s)')
    parser_create_sphere.add_argument('--radius', type=float, default=0.5, help='Sphere radius (default: %(default)s)')
    parser_create_sphere.add_argument('--phi', type=int, default=8, metavar='RES', help='Sphere phi_resolution (default: %(default)s)')
    parser_create_sphere.add_argument('--theta', type=int, default=8, metavar='RES', help='Sphere theta_resolution (default: %(default)s)')
    parser_create_sphere.add_argument('--phi_start', type=int, default=0, choices=range(0,180), metavar='RES', help='Sphere phi start angle (default: %(default)s)')
    parser_create_sphere.add_argument('--phi_end', type=int, default=180, choices=range(0,180), metavar='RES', help='Sphere phi end angle (default: %(default)s)')
    parser_create_sphere.add_argument('--theta_start', type=int, default=0, choices=range(0,360), metavar='RES', help='Sphere theta start angle (default: %(default)s)')
    parser_create_sphere.add_argument('--theta_end', type=int, default=360, choices=range(0,360), metavar='RES', help='Sphere theta end angle (default: %(default)s)')
    parser_create_sphere.add_argument('--center', type=float, nargs=3, default=[0,0,0], metavar='0', help='Sphere center (default: %(default)s)')
    parser_create_sphere.add_argument('--visualize', action='store_true', help='Visualize the model (default: %(default)s)')
    parser_create_sphere.add_argument('--overwrite', action='store_true', help='Overwrite output without asking (default: %(default)s)')
    parser_create_sphere.set_defaults(func=create_sphere)
        
    # parser for create_cylinder
    parser_create_cylinder = subparsers.add_parser('create_cylinder')
    parser_create_cylinder.add_argument('output_file', action=CheckExt({'stl','STL'}), help='Output STL image file name')
    parser_create_cylinder.add_argument('--transform_file', default="None", action=CheckExt({'txt','TXT'}), metavar='FILE', help='Apply a 4x4 transform from a file (default: %(default)s)')
    parser_create_cylinder.add_argument('--radius', type=float, default=0.5, help='Cylinder radius (default: %(default)s)')
    parser_create_cylinder.add_argument('--height', type=float, default=1.0, help='Cylinder height (default: %(default)s)')
    parser_create_cylinder.add_argument('--resolution', type=int, default=6, metavar='RES', help='Cylinder resolution (default: %(default)s)')
    parser_create_cylinder.add_argument('--capping', action='store_false', help='Cylinder capping (default: %(default)s)')
    parser_create_cylinder.add_argument('--center', type=float, nargs=3, default=[0,0,0], metavar='0', help='Cylinder center (default: %(default)s)')
    parser_create_cylinder.add_argument('--rotate', type=float, nargs=3, default=[0,0,0], metavar='0', help='Rotation angle about X, Y and Z axes (default: %(default)s)')
    parser_create_cylinder.add_argument('--endpoints', type=float, nargs=6, default=[0,0,0,0,0,0], metavar='0', help='Ends X,Y,Z and X,Y,Z (default: %(default)s)')
    parser_create_cylinder.add_argument('--visualize', action='store_true', help='Visualize the model (default: %(default)s)')
    parser_create_cylinder.add_argument('--overwrite', action='store_true', help='Overwrite output without asking (default: %(default)s)')
    parser_create_cylinder.set_defaults(func=create_cylinder)
    
    # parser for create_tube
    parser_create_tube = subparsers.add_parser('create_tube')
    parser_create_tube.add_argument('output_file', action=CheckExt({'stl','STL'}), help='Output STL image file name')
    parser_create_tube.add_argument('--transform_file', default="None", action=CheckExt({'txt','TXT'}), metavar='FILE', help='Apply a 4x4 transform from a file (default: %(default)s)')
    parser_create_tube.add_argument('--inner_radius', type=float, default=0.5, help='Inner radius (default: %(default)s)')
    parser_create_tube.add_argument('--outer_radius', type=float, default=1.0, help='Outer radius (default: %(default)s)')
    parser_create_tube.add_argument('--height', type=float, default=1.0, help='Tube height (default: %(default)s)')
    parser_create_tube.add_argument('--resolution', type=int, default=6, metavar='RES', help='Tube resolution (default: %(default)s)')
    parser_create_tube.add_argument('--rotate', type=float, nargs=3, default=[0,0,0], metavar='0', help='Rotation angle about X, Y and Z axes (default: %(default)s)')
    parser_create_tube.add_argument('--visualize', action='store_true', help='Visualize the model (default: %(default)s)')
    parser_create_tube.add_argument('--overwrite', action='store_true', help='Overwrite output without asking (default: %(default)s)')
    parser_create_tube.set_defaults(func=create_tube)

    # parser for create_cube
    parser_create_cube = subparsers.add_parser('create_cube')
    parser_create_cube.add_argument('output_file', action=CheckExt({'stl','STL'}), help='Output STL image file name')
    parser_create_cube.add_argument('--transform_file', default="None", action=CheckExt({'txt','TXT'}), metavar='FILE', help='Apply a 4x4 transform from a file (default: %(default)s)')
    parser_create_cube.add_argument('--bounds', type=float, nargs=6, default=[0,1,0,1,0,1], metavar='0', help='Cube bounds in units mm (default: %(default)s)')
    parser_create_cube.add_argument('--rotate', type=float, nargs=3, default=[0,0,0], metavar='0', help='Rotation angle about X, Y and Z axes (default: %(default)s)')
    parser_create_cube.add_argument('--visualize', action='store_true', help='Visualize the model (default: %(default)s)')
    parser_create_cube.add_argument('--overwrite', action='store_true', help='Overwrite output without asking (default: %(default)s)')
    parser_create_cube.set_defaults(func=create_cube)
    
    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('RapidPrototype', vars(args)))
        
    # Run program
    args.func(**vars(args))

if __name__ == '__main__':
    main()
