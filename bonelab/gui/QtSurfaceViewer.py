# History:
#   03 JUL 2020 skboyd@ucalgary.ca  Created
#
# Description:
#   GUI-based 3D rendering tool. Used to estimate 3D registration transforms.
#
# Notes:
#   - Based on 'marchingCubes.py' written by Bryce Besler, 07 FEB 2017
#   - Updated to use PyQt5, vtk8.2 and python3:
#     pyqt                      5.12.3           py38hf180056_3    conda-forge
#     vtk                       8.2.0           py38h19d254c_206    conda-forge
#     python                    3.8.1                h5c2c468_1    conda-forge
#   Try something like this:
#     conda create -n bl -c numerics88 -c conda-forge python=3.8 n88tools pyqt=5 vtk=8
#
#   - Download QtDesigner to edit the .ui file
#     https://build-system.fman.io/qt-designer-download
#   - Some useful references:
#     http://www.vtk.org/Wiki/VTK/Examples/Python/Widgets/EmbedPyQt
#     http://stackoverflow.com/questions/18897695/pyqt4-difference-between-qwidget-and-qmainwindow
#
#   - To convert a .ui file to .py do the following
#     pyuic5 -x QtSurfaceViewer.ui -o widget.py
#   - The save tiff button is not fully worked out.
#
# Usage:
#   python blQtSurfaceViewer

# Imports
import os
import math
import vtk
from bonelab.util.time_stamp import message
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
try:
    from PyQt5 import QtCore, QtGui, QtWidgets, uic
except ImportError:
    try:
        from PySide2 import QtCore, QtGui, QtWidgets, uic
    except ImportError:
        raise ImportError("Cannot load either PyQt5 or PySide2")

Ui_MainWindow, QtBaseClass = uic.loadUiType("QtSurfaceViewer.ui")
pointsDict = {}
actorDict = {}

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, 
                 min_size=(640, 640),
                 *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.initUI(min_size)

    def initUI(self,min_size):
        self.setWindowTitle('Bone Imaging Laboratory - Surface Viewer')
        self.centralWidget = VisualizationWindow()
        #self.setCentralWidget(self.centralWidget) # If I uncomment this the GUI placement is messed up...
        
        self.setMinimumSize(QtCore.QSize(*min_size))
        
        self.resize(1641, 1005)
        self.center_on_screen()
        
        # Tool bar
        self.createToolBar()

        # Status bar
        self.status = self.statusBar()
        self.status.showMessage("Load data")
        
    def createToolBar(self):
        self.saveAction = QtWidgets.QAction(QtGui.QIcon.fromTheme('save'), 'Save', self)
        self.exitAction = QtWidgets.QAction(QtGui.QIcon.fromTheme('exit'), 'Exit', self)
        
        self.fileToolBar = self.addToolBar("ToolBar")
        self.fileToolBar.addAction(self.exitAction)
        self.fileToolBar.addAction(self.saveAction)
        
        self.exitAction.triggered.connect(self.exitButtonClicked)
        self.saveAction.triggered.connect(self.saveButtonClicked)
                
    def center_on_screen(self):
        qr = self.frameGeometry()
        cp = QtWidgets.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def exitButtonClicked(self):
        self.status.showMessage("Exit the program?")
        self.close()
            
    def saveButtonClicked(self):
        self.saveFile, filter = QtWidgets.QFileDialog.getSaveFileName()
        print(self.saveFile)

        if os.path.exists(self.saveFile):
            reply = QtWidgets.QMessageBox.question(self, 'Message',
            "File exists. Overwrite?", QtWidgets.QMessageBox.Yes |
            QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        
            if reply == QtWidgets.QMessageBox.No:
                self.saveFile = None
                return
        
        # Do it. Save!
        print('hey, this needs to be implemented.')

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self, 'Message',
            "Are you sure you want to quit?", QtWidgets.QMessageBox.Yes |
            QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.Yes)

        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
        else:
            self.status.showMessage("Ready")
            event.ignore()

class VisualizationWindow(QtWidgets.QMainWindow):
    def __init__(self, parent = None):
        super(VisualizationWindow, self).__init__()

        self.initUI()
        self.setupImageProcessingPipeline()
        
    def initUI(self):
        # Use UI file to define User Interface
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Setup QVTKRenderWindowInteractor
        self.vtkFrame = self.ui.vtkFrame
        self.menu = self.ui.gridLayoutWidget
        self.vtkLayout = QtWidgets.QVBoxLayout()
        self.vtkWidget = QVTKRenderWindowInteractor(self.vtkFrame)
        self.vtkLayout.addWidget(self.vtkWidget)
        #self.vtkLayout.addWidget(self.menu)
        self.vtkFrame.setLayout(self.vtkLayout)

        # Adjust sizing; override the .ui
        self.vtkFrame.resize(1024,1024)
        self.menu.setGeometry(1044,24,271,201)
        
        # Define signal-slot connections
        self.ui.loadButton.clicked.connect(self.loadButtonClicked)
        self.ui.saveButton.clicked.connect(self.saveButtonClicked)
        self.ui.resampleSpinBox.valueChanged.connect(self.resampleSpinBoxChanged)
        self.ui.gaussSigmaSpinBox.valueChanged.connect(self.gaussSigmaSpinBoxChanged)
        self.ui.gaussRadiusSpinBox.valueChanged.connect(self.gaussRadiusSpinBoxChanged)

        # Create renderer/interactor
        self.ren = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.style = vtk.vtkInteractorStyleTrackballCamera()
        self.iren.SetInteractorStyle(self.style)
        self.iren.AddObserver(vtk.vtkCommand.KeyPressEvent, self.keypress, 1.0)

        # Initialize
        self.show()
        self.iren.Initialize()

    def printMatrix4x4(self, m):
        precision = 4
        delimiter=','
        formatter = '{{:8.{}f}}'.format(precision)
            
        for i in range(4):
          row_data = delimiter.join([formatter.format(float(m.GetElement(i,j))) for j in range(4)])
          print('[ '+row_data+' ]')
    
    def print_points_to_screen(self,points,delimiter,precision):
        formatter = '{{:8.{}f}}'.format(precision)
        print('|-------------------------')
        for point in points:
          entry = delimiter.join([formatter.format(float(x)) for x in point])
          #entry += os.linesep
          print(entry)
        print('|-------------------------')

    def writeTransform(self,output_file,matrix,check_for_overwrite=True):
        if os.path.isfile(output_file) and check_for_overwrite:
          result = input('File \"{}\" already exists. Overwrite? [y/n]: '.format(output_file))
          if result.lower() not in ['y', 'yes']:
            print('Not overwriting. Exiting...')
            self.printMatrix4x4(matrix)
            os.sys.exit()
        
        precision = 7
        delimiter=' '
        formatter = '{{:14.{}e}}'.format(precision)
        
        with open(output_file, 'w') as fp:
          fp.write('SCANCO TRANSFORMATION DATA VERSION:   10\n')
          fp.write('R4_MAT:\n')
          for i in range(4):
            row_data = delimiter.join([formatter.format(float(matrix.GetElement(i,j))) for j in range(4)])
            fp.write(row_data+'\n')

    def keypress(self, obj, event):
        interactor = obj
        renderer = interactor.GetRenderWindow().GetRenderers().GetFirstRenderer()
        actorCollection = renderer.GetActors()
        actorCollection.InitTraversal()
    
        key = obj.GetKeySym()

        if key in 'h':
          print('Press the \'u\' key to output actor transform matrix')
          print('Press the \'p\' key to pick a point')
          print('Press the \'d\' key to delete a point')
          print('Press the \'o\' key to output points')
          print('Press the \'a\' key for actor control mode')
          print('Press the \'c\' key for camera control mode')
          print('Press the \'q\' key to quit')

        if key in 'u':
         for index in range(actorCollection.GetNumberOfItems()):
           nextActor = actorCollection.GetNextActor()
           if (nextActor.GetPickable()==1):
             self.printMatrix4x4(nextActor.GetMatrix())
             message('File written: transform.txt')
             # output filename shouldn't be hard coded. Should use a file dialog.
             self.writeTransform('transform.txt',nextActor.GetMatrix(),False)
             
        if key in 'p':
          x, y = obj.GetEventPosition()
      
          cellPicker = vtk.vtkCellPicker()
          cellPicker.SetTolerance(0.0001)
          cellPicker.Pick(x, y, 0, renderer)
      
          points = cellPicker.GetPickedPositions()
          numPoints = points.GetNumberOfPoints()
          if numPoints < 1:
            return()
          i, j, k = points.GetPoint(0)
          
      
          # Get the size of the actor by measuring its diagonal
          b = actorCollection.GetNextActor().GetBounds()
          sphere_size = math.sqrt(math.pow((b[1]-b[0]),2)+
                                  math.pow((b[3]-b[2]),2)+
                                  math.pow((b[5]-b[4]),2)) * 0.005
          
          sphere = vtk.vtkSphereSource()
          sphere.SetRadius(sphere_size)
          sphere.SetThetaResolution(20)
          sphere.SetPhiResolution(20)
          sphere.SetCenter(i, j, k)
          
          mapper = vtk.vtkPolyDataMapper()
          mapper.SetInputConnection(sphere.GetOutputPort())
          
          marker = vtk.vtkActor()
          marker.SetMapper(mapper)
          renderer.AddActor(marker)
          marker.GetProperty().SetColor(1, 0, 0)
          marker.PickableOff()
          interactor.Render()
          
          # updates the dictionaries where the point coordinates are stored
          if len(pointsDict.keys()) > 0:
              pointNum = max(pointsDict.keys())
          else:
              pointNum = 0
          
          pointsDict.update({pointNum + 1:[i, j, k]})
          actorDict.update({pointNum + 1:marker})
          
          self.print_points_to_screen(pointsDict.values(),',',4)
    
        if key in 'd':
          x, y = interactor.GetEventPosition()
          
          cellPicker = vtk.vtkCellPicker()
          cellPicker.SetTolerance(0.00001)
          cellPicker.Pick(x, y, 0, renderer)
          
          points = cellPicker.GetPickedPositions()
          numPoints = points.GetNumberOfPoints()
          if numPoints < 1:
            return()
          i, j, k = points.GetPoint(0)
          
          min_distance_to_point = 1e12
          for point, posn in pointsDict.items():
            distance_to_point = math.sqrt(math.pow((posn[0]-i),2)+
                                          math.pow((posn[1]-j),2)+
                                          math.pow((posn[2]-k),2))
            if (distance_to_point < min_distance_to_point):
              min_distance_to_point = distance_to_point
              keyPoint = point
          
          try:    
             renderer.RemoveActor(actorDict[keyPoint])
             interactor.Render()
             
             del pointsDict[keyPoint]
             del actorDict[keyPoint]
             
             print("Deleted point #: ", keyPoint)
             print("Number of points remaining: ", str(len(pointsDict.keys())) )
             
          except KeyError:
             print("No point found at these coordinates")
             
          self.print_points_to_screen(pointsDict.values(),',',4)
    
        if key in 'o':
          # This shouldn't be hard coded. It should use a file dialog
          output_file = "points.txt"
          
          precision = 4
          delimiter=','
          formatter = '{{:8.{}f}}'.format(precision)
          
          with open(output_file, 'w') as fp:
              for point in pointsDict.values():
                  entry = delimiter.join([formatter.format(float(x)) for x in point])
                  entry += os.linesep
                  fp.write(entry)
          
          message('Wrote output file ',output_file)
    
        
    def setupImageProcessingPipeline(self):
        # Gaussian Smooth the image first
        # http://www.vtk.org/doc/nightly/html/classvtkImageGaussianSmooth.html
        self.noiseFilter = vtk.vtkImageGaussianSmooth()
        self.noiseFilter.SetStandardDeviation(1, 1, 1)
        self.noiseFilter.SetRadiusFactors(10, 10, 10)

        # Image Resize for resampler
        # http://www.vtk.org/doc/nightly/html/classvtkImageResize.html
        self.resampler = vtk.vtkImageResize()
        self.resampler.SetResizeMethodToMagnificationFactors()
        self.resampler.SetMagnificationFactors(1,1,1)
        self.resampler.BorderOn()
        self.resampler.SetInputConnection(self.noiseFilter.GetOutputPort())

        # Marching cubes for iso value
        # http://www.vtk.org/doc/nightly/html/classvtkImageMarchingCubes.html
        self.marchingCubes = vtk.vtkImageMarchingCubes()
        self.marchingCubes.SetInputConnection(self.resampler.GetOutputPort())
        self.marchingCubes.ComputeGradientsOn()
        self.marchingCubes.ComputeNormalsOn()
        self.marchingCubes.ComputeScalarsOn()
        self.marchingCubes.SetNumberOfContours(1)
        self.marchingCubes.SetValue(0, 0)

        # Create mapper and actor for renderer
        self.mapper = vtk.vtkPolyDataMapper()
        self.mapper.SetInputConnection(self.marchingCubes.GetOutputPort())
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(self.mapper)
        self.actor.GetProperty().SetInterpolationToGouraud()

    # Define slots
    def loadButtonClicked(self):
        reply = QtWidgets.QMessageBox.question(self, 'Message',
            "Are you loading a file? The alternative is a directory",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.Yes)

        if reply == QtWidgets.QMessageBox.Yes:
            # Ask use for input file
            self.inputFileName, filters = QtWidgets.QFileDialog.getOpenFileName(self,self.tr("Open Image"),"",self.tr("Image Files (*.nii)"))
        else:
            # Ask use for input directory
            self.inputFileName, filters = str(QtWidgets.QFileDialog.getExistingDirectory())

        if os.path.exists(self.inputFileName):
            self.readInputFile()
            if self.reader is not None:
                self.connectReader()
                self.updateUI()
        else:
            self.inputFileName = None

    def readInputFile(self):
        # Read the file
        print(self.inputFileName)
        if os.path.isdir(self.inputFileName): # DICOM dir
            self.reader = vtk.vtkDICOMImageReader()
            self.reader.SetDirectoryName(self.inputFileName)
            #print("DICOM dir")
        elif self.inputFileName.lower().endswith('.nii'): # NIfTI file
            self.reader = vtk.vtkNIFTIImageReader()
            self.reader.SetFileName(self.inputFileName)
            #print("NIfTI file")
        elif self.inputFileName.lower().endswith(('.dicom', '.dcm')): # DICOM file
            self.reader = vtk.vtkDICOMImageReader()
            self.reader.SetFileName(self.inputFileName)
            #print("DICOM file")
        else: # Not recognized
            self.inputFileName = None
            self.reader = None
            return
        self.reader.Update()

    def connectReader(self):
        # Connect the reader to the filter
        self.noiseFilter.SetInputConnection(self.reader.GetOutputPort())

        # Put it all together
        self.ren.AddActor(self.actor)
        self.ren.ResetCamera()
        self.ren.Render()

    def updateUI(self):
        # Enable resample spin box
        self.ui.resampleSpinBox.setEnabled(True)
        self.ui.resampleSpinBox.setValue(1)

        # Enable resample spin box
        self.ui.gaussSigmaSpinBox.setEnabled(True)
        self.ui.gaussSigmaSpinBox.setValue(1)

        # Enable resample spin box
        self.ui.gaussRadiusSpinBox.setEnabled(True)
        self.ui.gaussRadiusSpinBox.setValue(10)

        # Set contour value
        scalarRange = self.reader.GetOutput().GetScalarRange()
        self.ui.contourSlider.setEnabled(True)
        self.ui.contourSlider.setMinimum(int(scalarRange[0]))
        self.ui.contourSlider.setMaximum(int(scalarRange[1]))
        self.ui.contourSlider.setValue(int(scalarRange[0]))

    def contourSliderChanged(self, value):
        self.marchingCubes.SetValue(0, value)
        self.contourSliderLabel.setText(self.tr('Iso Value = {}'.format(value)))
        #self.vtkWidget.Render()

    def saveButtonClicked(self):
        self.saveFile = str(QtWidgets.QFileDialog.getSaveFileName())
        print(self.saveFile)

        if os.path.exists(self.inputFileName):
            reply = QtWidgets.QMessageBox.question(self, 'Message',
            "File exists. Overwrite?", QtWidgets.QMessageBox.Yes |
            QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

            if reply == QtWidgets.QMessageBox.No:
                self.saveFile = None
                return

        # Do it, write it out!
        windowToImage = vtk.vtkWindowToImageFilter()
        windowToImage.SetInput(self.vtkWidget.GetRenderWindow())
        windowToImage.Update()

        writer = vtk.vtkTIFFWriter()
        writer.SetCompressionToNoCompression()
        writer.SetFileName(self.saveFile)
        writer.SetInputConnection(windowToImage.GetOutputPort())
        writer.Write()

    def resampleSpinBoxChanged(self, value):
        if (value > 0) and (value < 2):
            self.resampler.SetMagnificationFactors(value, value, value)
            #self.marchingCubes.SetUpdateExtentToWholeExtent() # DO NOT REMOVE!
            self.marchingCubes.UpdateWholeExtent()

    def gaussSigmaSpinBoxChanged(self, value):
        if value > 0:
            self.noiseFilter.SetStandardDeviation(value, value, value)
            #self.marchingCubes.SetUpdateExtentToWholeExtent() # DO NOT REMOVE!
            self.marchingCubes.UpdateWholeExtent()

    def gaussRadiusSpinBoxChanged(self, value):
        if value > 0:
            self.noiseFilter.SetRadiusFactors(value, value, value)
            #self.marchingCubes.SetUpdateExtentToWholeExtent() # DO NOT REMOVE!
            self.marchingCubes.UpdateWholeExtent()

def ArgumentManager():
    import argparse
    description='''
A utility for viewing image data and determining rotations.
'''
    epilog='''
Example calls could be:
$ blQtSurfaceViewer
$ blQtSurfaceViewer --min_size 1000 1000
'''
    # Setup argument parsing
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        prog="blQtSurfaceViewer",
        description=description,
        epilog=epilog
    )
    parser.add_argument('--min_size', default=[640, 480], nargs=2, type=int, metavar='DIM', help='Specify minimum window size (default: %(default)s)')
    return parser.parse_args()

def main():
    # Parse arguments
    args = ArgumentManager()

    app = QtWidgets.QApplication([])
    window = MainWindow(**vars(args))
    window.show()
    os.sys.exit(app.exec_())

if __name__ == '__main__':
    main()
