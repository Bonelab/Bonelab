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
#   - Flip plans is not working. I think we'd have to go to 7.1 to get it working...
#   - Key Bindings:
#       Left Click          Scroll through slices
#       CTRL + Left Click   Change window/level
#       1                   Set active image to image 1. Allows Window/Level on image 1.
#       2                   Set active image to image 2. Allows Window/Level on image 2.
#       3                   Invert color scheme
#       X/Y/Z               Slice sagittal/coronal/axial
#       Right Click         Zoom camera
#       Shift + Left Click  Pan camera
#
# Usage:
#   python checkerBoardViewer.py input1.nii input2.nii

# Imports
import os
import math
import vtk
import vtkbone
import argparse

# Parse arguments
parser = argparse.ArgumentParser(
    description='''Checkerboard Viewer.
    Instructrions for use are as follows:
        Left Click          Scroll through slices
        CTRL + Left Click   Change window/level
        1                   Set active image to image 1. Allows Window/Level on image 1.
        2                   Set active image to image 2. Allows Window/Level on image 2.
        3                   Invert color scheme
        X/Y/Z               Slice sagittal/coronal/axial
        Right Click         Zoom camera
        Shift + Left Click  Pan camera''',
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
parser.add_argument('-w', '--window',
                    default=[0,0], type=float, nargs=2,
                    help='The initial window. If it is zero or less, take scalar range')
parser.add_argument('-l', '--level',
                    default=[0,0], type=float, nargs=2,
                    help='The initial level. If window is zero or less, take average of scalar range')
parser.add_argument('-d', '--divisions',
                    default=[10, 10], type=int, nargs=2,
                    help='The divisions')
parser.add_argument('-n', '--nThreads',
                    default=int(1), type=int,
                    help='Number of threads for each image slice visualizer')
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

# Get scalar range for W/L and padding
scalarRanges = [reader1.GetOutput().GetScalarRange(), reader2.GetOutput().GetScalarRange()]

# Determine window/level if needed
print("Window/Level:")
window = args.window
level = args.level
for i in range(len(args.window)):
    # Check if we should calculate (cannot have window less than or equal to zero)
    if args.window[i] <= 0:
        window[i] = scalarRanges[i][1] - scalarRanges[i][0]
        level[i] = (scalarRanges[i][1] + scalarRanges[i][0])/2

    # Print resulting window/level
    print("\tImage {i}: {w}/{l}".format(i=i+1, w=window[i], l=level[i]))

# Setup input1 Mapper + Property -> Slice
input1Mapper = vtk.vtkImageResliceMapper()
input1Mapper.SetInputConnection(reader1.GetOutputPort())
input1Mapper.SliceAtFocalPointOn()
input1Mapper.SliceFacesCameraOn()
input1Mapper.BorderOn()
input1Mapper.SetNumberOfThreads(args.nThreads)

image1Property = vtk.vtkImageProperty()
image1Property.SetColorLevel(level[0])
image1Property.SetColorWindow(window[0])
image1Property.SetInterpolationTypeToCubic()
image1Property.CheckerboardOn()
image1Property.SetCheckerboardSpacing(args.divisions)
image1Property.SetLayerNumber(1)

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

image2Property = vtk.vtkImageProperty()
image2Property.SetColorLevel(level[1])
image2Property.SetColorWindow(window[1])
image2Property.SetInterpolationTypeToCubic()
image2Property.CheckerboardOn()
image2Property.SetCheckerboardSpacing(args.divisions)
image2Property.SetCheckerboardOffset(0,1) # offset from image1 checkerboard
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

interactor.SetInteractorStyle(interactorStyle)
interactor.SetRenderWindow(renderWindow)

def layerSwitcher(obj,event):
    if str(interactor.GetKeyCode()) == '1':
        imageStack.SetActiveLayer(1)
    elif str(interactor.GetKeyCode()) == '2':
        imageStack.SetActiveLayer(2)
    elif str(interactor.GetKeyCode()) == 'w':
        print("Image 1 W/L: {w}/{l}".format(w=image1Property.GetColorWindow(), l=image1Property.GetColorLevel()))
        print("Image 2 W/L: {w}/{l}".format(w=image2Property.GetColorWindow(), l=image2Property.GetColorLevel()))

# Add ability to switch between active layers
interactor.AddObserver('KeyPressEvent', layerSwitcher, -1.0)

interactor.Initialize()
interactor.Start()
