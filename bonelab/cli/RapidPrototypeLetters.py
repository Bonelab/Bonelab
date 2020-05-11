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

def CreateShapes(output_filename, 
                 dim, el_size_mm,
                 shape_letters, text, overwrite):
  
  # Check if output exists and should overwrite
  if os.path.isfile(output_filename) and not overwrite:
    result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_filename))
    if result.lower() not in ['y', 'yes']:
      print('Not overwriting. Exiting...')
      os.sys.exit()
  
  # Create vector text
  vecText = vtk.vtkVectorText()
  vecText.SetText(text)
    
  # Apply linear extrusion 
  extrude = vtk.vtkLinearExtrusionFilter()
  extrude.SetInputConnection( vecText.GetOutputPort() )
  extrude.SetExtrusionTypeToNormalExtrusion()
  extrude.SetVector(0, 0, 1 )
  extrude.SetScaleFactor (0.5)
    
  triangleFilter = vtk.vtkTriangleFilter()
  triangleFilter.SetInputConnection( extrude.GetOutputPort() )

  triangleFilter.Update()
  print(triangleFilter.GetOutput().GetBounds())
  width = triangleFilter.GetOutput().GetBounds()[1] - triangleFilter.GetOutput().GetBounds()[0]
  print(width)
  targetWidth = 20
  
  transform = vtk.vtkTransform()
  transform.Scale(5,1,1)
  
  transformFilter = vtk.vtkTransformFilter()
  transformFilter.SetInputConnection( triangleFilter.GetOutputPort() )
  transformFilter.SetTransform( transform )

  transformFilter.Update()
  print(transformFilter.GetOutput().GetBounds())
  exit()

  mapper = vtk.vtkDataSetMapper()
  mapper.SetInputConnection( triangleFilter.GetOutputPort() )

  actor = vtk.vtkActor()
  actor.SetMapper(mapper)
  actor.GetProperty().SetColor(0.8900, 0.8100, 0.3400)
    
  renderWindow = vtk.vtkRenderWindow()
  
  renderer = vtk.vtkRenderer()
  renderer.SetBackground(.4, .5, .7)

  renderWindow.AddRenderer( renderer )
  renderWindow.SetSize(2000,2000)

  renderer.AddActor( actor )
  
  renderer.ResetCamera()
  renderer.GetActiveCamera().Azimuth(30)
  renderer.GetActiveCamera().Elevation(30)
  renderer.GetActiveCamera().Dolly(1.0)
  renderer.ResetCameraClippingRange()

  renderWindowInteractor = vtk.vtkRenderWindowInteractor()
  renderWindowInteractor.SetRenderWindow( renderWindow )
  renderWindow.Render()
  renderWindowInteractor.Start()
  
  
  
  # int main(int, char *[])
  # {  
  #   vtkSmartPointer<vtkSphereSource> sphereSource = 
  #     vtkSmartPointer<vtkSphereSource>::New();  
  #   sphereSource->SetRadius(20);
  #   sphereSource->SetPhiResolution(30);
  #   sphereSource->SetThetaResolution(30);
  #   vtkSmartPointer<vtkPolyData> pd = sphereSource->GetOutput();
  #   sphereSource->Update();
  # 
  #   vtkSmartPointer<vtkImageData> whiteImage = 
  #     vtkSmartPointer<vtkImageData>::New();    
  #   double bounds[6];
  #   pd->GetBounds(bounds);
  #   double spacing[3]; // desired volume spacing
  #   spacing[0] = 0.5;
  #   spacing[1] = 0.5;
  #   spacing[2] = 0.5;
  #   whiteImage->SetSpacing(spacing);
  # 
  #   // compute dimensions
  #   int dim[3];
  #   for (int i = 0; i < 3; i++)
  #     {
  #     dim[i] = static_cast<int>(ceil((bounds[i * 2 + 1] - bounds[i * 2]) / spacing[i]));
  #     }
  #   whiteImage->SetDimensions(dim);
  #   whiteImage->SetExtent(0, dim[0] - 1, 0, dim[1] - 1, 0, dim[2] - 1);
  # 
  #   double origin[3];
  #   origin[0] = bounds[0] + spacing[0] / 2;
  #   origin[1] = bounds[2] + spacing[1] / 2;
  #   origin[2] = bounds[4] + spacing[2] / 2;
  #   whiteImage->SetOrigin(origin);
  #   whiteImage->AllocateScalars(VTK_UNSIGNED_CHAR,1);
  # 
  #   // fill the image with foreground voxels:
  #   unsigned char inval = 255;
  #   unsigned char outval = 0;
  #   vtkIdType count = whiteImage->GetNumberOfPoints();
  #   for (vtkIdType i = 0; i < count; ++i)
  #     {
  #     whiteImage->GetPointData()->GetScalars()->SetTuple1(i, inval);
  #     }
  # 
  #   // polygonal data --> image stencil:
  #   vtkSmartPointer<vtkPolyDataToImageStencil> pol2stenc = 
  #     vtkSmartPointer<vtkPolyDataToImageStencil>::New();
  #   pol2stenc->SetInputData(pd);
  #   pol2stenc->SetOutputOrigin(origin);
  #   pol2stenc->SetOutputSpacing(spacing);
  #   pol2stenc->SetOutputWholeExtent(whiteImage->GetExtent());
  #   pol2stenc->Update();
  # 
  #   // cut the corresponding white image and set the background:
  #   vtkSmartPointer<vtkImageStencil> imgstenc = 
  #     vtkSmartPointer<vtkImageStencil>::New();
  #   imgstenc->SetInputData(whiteImage);
  #   imgstenc->SetStencilConnection(pol2stenc->GetOutputPort());
  #   imgstenc->ReverseStencilOff();
  #   imgstenc->SetBackgroundValue(outval);
  #   imgstenc->Update();
  # 
  #   vtkSmartPointer<vtkMetaImageWriter> writer = 
  #     vtkSmartPointer<vtkMetaImageWriter>::New();
  #   writer->SetFileName("SphereVolume.mhd");
  #   writer->SetInputData(imgstenc->GetOutput());
  #   writer->Write();  
  
  
  # Read input
  # if not os.path.isfile(input_filename):
  #   os.sys.exit('[ERROR] Cannot find file \"{}\"'.format(input_filename))
  # 
  # log("Reading AIM file " + input_filename)
  # reader = vtkbone.vtkboneAIMReader()
  # reader.SetFileName(input_filename)
  # reader.DataOnCellsOff()
  # reader.Update()
  # 
  # image = reader.GetOutput()
  # log("Read %d points from AIM file." % image.GetNumberOfPoints())
  # image_bounds = image.GetBounds()
  # log("Image bounds:", (" %.4f"*6) % image_bounds)
  # image_extent = image.GetExtent()
  # log("Image extent:", (" %d"*6) % image_extent)
  # 
  # log("Gaussian smoothing.")
  # gauss = vtk.vtkImageGaussianSmooth()
  # gauss.SetStandardDeviation(gaussian)
  # gauss.SetRadiusFactor(radius)
  # gauss.SetInputConnection(reader.GetOutputPort())
  # gauss.Update()
  # log("Total of %d voxels" % gauss.GetOutput().GetNumberOfCells())
  # 
  # log ("Padding the data.")
  # pad = vtk.vtkImageConstantPad()
  # pad.SetConstant(0)
  # pad.SetOutputWholeExtent(image_extent[0]-1,image_extent[1]+1,
  #                          image_extent[2]-1,image_extent[3]+1,
  #                          image_extent[4]-1,image_extent[5]+1)
  # pad.SetInputConnection(gauss.GetOutputPort())
  # pad.Update()
  # log("Total of %d padded voxels" % pad.GetOutput().GetNumberOfCells())
  # 
  # log("Extracting isosurface.")
  # mcube = vtk.vtkImageMarchingCubes()
  # mcube.SetValue(0,marching_cubes)
  # mcube.SetInputConnection(pad.GetOutputPort())
  # mcube.Update()
  # log("Generated %d triangles" % mcube.GetOutput().GetNumberOfCells())
  # #log(" mcube %s" % mcube.GetOutput())
  # 
  # if (decimation>0.0 and decimation<1.0):
  #   log("Decimating the isosurface.")
  #   deci = vtk.vtkDecimatePro()
  #   deci.SetInputConnection(mcube.GetOutputPort())
  #   deci.SetTargetReduction(decimation) # 0 to 1, 0 is no decimation.
  #   deci.Update()
  #   log("Decimated to %d triangles" % deci.GetOutput().GetNumberOfCells())
  #   mesh = deci.GetOutputPort()
  # else:
  #   log("No decimation of the isosurface will be performed.")
  #   mesh = mcube.GetOutputPort()
  #     
  # if (visualize):
  #   
  #   ren = vtk.vtkRenderer()
  #   renWin = vtk.vtkRenderWindow()
  #   renWin.AddRenderer(ren)
  #   renWin.SetSize(600,600)
  #   renWin.SetWindowName("Bone Imaging Laboratory")
  #   
  #   iren = vtk.vtkRenderWindowInteractor()
  #   iren.SetRenderWindow(renWin)
  #   
  #   mapper = vtk.vtkPolyDataMapper()
  #   mapper.ScalarVisibilityOff()
  #   mapper.SetInputConnection(mesh)
  #   #mapper.SetInputConnection(mcube.GetOutputPort())
  #   actor = vtk.vtkActor()
  #   #actor.GetProperty().SetColor(.5,.5,.5)
  #   actor.SetMapper(mapper)
  #   
  #   ren.AddActor(actor)
  #   ren.SetBackground(.8,.8,.8)
  #    
  #   iren.Initialize()
  #   renWin.Render()
  #   iren.Start()
  # 
  # log("Writing STL file.")
  # writer = vtk.vtkSTLWriter()
  # writer.SetFileName(output_filename)
  # writer.SetFileTypeToBinary()
  # #writer.SetFileTypeToASCII()
  # writer.SetInputConnection(mesh)
  # #writer.SetInputConnection(mcube.GetOutputPort())
  # log("Writing mesh to " + output_filename)
  # writer.Write()
  
  log("Done.")

def main():
    # Setup description
    description='''Generates AIM shapes.

This is a utility that can create an AIM file for a variety of shapes.
'''

    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blRapidPrototypeLetters",
        description=description
    )
    #parser.add_argument('input_filename', help='Input image file')
    parser.add_argument('output_filename', help='Output image file')
    #parser.add_argument('-g', '--gaussian', type=float, default=0.7, help='Gaussian standard deviation (default: %(default)s)')
    #parser.add_argument('-r', '--radius', type=float, default=1.0, help='Gaussian radius support (default: %(default)s)')
    #parser.add_argument('-m', '--marching_cubes', type=float, default=50.0, help='Marching cubes threshold (default: %(default)s)')
    parser.add_argument('--dim', type=int, nargs=3, default=[100,100,100], help='Set dimensions of output file (default: %(default)s)')
    parser.add_argument('--el_size_mm', type=float, nargs=3, default=[0.0607,0.0607,0.0607], help='Set element size of output file (default: %(default)s)')
    parser.add_argument('--shape_letters', action='store_true', help='Visualize the STL mesh (default: %(default)s)')
    parser.add_argument('--text', default="Hello!", help='Letters for 3D rendering (default: %(default)s)')
    parser.add_argument('--overwrite','-o',action='store_true', help='Overwrite output without asking (default: %(default)s)')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('RapidPrototypeLetters', vars(args)))

    # Run program
    CreateShapes(**vars(args))

if __name__ == '__main__':
    main()
