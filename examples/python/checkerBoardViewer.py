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
parser.add_argument('-w', '--window',
                    default=float(0), type=float,
                    help='The initial window. If it is zero or less, take scalar range')
parser.add_argument('-l', '--level',
                    default=float(0), type=float,
                    help='The initial level. If window is zero or less, take average of scalar range')
parser.add_argument('-d', '--divisions',
                    #default=[10, 10, 0], type=int, nargs=3,
                    default=[10, 10], type=int, nargs=2,
                    help='The divisions')
args = parser.parse_args()

# Check input arguments
for fileName in [args.inputImage1, args.inputImage2]:
    # Check that input files exist
    if not os.path.isfile(fileName):
        os.sys.exit('Input file \"{fileName}\" does not exist. Exiting...'.format(fileName=fileName))

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

# Get the common extent
extent1 = reader1.GetOutput().GetExtent()
extent2 = reader2.GetOutput().GetExtent()
commonExtent = [0 for x in range(6)]

# Set minimums
for i in [0,2,4]:
    commonExtent[i] = min(extent1[i], extent2[i])

# Set maximums
for i in [1,3,5]:
    commonExtent[i] = max(extent1[i], extent2[i])

print("Updated Extents:")
print("\tFirst Input Extent      {}".format(extent1))
print("\tSecond Input Extent     {}".format(extent2))
print("\tCommon Extent           {}".format(commonExtent))


# Get scalar range for W/L and padding
range1 = reader1.GetOutput().GetScalarRange()
range2 = reader2.GetOutput().GetScalarRange()

print("Padding:")
print("\tFirst padding constant  {}".format(range1[0]))
print("\tSecond padding constant {}".format(range2[0]))

# Determine window/level if needed
if args.window <= 0:
    window1 = range1[1] - range1[0]
    level1 = (range1[1] + range1[0])/2
    window2 = range2[1] - range2[0]
    level2 = (range2[1] + range2[0])/2
else:
    window1 = args.window
    level1 = args.level
    window2 = args.window
    level2 = args.level

print("Window/Level:")
print("\tFirst W/L               {}/{}".format(window1, level1))
print("\tSecond W/L              {}/{}".format(window2, level2))

# Need to pad each image to the same extent
padder1 = vtk.vtkImageConstantPad()
padder1.SetInputConnection(reader1.GetOutputPort())
padder1.SetOutputWholeExtent(commonExtent)
padder1.SetConstant(range1[0])

padder2 = vtk.vtkImageConstantPad()
padder2.SetInputConnection(reader2.GetOutputPort())
padder2.SetOutputWholeExtent(commonExtent)
padder2.SetConstant(range2[0])

# Setup input1 Mapper + Property -> Slice
input1Mapper = vtk.vtkImageResliceMapper()
input1Mapper.SetInputConnection(padder1.GetOutputPort())
input1Mapper.SliceAtFocalPointOn()
input1Mapper.SliceFacesCameraOn()
input1Mapper.BorderOff()

image1Property = vtk.vtkImageProperty()
image1Property.SetColorLevel(level1)
image1Property.SetColorWindow(window1)
image1Property.SetInterpolationTypeToLinear()
image1Property.CheckerboardOn()
image1Property.SetCheckerboardSpacing(args.divisions)
image1Property.SetLayerNumber(1)

input1Slice = vtk.vtkImageSlice()
input1Slice.SetMapper(input1Mapper)
input1Slice.SetProperty(image1Property)

# Setup input2 Mapper + Property -> Slice
input2Mapper = vtk.vtkImageResliceMapper()
input2Mapper.SetInputConnection(padder2.GetOutputPort())
input2Mapper.SliceAtFocalPointOn()
input2Mapper.SliceFacesCameraOn()
input2Mapper.BorderOff()

image2Property = vtk.vtkImageProperty()
image2Property.SetColorLevel(level2)
image2Property.SetColorWindow(window2)
image2Property.SetInterpolationTypeToLinear()
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
#imageStack.SetActiveLayer(1)

# Create Renderer -> RenderWindow -> RenderWindowInteractor -> InteractorStyle
renderer = vtk.vtkRenderer()
renderer.AddViewProp(imageStack)
renderer.ResetCamera()

renderWindow = vtk.vtkRenderWindow()
renderWindow.AddRenderer(renderer)

interactor = vtk.vtkRenderWindowInteractor()
interactorStyle = vtk.vtkInteractorStyleImage()
interactorStyle.SetInteractionModeToImageSlicing()

interactor.SetRenderWindow(renderWindow)
interactor.SetInteractorStyle(interactorStyle)

# TODO: Manually set the plan flipping by registering a callback

interactor.Start()
