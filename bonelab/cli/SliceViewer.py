
# Imports
import argparse
import os
import vtk

from bonelab.util.echo_arguments import echo_arguments
from bonelab.io.vtk_helpers import get_vtk_reader

def SliceViewer(input_filename, window, level, nThreads, image_orientation, slice_percent, offscreen, outfile):
    # Python 2/3 compatible input
    from six.moves import input

    # Read input
    if not os.path.isfile(input_filename):
        os.sys.exit('[ERROR] Cannot find file \"{}\"'.format(input_filename))

    # Set a minimum thread count
    nThreads = max(1, nThreads)
    
    # Offscreen setup
    if offscreen and (outfile is None):
        # Create default output filename for image
        name, ext = os.path.splitext(input_filename)
        if 'gz' in ext:
            name = os.path.splitext(name)[0]  # Manages files with double extension
        outfile = '{}_{}_{:.0f}_2d.tif'.format(name,image_orientation, slice_percent)
        print('[WARNING]: No filename specified for output image.')
        print('           Creating a filename based on input file.')
        print('           {}'.format(outfile))
    
    # Read the input
    reader = get_vtk_reader(input_filename)
    if reader is None:
        os.sys.exit('[ERROR] Cannot find reader for file \"{}\"'.format(input_filename))

    print('Reading input image ' + input_filename)
    reader.SetFileName(input_filename)
    reader.Update()

    image_bounds = reader.GetOutput().GetBounds()

    # Get scalar range for W/L and padding
    scalarRanges = reader.GetOutput().GetScalarRange()

    # Determine if we need to autocompute the window/level
    if window <= 0:
        window = scalarRanges[1] - scalarRanges[0]
        level = (scalarRanges[1] + scalarRanges[0])/2

    # Setup input Mapper + Property -> Slice
    inputMapper = vtk.vtkOpenGLImageSliceMapper()
    inputMapper.SetInputConnection(reader.GetOutputPort())
    inputMapper.SliceAtFocalPointOn()
    inputMapper.SliceFacesCameraOn()
    inputMapper.BorderOn()
    inputMapper.SetNumberOfThreads(nThreads)
    inputMapper.StreamingOn()
        
    imageProperty = vtk.vtkImageProperty()
    imageProperty.SetColorLevel(level)
    imageProperty.SetColorWindow(window)
    imageProperty.SetInterpolationTypeToNearest()

    inputSlice = vtk.vtkImageSlice()
    inputSlice.SetMapper(inputMapper)
    inputSlice.SetProperty(imageProperty)

    # Create Renderer -> RenderWindow -> RenderWindowInteractor -> InteractorStyle
    renderer = vtk.vtkRenderer()
    renderer.AddActor(inputSlice)

    renderWindow = vtk.vtkRenderWindow()
    renderWindow.SetSize(2048,2048)
    renderWindow.AddRenderer(renderer)
    if offscreen:
        renderWindow.SetOffScreenRendering(1)

    interactorStyle = vtk.vtkInteractorStyleImage()
    interactorStyle.SetInteractionModeToImageSlicing()
    interactorStyle.SetCurrentRenderer(renderer)
      
    # Set image orientation
    print('Image orientation set to {}'.format(image_orientation))
    if image_orientation == 'sagittal': # 'x' key
        interactorStyle.SetImageOrientation((0,1,0), (0,0,-1))
    elif image_orientation == 'coronal': # 'y' key
        interactorStyle.SetImageOrientation((1,0,0), (0,0,-1))
    elif image_orientation == 'axial': # 'z' key
        interactorStyle.SetImageOrientation((1,0,0), (0,1,0))
    else:
        print('Error selecting image orientation')
        os.sys.exit()
    renderer.ResetCamera()
        
    # Set slice
    print('Percent slice set to {:.1f}%'.format(slice_percent))
    camera = renderer.GetActiveCamera()
    fp = list(camera.GetFocalPoint())
    print(fp)
    if image_orientation == 'sagittal': # 'x' key
        fp[0] = (image_bounds[1] - image_bounds[0]) * slice_percent / 100.0
    elif image_orientation == 'coronal': # 'y' key
        fp[1] = (image_bounds[3] - image_bounds[2]) * slice_percent / 100.0
    elif image_orientation == 'axial': # 'z' key
        fp[2] = (image_bounds[5] - image_bounds[4]) * slice_percent / 100.0
    else:
        print('Error selecting percent slice')
        os.sys.exit()
    camera.SetFocalPoint(fp)

    fp = list(renderer.GetActiveCamera().GetFocalPoint())
    print('Focal point is '+', '.join('{:.1f}'.format(i) for i in fp))

    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetInteractorStyle(interactorStyle)
    interactor.SetRenderWindow(renderWindow)

    # Add some functionality to switch layers for window/level
    def layerSwitcher(obj,event):
        if str(interactor.GetKeyCode()) == 'w':
            print("Image W/L: {w}/{l}".format(w=imageProperty.GetColorWindow(), l=imageProperty.GetColorLevel()))
        elif str(interactor.GetKeyCode()) == 'n':
            # Set interpolation to nearest neighbour (good for voxel visualization)
            imageProperty.SetInterpolationTypeToNearest()
            interactor.Render()
        elif str(interactor.GetKeyCode()) == 'c':
            # Set interpolation to cubic (makes a better visualization)
            imageProperty.SetInterpolationTypeToCubic()
            interactor.Render()
        elif str(interactor.GetKeyCode()) == 'r':
            window = scalarRanges[1] - scalarRanges[0]
            level = (scalarRanges[1] + scalarRanges[0])/2
            imageProperty.SetColorLevel(level)
            imageProperty.SetColorWindow(window)
            interactor.Render()

    # Add ability to switch between active layers
    interactor.AddObserver('KeyPressEvent', layerSwitcher, -1.0) # Call layerSwitcher as last observer
    
    # Initialize and go
    interactor.Initialize()
    if not offscreen:
        interactor.Start()

    if outfile is not None:
        interactor.Render()
        windowToImage = vtk.vtkWindowToImageFilter()
        windowToImage.SetInput(renderWindow)
        
        writer = vtk.vtkTIFFWriter()
        writer.SetFileName(outfile)
        writer.SetInputConnection(windowToImage.GetOutputPort())
        writer.Write()
        print('Writing {}'.format(outfile))
    
def main():
    # Setup description
    description='''2D slice visualizer

The following keyboard mappings are available:
    w   Print window/Level to terminal
    n   Set interpolator to nearest neighbour
    c   Set interpolator to cubic
    r   Reset window/level
    x   View in x-plane (saggital)
    y   View in y-plane (coronal)
    z   View in z-plane (axial)
    q   Quit

The following mouse mappings are available:
    left click + vertical scroll                Modify window
    left click + horizontal scroll              Modify level
    right click + vertical scroll               Zoom
    control + left click + vertical scroll      Slice level
    control + right click + vertical scroll     Rotate slice
    shift + left click + vertical scroll        Translate slice
'''

    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blSliceViewer",
        description=description
    )
    parser.add_argument('input_filename', help='Input image file')
    parser.add_argument('--window', default=float(0), type=float, help='The initial window. If window is zero or less, the window is computed from the dynamic range of the image.')
    parser.add_argument('--level', default=float(0), type=float, help='The initial level. If window is zero or less, the level is computed from the dynamic range of the image.')
    parser.add_argument('--nThreads', '-n', default=int(1), type=int, help='Number of threads for each image slice visualizer (default: %(default)s)')
    parser.add_argument('--image_orientation', default='sagittal', choices=['sagittal', 'coronal', 'axial'],
                                                           help='Initiate a particular orientation (default: %(default)s)')
    parser.add_argument('--slice_percent', default=float(50), type=float, help='Set percent slice through image (default: %(default)s)')
    parser.add_argument('--offscreen', action='store_true', help='Set to offscreen rendering (default: %(default)s)')
    parser.add_argument('-o','--outfile', default=None, metavar='FN', help='Output image file (*.tif) (default: %(default)s)')
    
    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('SliceViewer', vars(args)))

    # Run program
    SliceViewer(**vars(args))

if __name__ == '__main__':
    main()
