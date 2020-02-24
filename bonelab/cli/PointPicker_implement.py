
"""
Author: Matt Daalder & Bryce Besler
Last edited: Feb 23, 2020

Pick points on a nifti, dicom, or aim file.
This code is optimized for bone.

Takes as input the medical image to read and the directory in which to write the
picked points plain text file.

Example command line/terminal input:
    >>>python PointPicker_implement.py \input\path\image.nii \output\directory\path\

Press 'p' to place a point at the location of your cursor.
Press 'z' to remove a point at the location of your cursor.
Press 't' to write a plaintext file containing the coordintaes of the points picked.

This code takes the medical image, applies a gaussian filter, segments the filtered 
image based on bone CT HU values then renders the surface using marching cubes.
"""

# Imports
import argparse
import os
import vtk

from bonelab.util.echo_arguments import echo_arguments
from bonelab.io.points import write_points
from bonelab.io.vtk_helpers import get_vtk_reader

# =============================================================================
# Takes as argument input file of type nifti, dicom, or aim
# Reads the files, applies a gaussian filter, segments based on bone HU threshold values
# then renders the surface using marching cubes algorithm.
# =============================================================================
def PointPicker(input_filename, output_dir, overwrite=False):

    # Check if output directory exists, if not, exit
    if not os.path.isdir(output_dir):
        os.sys.exit('[ERROR] Cannot find output directory \"{}\" in which to write picked points .txt file'.format(output_dir))
        
    # Read input
    if not os.path.isfile(input_filename):
        os.sys.exit('[ERROR] Cannot find file \"{}\"'.format(input_filename))

    reader = get_vtk_reader(input_filename)
    if reader is None:
        os.sys.exit('[ERROR] Cannot find reader for file \"{}\"'.format(input_filename))

    print('Reading input image ' + input_filename)
    reader.SetFileName(input_filename)
    reader.Update()
    
    # apply filter(s) to images to smooth it out
    filteredImg = vtk.vtkImageGaussianSmooth()
    filteredImg.SetInputConnection(reader.GetOutputPort())
    filteredImg.SetStandardDeviation(1)
    filteredImg.SetRadiusFactors(1,1,1)
    filteredImg.SetDimensionality(3)
    filteredImg.Update()
    
    """ render and display the image """
       
    #set threshold values for segmentation
    loThresh = 200
    hiThresh = 3000
    
    # Threshold the image and segment
    segmentImg = vtk.vtkImageThreshold()
    segmentImg.SetInputData(filteredImg.GetOutput())
    segmentImg.ThresholdBetween(loThresh, hiThresh)
    segmentImg.ReplaceInOn()
    segmentImg.SetInValue(1)
    segmentImg.ReplaceOutOn()
    segmentImg.SetOutValue(0)
    segmentImg.SetOutputScalarTypeToFloat()
    segmentImg.Update()
    
    # initialise 3D marching cubes render
    marchingCubes = vtk.vtkMarchingCubes()
    marchingCubes.SetInputConnection(segmentImg.GetOutputPort())
    marchingCubes.ComputeNormalsOn()
    marchingCubes.SetValue(0, 1.0)

    # # get largest object only (remove noise or unwanted objects)
    # largestObject = vtk.vtkPolyDataConnectivityFilter()
    # largestObject.SetInputConnection(marchingCubes.GetOutputPort())
    # largestObject.SetExtractionModeToLargestRegion()
    # largestObject.ColorRegionsOn()
    # largestObject.Update()
    
    # Filter to smooth the surface
    smoothImg = vtk.vtkSmoothPolyDataFilter()
    smoothImg.SetInputConnection(marchingCubes.GetOutputPort())
    smoothImg.SetNumberOfIterations(5)
    smoothImg.SetRelaxationFactor(0.2)
    smoothImg.FeatureEdgeSmoothingOff()
    smoothImg.BoundarySmoothingOn()
    smoothImg.Update()
    
    # Calculate normals for triangle strips
    normals = vtk.vtkPolyDataNormals()
    normals.SetInputConnection(smoothImg.GetOutputPort())
    normals.ComputePointNormalsOn()
    normals.ComputeCellNormalsOn()
    normals.ConsistencyOn()
    normals.Update()
    
    # create a dict of preset colors (i.e. bone, skin, blood, etc)
    colors = {}
    colors = {'skin':(0.90, 0.76, 0.6), 
              'bone':(0.83, 0.8, 0.81), 
              'red':(0.65, 0.1, 0.1), 
              'green':(0, 0.9, 0.2), 
              'purple':(0.7, 0.61, 0.85)}

    # initialise mapper of opaque 3D image
    mapper3DOpaque = vtk.vtkPolyDataMapper()
    mapper3DOpaque.SetInputConnection(normals.GetOutputPort())
    mapper3DOpaque.ScalarVisibilityOff()

    # initialise the opaque actor
    actor3DOpaque = vtk.vtkActor()
    actor3DOpaque.SetMapper(mapper3DOpaque)
    actor3DOpaque.GetProperty().SetOpacity(1.0)
    actor3DOpaque.GetProperty().SetColor(colors['bone'])

    # create the renderer and add actors
    renderer = vtk.vtkRenderer()
    renderer.AddActor(actor3DOpaque)
    
    # create the render window
    renderWindow = vtk.vtkRenderWindow()
    renderWindow.AddRenderer(renderer)
    renderWindow.SetSize(1000, 1000)
    
    # Connect an interactor to the image viewer
    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(renderWindow)
    interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())

    # =============================================================================
    # Press 'p' to add a point to the display and to the existing points dictionaries
    # Initialised on key press event in the interactor
    # =============================================================================    
    def pickCell(interactor, event):
        
        keyPress = interactor.GetKeySym()
        
        if keyPress == 'p' or keyPress =='P':
            
            # get cursor position when 'p' is pressed
            x, y = interactor.GetEventPosition()
            
            # determine where the cursor is when 'p' is pressed
            cellPicker = vtk.vtkCellPicker()
            cellPicker.PickFromListOn()
            cellPicker.AddPickList(actor3DOpaque)
            cellPicker.SetTolerance(0.0001)
            cellPicker.Pick(x, y, 0, renderer)
            
            points = cellPicker.GetPickedPositions()
            numPoints = points.GetNumberOfPoints()
            if numPoints < 1:
                return()
            i, j, k = points.GetPoint(0)
            
            # create a sphere at the location of the mouse cursor
            sphere = vtk.vtkSphereSource()
            sphere.SetRadius(0.005 * (reader.GetOutput().GetDimensions()[1]))
            res = 20
            sphere.SetThetaResolution(res)
            sphere.SetPhiResolution(res)
            sphere.SetCenter(i, j, k)
            
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(sphere.GetOutputPort())
            
            marker = vtk.vtkActor()
            marker.SetMapper(mapper)
            renderer.AddActor(marker)
            marker.GetProperty().SetColor(1, 0, 0)
            interactor.Render()
            
            # updates the dictionaries where the point coordinates are stored
            if len(pointsDict.keys()) > 0:
                pointNum = max(pointsDict.keys())
            else:
                pointNum = 0
            
            # pointsDict.update({pointNum + 1:[round(i, 2), round(j, 2), round(k, 2)]})
            pointsDict.update({pointNum + 1:[i, j, k]})
            actorDict.update({pointNum + 1:marker})

    # =============================================================================
    # Press 'z' to delete a point from the display and the existing points dictionaries
    # Initialised on key press event in the interactor
    # =============================================================================
    def deleteCell(interactor, event):
        
        keyPress = interactor.GetKeySym()
        
        if keyPress == 'z' or keyPress == 'Z':
            
            # get cursor position when 'z' is pressed
            x, y = interactor.GetEventPosition()
            
            # determine where the cursor is when 'p' is pressed
            cellPicker = vtk.vtkCellPicker()
            cellPicker.PickFromListOn()
            cellPicker.AddPickList(actor3DOpaque)
            cellPicker.SetTolerance(0.00001)
            cellPicker.Pick(x, y, 0, renderer)
            
            points = cellPicker.GetPickedPositions()
            numPoints = points.GetNumberOfPoints()
            if numPoints < 1:
                return()
            i, j, k = points.GetPoint(0)
            
            # determine if there is an existing point close to the cursor position
            for point, posn in pointsDict.items():
                if round(i, 0) == round(posn[0], 0) or ( round(i, 0)-1 ) == round(posn[0], 0) or ( round(i, 0)+1 ) == round(posn[0], 0):
                    if round(j, 0) == round(posn[1], 0) or ( round(j, 0)-1 ) == round(posn[1], 0) or ( round(j, 0)+1 ) == round(posn[1], 0):
                        
                        keyPoint = point
                        
                        # remove the displayed sphere, and remove the point from the point dictionary
                        try:    
                            renderer.RemoveActor(actorDict[keyPoint])
                            interactor.Render()
                            
                            del pointsDict[keyPoint]
                            del actorDict[keyPoint]
                            
                            print("Deleted point #: ", keyPoint)
                            print("Number of points remaining: ", str(len(pointsDict.keys())) )
                            
                        except KeyError:
                            print("No point found at these coordinates")
                            
    # =============================================================================
    # Use in future to display pertinent information, or create a GUI??
    # Image info, cursor position, existing points and their coordinates?
    # =============================================================================
    #                            
    # def textDisplay():
    #     None
    
    # return()
    
    # =============================================================================
    # Press 't' to write a .txt file of the points picked and displayed in the image window 
    # Currently point coordinate precision is set to 4 decimal points (arbitrary)
    # =============================================================================
    def printPoints(interactor, event):
        
        precision = 4
        keyPress = interactor.GetKeySym()
        
        if keyPress == 't':
            
            # ask user for .txt filename
            result = input('Please name the point coordinates file to be stored in \"{}\" as .txt filetype. \n'.format(output_dir))
            output_filename = str(output_dir) + str(result) + '.txt'

            # Check if output exists and should overwrite
            if os.path.isfile(output_filename) and not overwrite:
                result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_filename))
                if result.lower() not in ['y', 'yes']:
                    print('Not overwriting. Please try again, or exit the program.')
                    return()
                
            print('Points to be printed in ' + output_filename + ':')
            for point, coords in pointsDict.items():
                print(point,':' , coords)
            
            write_points(pointsDict.values(), output_filename, ',', precision)
        
    # dictionaries to keep track of picked points coordinates and respective actors    
    pointsDict = {}
    actorDict = {}
    
    # press 'p' to add a point, or 'z' to remove a point
    interactor.AddObserver('KeyPressEvent', pickCell)
    interactor.AddObserver('KeyPressEvent', deleteCell)
    interactor.AddObserver('KeyPressEvent', printPoints)
    
    # initialise the interactor
    interactor.Initialize()
    
    # render the scene with all actors in it
    renderWindow.Render()
    
    # Start the event loop for the interactor
    interactor.Start()

    

def main():
    # Setup description
    description='''Pick points on an image

    This function allows one to pick points on an image. Points are written to a plain
    text file for use in other programs
    '''

    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blPointPicker",
        description=description
    )
    parser.add_argument('input_filename', help='Input image file')
    parser.add_argument('output_dir', help='Output directory in which to print plain text file listing the picked points')
    parser.add_argument('-o', '--overwrite', action='store_true', help='Overwrite output without asking')

    # Parse and display
    args = parser.parse_args()
    print(echo_arguments('PointPicker', vars(args)))

    # Run program
    PointPicker(**vars(args))

if __name__ == '__main__':
    main()
