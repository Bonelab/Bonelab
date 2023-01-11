# History:
#   2017.04.03  babesler@ucalgary.ca   Created
#   2017.04.25  babesler@ucalgary.ca   Setup threaded visualization
#
# Description:
#   Slice-by-slice visualization
#
# Notes:
#   - Taken from visualizeSegmentation.py
#
# Usage:
#   python sliceViewer.py greyScale

# Libraries
import argparse
import os
import vtk
try:
    import vtkbone
    vtkboneImported = True
    vtkbonelabImported = False
except ImportError:
    vtkboneImported = False
    try:
        import vtkbonelab
        vtkbonelabImported = True
    except ImportError:
        vtkbonelabImported = False

# Setup and parse command line arguments
parser = argparse.ArgumentParser(
    description='Test thresholding, dilation, and overlay',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
parser.add_argument(
    'inputImage',
    help='The input image file'
    )
parser.add_argument('--window',
                    default=float(0), type=float,
                    help='The initial window. If window is zero or less, the window is computed from the dynamic range of the image.')
parser.add_argument('--level',
                    default=float(0), type=float,
                    help='The initial level. If window is zero or less, the level is computed from the dynamic range of the image.')
parser.add_argument('-n', '--nThreads',
                    default=int(1), type=int,
                    help='Number of threads for each image slice visualizer (default: %(default)s)')
args = parser.parse_args()

# Check that the input (file or directory) exists
if not os.path.exists(args.inputImage):
    os.sys.exit('Input \"{inputImage}\" does not exist. Exiting...'.format(inputImage=args.inputImage))

# Check threads
if args.nThreads < 1:
    os.sys.exit('Number of threads must be one or greater. Given {n}. Exiting...'.format(n=args.nThreads))

# Read the image
inputReader = vtk.vtkImageReader2Factory.CreateImageReader2(args.inputImage)
if inputReader is None:
    if args.inputImage.lower().endswith('.nii'):
        inputReader = vtk.vtkNIFTIImageReader()
    elif args.inputImage.lower().endswith('.dcm'):
        inputReader = vtk.vtkDICOMImageReader()
    elif vtkboneImported and args.inputImage.lower().endswith('.aim'):
        inputReader = vtkbone.vtkboneAIMReader()
        inputReader.DataOnCellsOff()
    elif vtkbonelabImported and args.inputImage.lower().endswith('.aim'):
        inputReader = vtkbonelab.vtkbonelabAIMReader()
        inputReader.DataOnCellsOff()
    else:
        os.sys.exit('Unable to find a reader for \"{fileName}\". Exiting...'.format(fileName=args.inputImage))
inputReader.SetFileName(args.inputImage)
print('Loading {}...'.format(args.inputImage))
inputReader.Update()

# Get scalar range for W/L and padding
scalarRanges = inputReader.GetOutput().GetScalarRange()

# Determine window/level if needed
window = args.window
level = args.level

# Determine if we need to autocompute the window/level
if args.window <= 0:
    window = scalarRanges[1] - scalarRanges[0]
    level = (scalarRanges[1] + scalarRanges[0])/2

# Print resulting window/level
print("Image W/L: {w}/{l}".format(w=window, l=level))

# Setup input Mapper + Property -> Slice
inputMapper = vtk.vtkOpenGLImageSliceMapper()
inputMapper.SetInputConnection(inputReader.GetOutputPort())
inputMapper.SliceAtFocalPointOn()
inputMapper.SliceFacesCameraOn()
inputMapper.BorderOn()
inputMapper.SetNumberOfThreads(args.nThreads)
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

# Add ability to switch between active layers
interactor.AddObserver('KeyPressEvent', layerSwitcher, -1.0) # Call layerSwitcher as last observer

# Initialize and go
interactor.Initialize()
interactor.Start()
