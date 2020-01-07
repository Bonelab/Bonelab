
# Imports
import argparse
import os
import vtk

from bonelab.util.echo_arguments import echo_arguments
from bonelab.io.vtk_helpers import get_vtk_reader

def SliceViewer(input_filename, window, level, nThreads):
    # Python 2/3 compatible input
    from six.moves import input

    # Read input
    if not os.path.isfile(input_filename):
        os.sys.exit('[ERROR] Cannot find file \"{}\"'.format(input_filename))

    # Set a minimum thread count
    nThreads = max(1, nThreads)

    # Read the input
    reader = get_vtk_reader(input_filename)
    if reader is None:
        os.sys.exit('[ERROR] Cannot find reader for file \"{}\"'.format(input_filename))

    print('Reading input image ' + input_filename)
    reader.SetFileName(input_filename)
    reader.Update()

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
    renderWindow.AddRenderer(renderer)

    interactor = vtk.vtkRenderWindowInteractor()
    interactorStyle = vtk.vtkInteractorStyleImage()
    interactorStyle.SetInteractionModeToImageSlicing()
    interactorStyle.KeyPressActivationOn()

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
    interactor.Start()

def main():
    # Setup description
    description='''2D slice visualizer

The following keyboard mappings are available:
    w   Print window/Level to terminal
    n   Set interpolator to nearest neighbour
    c   Set interpolator to cubic
    r   Reset window/level
    x   View in x-plane
    y   View in y-plane
    z   View in z-plane
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
    parser.add_argument('--window',
                    default=float(0), type=float,
                    help='The initial window. If window is zero or less, the window is computed from the dynamic range of the image.')
    parser.add_argument('--level',
                        default=float(0), type=float,
                        help='The initial level. If window is zero or less, the level is computed from the dynamic range of the image.')
    parser.add_argument('--nThreads', '-n', 
                        default=int(1), type=int,
                        help='Number of threads for each image slice visualizer (default: %(default)s)')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('SliceViewer', vars(args)))

    # Run program
    SliceViewer(**vars(args))

if __name__ == '__main__':
    main()
