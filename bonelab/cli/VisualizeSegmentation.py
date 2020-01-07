
# Imports
import argparse
import os
import vtk

from bonelab.util.echo_arguments import echo_arguments
from bonelab.io.vtk_helpers import get_vtk_reader

def VisualizeSegmentation(input_filename, segmentation_filename, window, level, nThreads, opacity):
    # Python 2/3 compatible input
    from six.moves import input

    # Read input
    for filename in [input_filename, segmentation_filename]:
        if not os.path.isfile(filename):
            os.sys.exit('[ERROR] Cannot find file \"{}\"'.format(filename))

    # Set a minimum thread count
    nThreads = max(1, nThreads)

    # Max/min opacity
    opacity = max(0, opacity)
    opacity = min(1, opacity)

    # Read the input
    image_reader = get_vtk_reader(input_filename)
    if image_reader is None:
        os.sys.exit('[ERROR] Cannot find reader for file \"{}\"'.format(input_filename))

    print('Reading input image ' + input_filename)
    image_reader.SetFileName(input_filename)
    image_reader.Update()

    # Read the segmentation
    seg_reader = get_vtk_reader(segmentation_filename)
    if seg_reader is None:
        os.sys.exit('[ERROR] Cannot find reader for file \"{}\"'.format(segmentation_filename))

    print('Reading input image ' + segmentation_filename)
    seg_reader.SetFileName(segmentation_filename)
    seg_reader.Update()

    # Get scalar range for W/L and padding
    image_scalar_range = image_reader.GetOutput().GetScalarRange()

    # Determine if we need to autocompute the window/level
    if window <= 0:
        window = image_scalar_range[1] - image_scalar_range[0]
        level = (image_scalar_range[1] + image_scalar_range[0])/2

    # Get data range
    seg_scalar_range = [int(x) for x in seg_reader.GetOutput().GetScalarRange()]
    if seg_scalar_range[0] < 0:
        os.sys.exit("Segmentation image \"{}\" has values less than zero which cannot currently be handled. Exiting...".format(segmentation_filename))
    nLabels = seg_scalar_range[1]
    print("Segmented image has {} labels".format(nLabels))

    # Setup LUT
    segLUT = vtk.vtkLookupTable()
    segLUT.SetRange(0,nLabels)
    segLUT.SetRampToLinear()
    segLUT.SetAlphaRange(1,1) # Make it slightly transparent
    segLUT.Build()
    segLUT.SetTableValue(0, 0.0, 0.0, 0.0, 0.0 ) # Set zero to black, transparent

    # Setup input Mapper + Property -> Slice
    inputMapper = vtk.vtkImageResliceMapper()
    inputMapper.SetInputConnection(image_reader.GetOutputPort())
    inputMapper.SliceAtFocalPointOn()
    inputMapper.SliceFacesCameraOn()
    inputMapper.BorderOn()
    inputMapper.SetNumberOfThreads(nThreads)
    inputMapper.ResampleToScreenPixelsOn()
    inputMapper.StreamingOn()

    imageProperty = vtk.vtkImageProperty()
    imageProperty.SetColorLevel(level)
    imageProperty.SetColorWindow(window)
    imageProperty.SetLayerNumber(1)
    imageProperty.SetInterpolationTypeToNearest()

    inputSlice = vtk.vtkImageSlice()
    inputSlice.SetMapper(inputMapper)
    inputSlice.SetProperty(imageProperty)

    # Setup seg Mapper + Property -> Slice
    segImageProperty = vtk.vtkImageProperty()
    segImageProperty.SetLookupTable(segLUT)
    segImageProperty.UseLookupTableScalarRangeOn()
    segImageProperty.SetInterpolationTypeToLinear()
    segImageProperty.SetOpacity(opacity)
    segImageProperty.SetLayerNumber(2)
    segImageProperty.SetInterpolationTypeToNearest()

    segMapper = vtk.vtkImageResliceMapper()
    segMapper.SetInputConnection(seg_reader.GetOutputPort())
    segMapper.SliceAtFocalPointOn()
    segMapper.SliceFacesCameraOn()
    segMapper.BorderOn()
    segMapper.SetNumberOfThreads(nThreads)
    segMapper.ResampleToScreenPixelsOn()
    segMapper.StreamingOn()

    segSlice = vtk.vtkImageSlice()
    segSlice.SetProperty(segImageProperty)
    segSlice.SetMapper(segMapper)

    # Add everything to a vtkImageStack
    imageStack = vtk.vtkImageStack()
    imageStack.AddImage(inputSlice)
    imageStack.AddImage(segSlice)
    imageStack.SetActiveLayer(1)

    # Create Renderer -> RenderWindow -> RenderWindowInteractor -> InteractorStyle
    renderer = vtk.vtkRenderer()
    renderer.AddViewProp(imageStack)

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
            # Print the w/l for the image
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
            window = image_scalar_range[1] - image_scalar_range[0]
            level = (image_scalar_range[1] + image_scalar_range[0])/2
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
    description='''Overlay segmentation on visualization

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
        prog="blVisualizeSegmentation",
        description=description
    )
    parser.add_argument('input_filename', help='Input image')
    parser.add_argument('segmentation_filename', help='Input segmentation image')
    parser.add_argument('--window',
                        default=float(500), type=float,
                        help='The initial window')
    parser.add_argument('--level',
                        default=float(0), type=float,
                        help='The initial level')
    parser.add_argument('--nThreads', '-n',
                        default=int(1), type=int,
                        help='Number of threads for each image slice visualizer (default: %(default)s)')
    parser.add_argument('--opacity', '-o',
                        default=float(0.25), type=float,
                        help='The opacity of the segmentation between zero and one (default: %(default)s)')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('VisualizeSegmentation', vars(args)))

    # Run program
    VisualizeSegmentation(**vars(args))

if __name__ == '__main__':
    main()
