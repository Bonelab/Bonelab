# History:
#   2017.03.21  babesler@ucalgary.ca    Created
#
# Description:
#   Visualize two volumes overlayed with a checherboard layout
#
# Notes:
#   - See http://www.vtk.org/Wiki/VTK/Examples/Cxx/Widgets/CheckerboardWidget
#   - Uses a single image property for displaying the image, which is not ideal
#       for multi-modal images
#
# Usage:
#   python checkerBoardViewer.py input1.nii input2.nii

# Imports
import os
import math
import vtk
import argparse
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

# Parse arguments
parser = argparse.ArgumentParser(
    description='Checkerboard Viewer',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
parser.add_argument(
    'inputImage1',
    help='First input file'
    )
parser.add_argument(
    'inputImage2',
    help='Second input file'
    )
parser.add_argument('--window',
                    default=float(0), type=float,
                    help='The initial window')
parser.add_argument('--level',
                    default=float(0), type=float,
                    help='The initial level')
parser.add_argument('-d', '--divisions',
                    default=[10, 10], type=int, nargs=2,
                    help='The spacing between divisions in spacing units (default: %(default)s)')
parser.add_argument('-n', '--nThreads',
                    default=int(1), type=int,
                    help='Number of threads for each image slice visualizer (default: %(default)s)')
args = parser.parse_args()

# Check input arguments
for fileName in [args.inputImage1, args.inputImage2]:
    # Check that input files exist
    if not os.path.isfile(fileName):
        os.sys.exit('Input file \"{fileName}\" does not exist. Exiting...'.format(fileName=fileName))

# Check threads
if args.nThreads < 1:
    os.sys.exit('Number of threads must be one or greater. Given {n}. Exiting...'.format(n=args.nThreads))

# Read in inputs
reader1 = vtk.vtkImageReader2Factory.CreateImageReader2(args.inputImage1)
if reader1 is None:
    if args.inputImage1.lower().endswith('.aim'):
        reader1 = vtkbone.vtkboneAIMReader()
        reader1.DataOnCellsOff()
    elif args.inputImage1.lower().endswith('.nii'):
        reader1 = vtk.vtkNIFTIImageReader()
    elif args.inputImage1.lower().endswith('.dcm'):
        reader1 = vtk.vtkDICOMImageReader()
    else:
        os.sys.exit('Unable to find a reader for \"{fileName}\". Exiting...'.format(fileName=args.inputImage1))
reader1.SetFileName(args.inputImage1)
print('Loading {}...'.format(args.inputImage1))
reader1.Update()

reader2 = vtk.vtkImageReader2Factory.CreateImageReader2(args.inputImage1)
if reader2 is None:
    if args.inputImage2.lower().endswith('.aim'):
        reader2 = vtkbone.vtkboneAIMReader()
        reader2.DataOnCellsOff()
    elif args.inputImage2.lower().endswith('.nii'):
        reader2 = vtk.vtkNIFTIImageReader()
    elif args.inputImage2.lower().endswith('.dcm'):
        reader2 = vtk.vtkDICOMImageReader()
    else:
        os.sys.exit('Unable to find a reader for \"{fileName}\". Exiting...'.format(fileName=args.inputImage2))
reader2.SetFileName(args.inputImage2)
print('Loading {}...'.format(args.inputImage2))
reader2.Update()

# Determine window/level if needed
print("Window/Level:")
window = args.window
level = args.level

# Check if we should calculate (cannot have window less than or equal to zero)
if args.window <= 0:
    # Get scalar range for W/L and padding
    scalarRanges1 = reader1.GetOutput().GetScalarRange()
    scalarRanges2 = reader2.GetOutput().GetScalarRange()
    scalarRanges = [min(scalarRanges1[0], scalarRanges2[0]), max(scalarRanges1[1], scalarRanges2[1])]

    window = scalarRanges[1] - scalarRanges[0]
    level = (scalarRanges[1] + scalarRanges[0])/2

# Print resulting window/level
print("\tImage W/L: {w}/{l}".format(w=window, l=level))


# Setup input1 Mapper + Property -> Slice
input1Mapper = vtk.vtkImageResliceMapper()
input1Mapper.SetInputConnection(reader1.GetOutputPort())
input1Mapper.SliceAtFocalPointOn()
input1Mapper.SliceFacesCameraOn()
input1Mapper.BorderOn()
input1Mapper.SetNumberOfThreads(args.nThreads)
input1Mapper.ResampleToScreenPixelsOn()
input1Mapper.StreamingOn()

image1Property = vtk.vtkImageProperty()
image1Property.SetColorLevel(level)
image1Property.SetColorWindow(window)
image1Property.SetInterpolationTypeToNearest()
image1Property.SetCheckerboardSpacing(args.divisions)
image1Property.SetLayerNumber(1)
image1Property.CheckerboardOn()

input1Slice = vtk.vtkImageSlice()
input1Slice.SetMapper(input1Mapper)
input1Slice.SetProperty(image1Property)

# Setup input2 Mapper + Property -> Slice
input2Mapper = vtk.vtkImageResliceMapper()
input2Mapper.SetInputConnection(reader2.GetOutputPort())
input2Mapper.SliceAtFocalPointOn()
input2Mapper.SliceFacesCameraOn()
input2Mapper.BorderOn()
input2Mapper.SetNumberOfThreads(args.nThreads)
input2Mapper.ResampleToScreenPixelsOn()
input2Mapper.StreamingOn()

image2Property = vtk.vtkImageProperty()
image2Property.SetColorLevel(level)
image2Property.SetColorWindow(window)
image2Property.SetInterpolationTypeToNearest()
image2Property.SetCheckerboardSpacing(args.divisions)
image2Property.SetCheckerboardOffset(0,1) # offset from image1 checkerboard
image2Property.CheckerboardOn()
image2Property.SetLayerNumber(2)

input2Slice = vtk.vtkImageSlice()
input2Slice.SetMapper(input2Mapper)
input2Slice.SetProperty(image2Property)

imageStack = vtk.vtkImageStack()
imageStack.AddImage(input1Slice)
imageStack.AddImage(input2Slice)
imageStack.SetActiveLayer(1)

# Create Renderer -> RenderWindow -> RenderWindowInteractor -> InteractorStyle
renderer = vtk.vtkRenderer()
renderer.AddViewProp(imageStack)
renderer.ResetCamera()

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
        # Print the w/l for both images
        print("Image 1 W/L: {w}/{l}".format(w=image1Property.GetColorWindow(), l=image1Property.GetColorLevel()))
        print("Image 2 W/L: {w}/{l}".format(w=image2Property.GetColorWindow(), l=image2Property.GetColorLevel()))
    elif str(interactor.GetKeyCode()) == 'n':
        # Set interpolation to nearest neighbour (good for voxel visualization)
        image1Property.SetInterpolationTypeToNearest()
        image2Property.SetInterpolationTypeToNearest()
        interactor.Render()
    elif str(interactor.GetKeyCode()) == 'c':
        # Set interpolation to cubic (makes a better visualization)
        image1Property.SetInterpolationTypeToCubic()
        image2Property.SetInterpolationTypeToCubic()
        interactor.Render()

def windowLevelEvent(obj, event):
    image2Property.SetColorLevel(image1Property.GetColorLevel())
    image2Property.SetColorWindow(image1Property.GetColorWindow())

# Add ability to switch between active layers
interactor.AddObserver('KeyPressEvent', layerSwitcher, -1.0) # Call layerSwitcher as last observer
interactorStyle.AddObserver('InteractionEvent', windowLevelEvent, 0.0) # Call layerSwitcher as last observer

# Initialize and go
interactor.Initialize()
interactor.Start()
