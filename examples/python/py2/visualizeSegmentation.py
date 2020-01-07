# History:
#   2017.02.04  babesler@ucalgary.ca    Created
#   2017.04.03  babesler@ucalgary.ca    Updated to overlay inputs
#   2017.04.25  babesler@ucalgary.ca    Setup standard vtkImageStack with threaded visualization
#
# Description:
#   Given two images, visualize the second image ontop of the first
#
# Notes:
#   - See http://www.vtk.org/gitweb?p=VTK.git;a=blob;f=Examples/ImageProcessing/Python/ImageSlicing.py
#       for inspiration in creating the script
#
# Usage:
#   python segmentation.py greyScale segmentation

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
    help='The input NIfTI file'
    )
parser.add_argument(
    'inputSegmentation',
    help='The input NIfTI segmented file'
    )
parser.add_argument('--window',
                    default=float(500), type=float,
                    help='The initial window')
parser.add_argument('--level',
                    default=float(0), type=float,
                    help='The initial level')
parser.add_argument('-n', '--nThreads',
                    default=int(1), type=int,
                    help='Number of threads for each image slice visualizer (default: %(default)s)')
parser.add_argument('-o', '--opacity',
                    default=float(0.25), type=float,
                    help='The opacity of the segmentation between zero and one (default: %(default)s)')
args = parser.parse_args()

# Check that the input (file or directory) exists
for fileName in [args.inputImage,args.inputSegmentation]:
    if not os.path.exists(fileName):
        os.sys.exit('Input \"{inputImage}\" does not exist. Exiting...'.format(inputImage=fileName))

# Check threads
if args.nThreads < 1:
    os.sys.exit('Number of threads must be one or greater. Given {n}. Exiting...'.format(n=args.nThreads))

# Check opacity
if args.opacity > 1 or args.opacity < 0:
    os.sys.exit('Opaicty must be between zeor and one. Given {o}. Exiting...'.format(o=args.opacity))

# Read both images
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

segReader = vtk.vtkImageReader2Factory.CreateImageReader2(args.inputSegmentation)
if segReader is None:
    if args.inputSegmentation.lower().endswith('.nii'):
        segReader = vtk.vtkNIFTIImageReader()
    elif args.inputSegmentation.lower().endswith('.dcm'):
        segReader = vtk.vtkDICOMImageReader()
    elif vtkboneImported and args.inputSegmentation.lower().endswith('.aim'):
        segReader = vtkbone.vtkboneAIMReader()
        segReader.DataOnCellsOff()
    elif vtkbonelabImported and args.inputSegmentation.lower().endswith('.aim'):
        segReader = vtkbonelab.vtkbonelabAIMReader()
        segReader.DataOnCellsOff()
    else:
        os.sys.exit('Unable to find a reader for \"{fileName}\". Exiting...'.format(fileName=args.inputSegmentation))
segReader.SetFileName(args.inputSegmentation)
print('Loading {}...'.format(args.inputSegmentation))
segReader.Update()

# Get data range
scalarRange = [int(x) for x in segReader.GetOutput().GetScalarRange()]
if scalarRange[0] < 0:
    os.sys.exit("Segmentation image \"{}\" has values less than zero which cannot currently be handled. Exiting...".format(args.inputSegmentation))
nLabels = scalarRange[1]
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
inputMapper.SetInputConnection(inputReader.GetOutputPort())
inputMapper.SliceAtFocalPointOn()
inputMapper.SliceFacesCameraOn()
inputMapper.BorderOn()
inputMapper.SetNumberOfThreads(args.nThreads)
inputMapper.ResampleToScreenPixelsOn()
inputMapper.StreamingOn()

imageProperty = vtk.vtkImageProperty()
imageProperty.SetColorLevel(args.level)
imageProperty.SetColorWindow(args.window)
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
segImageProperty.SetOpacity(args.opacity)
segImageProperty.SetLayerNumber(2)
segImageProperty.SetInterpolationTypeToNearest()

segMapper = vtk.vtkImageResliceMapper()
segMapper.SetInputConnection(segReader.GetOutputPort())
segMapper.SliceAtFocalPointOn()
segMapper.SliceFacesCameraOn()
segMapper.BorderOn()
segMapper.SetNumberOfThreads(args.nThreads)
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
    if str(interactor.GetKeyCode()) == '1':
        # Set the first image to the active image (allows W/L)
        imageStack.SetActiveLayer(1)
    elif str(interactor.GetKeyCode()) == '2':
        # Set the second image to the active image (allows W/L)
        imageStack.SetActiveLayer(2)
    elif str(interactor.GetKeyCode()) == 'w':
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

# Add ability to switch between active layers
interactor.AddObserver('KeyPressEvent', layerSwitcher, -1.0) # Call layerSwitcher as last observer

# Initialize and go
interactor.Initialize()
interactor.Start()
