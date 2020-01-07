# History:
#   2017.04.10  babesler@ucalgary.ca    Created
#
# Description:
#   Given an image and a grid, overlay them.
#
# Notes:
#   - None
#
# Usage:
#   python overlayGrid.py image checkerboard

# Libraries
import vtk
import argparse
import os

# Setup and parse command line arguments
parser = argparse.ArgumentParser(
    description='Test thresholding, dilation, and overlay',
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
parser.add_argument(
    'inputImage',
    help='The input NIfTI file'
    )
parser.add_argument(
    'inputGrid',
    help='The input NIfTI grid file'
    )
parser.add_argument('-w', '--window',
                    default=float(500), type=float,
                    help='The initial window')
parser.add_argument('-l', '--level',
                    default=float(0), type=float,
                    help='The initial level')
parser.add_argument('-o', '--opacity',
                    default=float(0.25), type=float,
                    help='The grid opacity')
args = parser.parse_args()

# Check that the input (file or directory) exists
for fileName in [args.inputImage,args.inputGrid]:
    if not os.path.exists(fileName):
        os.sys.exit('Input \"{inputImage}\" does not exist. Exiting...'.format(inputImage=fileName))

    if not fileName.lower().endswith('.nii'):
        os.sys.exit('Input \"{inputImage}\" is not of type NIfTI (*.nii). Exiting...'.format(inputImage=fileName))

# Read both images
inputReader = vtk.vtkNIFTIImageReader()
inputReader.SetFileName(args.inputImage)
print("Reading {}".format(args.inputImage))
inputReader.Update()

gridReader = vtk.vtkNIFTIImageReader()
gridReader.SetFileName(args.inputGrid)
print("Reading {}".format(args.inputGrid))
gridReader.Update()

# Setup input Mapper + Property -> Slice
inputMapper = vtk.vtkImageSliceMapper()
inputMapper.SetInputConnection(inputReader.GetOutputPort())
inputMapper.SliceAtFocalPointOn()
inputMapper.SliceFacesCameraOn()
inputMapper.BorderOff()

imageProperty = vtk.vtkImageProperty()
imageProperty.SetColorLevel(args.level)
imageProperty.SetColorWindow(args.window)
imageProperty.SetInterpolationTypeToLinear()
imageProperty.SetLayerNumber(1)

inputSlice = vtk.vtkImageSlice()
inputSlice.SetMapper(inputMapper)
inputSlice.SetProperty(imageProperty)

# Determine an appropriate window/level for the grid
scalarRange = [int(x) for x in gridReader.GetOutput().GetScalarRange()]
window = scalarRange[1] - scalarRange[0]+1
level = (scalarRange[1] + scalarRange[0])/2

# Setup grid Mapper + Property -> Slice
gridImageProperty = vtk.vtkImageProperty()
gridImageProperty.SetOpacity(args.opacity)
gridImageProperty.SetColorLevel(level)
gridImageProperty.SetColorWindow(window)
gridImageProperty.SetLayerNumber(2)
gridImageProperty.SetInterpolationTypeToNearest()

gridMapper = vtk.vtkImageSliceMapper()
gridMapper.SetInputConnection(gridReader.GetOutputPort())
gridMapper.SliceAtFocalPointOn()
gridMapper.SliceFacesCameraOn()
gridMapper.BorderOff()
#gridMapper.ResampleToScreenPixelsOn()
#gridMapper.JumpToNearestSliceOn()

gridSlice = vtk.vtkImageSlice()
gridSlice.SetProperty(gridImageProperty)
gridSlice.SetMapper(gridMapper)

# Add everything to a vtkImageStack
imageStack = vtk.vtkImageStack()
imageStack.AddImage(inputSlice)
imageStack.AddImage(gridSlice)
imageStack.SetActiveLayer(1)

# Create Renderer -> RenderWindow -> RenderWindowInteractor -> InteractorStyle
renderer = vtk.vtkRenderer()
renderer.AddViewProp(imageStack)

renderWindow = vtk.vtkRenderWindow()
renderWindow.AddRenderer(renderer)

interactor = vtk.vtkRenderWindowInteractor()
interactorStyle = vtk.vtkInteractorStyleImage()
interactorStyle.SetInteractionModeToImageSlicing()
interactor.SetInteractorStyle(interactorStyle)
renderWindow.SetInteractor(interactor)

# TODO: Get multislice visualization working.

# Let 'er rip
renderWindow.Render()
interactor.Start()
