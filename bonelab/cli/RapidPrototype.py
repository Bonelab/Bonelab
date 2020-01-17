#Imports
import argparse
import os
import sys
import time
import vtk
import vtkbone

from bonelab.util.echo_arguments import echo_arguments

#  Utility function
def log(msg, *additionalLines):
   """Print message with time stamp.
   
   The first argument is printed with the a time stamp.
   Subsequent arguments are printed one to a line without a timestamp.
   """
   print('{0:8.2f} {1:s}'.format(time.time()-start_time, msg))
   for line in additionalLines:
       print(" " * 9 + line)
start_time = time.time()

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

  log("Reading AIM file " + input_filename)
  reader = vtkbone.vtkboneAIMReader()
  reader.SetFileName(input_filename)
  reader.DataOnCellsOff()
  reader.Update()

  image = reader.GetOutput()
  log("Read %d points from AIM file." % image.GetNumberOfPoints())
  image_bounds = image.GetBounds()
  log("Image bounds:", (" %.4f"*6) % image_bounds)
  image_extent = image.GetExtent()
  log("Image extent:", (" %d"*6) % image_extent)

  log("Gaussian smoothing.")
  gauss = vtk.vtkImageGaussianSmooth()
  gauss.SetStandardDeviation(gaussian)
  gauss.SetRadiusFactor(radius)
  gauss.SetInputConnection(reader.GetOutputPort())
  gauss.Update()
  log("Total of %d voxels" % gauss.GetOutput().GetNumberOfCells())
  
  log ("Padding the data.")
  pad = vtk.vtkImageConstantPad()
  pad.SetConstant(0)
  pad.SetOutputWholeExtent(image_extent[0]-1,image_extent[1]+1,
                           image_extent[2]-1,image_extent[3]+1,
                           image_extent[4]-1,image_extent[5]+1)
  pad.SetInputConnection(gauss.GetOutputPort())
  pad.Update()
  log("Total of %d padded voxels" % pad.GetOutput().GetNumberOfCells())

  log("Extracting isosurface.")
  mcube = vtk.vtkImageMarchingCubes()
  mcube.SetValue(0,marching_cubes)
  mcube.SetInputConnection(pad.GetOutputPort())
  mcube.Update()
  log("Generated %d triangles" % mcube.GetOutput().GetNumberOfCells())
  #log(" mcube %s" % mcube.GetOutput())
  
  if (decimation>0.0 and decimation<1.0):
    log("Decimating the isosurface.")
    deci = vtk.vtkDecimatePro()
    deci.SetInputConnection(mcube.GetOutputPort())
    deci.SetTargetReduction(decimation) # 0 to 1, 0 is no decimation.
    deci.Update()
    log("Decimated to %d triangles" % deci.GetOutput().GetNumberOfCells())
    mesh = deci.GetOutputPort()
  else:
    log("No decimation of the isosurface will be performed.")
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

  log("Writing STL file.")
  writer = vtk.vtkSTLWriter()
  writer.SetFileName(output_filename)
  writer.SetFileTypeToBinary()
  #writer.SetFileTypeToASCII()
  writer.SetInputConnection(mesh)
  #writer.SetInputConnection(mcube.GetOutputPort())
  log("Writing mesh to " + output_filename)
  writer.Write()
  
  log("Done.")

def main():
    # Setup description
    description='''Generates STL file for rapid prototyping from AIM.

Input AIM must be type 'char'. STL mesh properties can be controlled 
by setting gaussian smoothing and isosurface. The number of polygons
can be reduced (decimation).

For now only AIM files can be used as input.
'''

    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blRapidPrototype",
        description=description
    )
    parser.add_argument('input_filename', help='Input image file')
    parser.add_argument('output_filename', help='Output image file')
    parser.add_argument('-g', '--gaussian', type=float, default=0.7, help='Gaussian standard deviation')
    parser.add_argument('-r', '--radius', type=float, default=1.0, help='Gaussian radius support')
    parser.add_argument('-m', '--marching_cubes', type=float, default=50.0, help='Marching cubes threshold')
    parser.add_argument('-d', '--decimation', type=float, default=0.85, help='Decimation between 0 and 1. To skip set to 1')
    parser.add_argument('-v', '--visualize', action='store_false', help='Visualize the STL mesh')
    parser.add_argument('-o', '--overwrite', action='store_true', help='Overwrite output without asking')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('RapidPrototype', vars(args)))

    # Run program
    CreateSTL(**vars(args))

if __name__ == '__main__':
    main()
