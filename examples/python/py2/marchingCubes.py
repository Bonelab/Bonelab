# History:
#   2017.02.07  babesler@ucalgary.ca    Created
#
# Description:
#   Render a volume using marching cubes
#
# Notes:
#   - See http://www.vtk.org/Wiki/VTK/Examples/Python/Widgets/EmbedPyQt
#   - http://stackoverflow.com/questions/18897695/pyqt4-difference-between-qwidget-and-qmainwindow
#   - The save tiff button is not fully worked out.
#
# Usage:
#   python marchingCube.py

# Imports
import os
import math
import vtk
from vtk.qt4.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
try:
    from PyQt4 import QtCore, QtGui
    #print "PyQt4"
except ImportError:
    try:
        from PySide import QtCore, QtGui
        #print "PySide"
    except ImportError:
        raise ImportError("Cannot load either PyQt or PySide")

class MainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.initUI()

    def initUI(self):
        self.setWindowTitle('Marching Cubes')
        self.centralWidget = MarchingCubesVisualize()
        self.setCentralWidget(self.centralWidget)

        self.resize(800, 600)
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def closeEvent(self, event):
        reply = QtGui.QMessageBox.question(self, 'Message',
            "Are you sure to quit?", QtGui.QMessageBox.Yes |
            QtGui.QMessageBox.No, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

class MarchingCubesVisualize(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(MarchingCubesVisualize, self).__init__()

        self.initUI()
        self.setupImageProcessingPipeline()

    def initUI(self):
        # Setup QVTKRenderWindowInteractor
        self.vtkFrame = QtGui.QFrame()
        self.vtkLayout = QtGui.QVBoxLayout()
        self.vtkWidget = QVTKRenderWindowInteractor(self.vtkFrame)
        self.vtkLayout.addWidget(self.vtkWidget)
        self.vtkFrame.setLayout(self.vtkLayout)

        # Create the user input layout
        self.loadButton = QtGui.QPushButton(self.tr("&Load Data"))
        QtCore.QObject.connect(self.loadButton, QtCore.SIGNAL('clicked()'), self.loadButtonClicked)
        self.saveButton = QtGui.QPushButton(self.tr("&Save Screenshot"))
        QtCore.QObject.connect(self.saveButton, QtCore.SIGNAL('clicked()'), self.saveButtonClicked)

        self.resampleSpinBox = QtGui.QDoubleSpinBox()
        QtCore.QObject.connect(self.resampleSpinBox, QtCore.SIGNAL('valueChanged(double)'), self.resampleSpinBoxChanged)
        self.resampleSpinBox.setDisabled(True)
        self.resampleSpinBox.setMinimum(0)
        self.resampleSpinBox.setMaximum(2)
        self.resampleSpinBoxLabel = QtGui.QLabel(self.tr('Resample factor (< 1 reduce)'))

        self.gaussSigmaSpinBox = QtGui.QDoubleSpinBox()
        QtCore.QObject.connect(self.gaussSigmaSpinBox, QtCore.SIGNAL('valueChanged(double)'), self.gaussSigmaSpinBoxChanged)
        self.gaussSigmaSpinBox.setDisabled(True)
        self.gaussSigmaSpinBox.setMinimum(0)
        self.gaussSigmaSpinBoxLabel = QtGui.QLabel(self.tr('Gaussian Sigma'))

        self.gaussRadiusSpinBox = QtGui.QDoubleSpinBox()
        QtCore.QObject.connect(self.gaussRadiusSpinBox, QtCore.SIGNAL('valueChanged(double)'), self.gaussRadiusSpinBoxChanged)
        self.gaussRadiusSpinBox.setDisabled(True)
        self.gaussRadiusSpinBox.setMinimum(0)
        self.gaussRadiusSpinBoxLabel = QtGui.QLabel(self.tr('Gaussian Radius'))

        self.contourSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
        QtCore.QObject.connect(self.contourSlider, QtCore.SIGNAL('valueChanged(int)'), self.contourSliderChanged)
        self.contourSlider.setDisabled(True)
        self.contourSliderLabel = QtGui.QLabel(self.tr('Iso Value'))

        self.userInputLayout = QtGui.QGridLayout()
        self.userInputLayout.addWidget(self.loadButton, 0, 0)
        self.userInputLayout.addWidget(self.saveButton, 0, 1)
        self.userInputLayout.addWidget(self.gaussSigmaSpinBoxLabel, 1, 0)
        self.userInputLayout.addWidget(self.gaussSigmaSpinBox, 1, 1)
        self.userInputLayout.addWidget(self.gaussRadiusSpinBoxLabel, 2, 0)
        self.userInputLayout.addWidget(self.gaussRadiusSpinBox, 2, 1)
        self.userInputLayout.addWidget(self.contourSliderLabel, 3, 0)
        self.userInputLayout.addWidget(self.contourSlider, 3, 1)
        self.userInputLayout.addWidget(self.resampleSpinBoxLabel, 4, 0)
        self.userInputLayout.addWidget(self.resampleSpinBox, 4, 1)

        # Combine all widgets together
        self.layout = QtGui.QHBoxLayout()
        self.layout.addWidget(self.vtkFrame)
        self.layout.addLayout(self.userInputLayout)
        self.centralWidget = QtGui.QWidget()
        self.centralWidget.setLayout(self.layout)

        # Set central widget
        self.setCentralWidget(self.centralWidget)

        # Create renderer/interactor
        self.ren = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.style = vtk.vtkInteractorStyleTrackballCamera()
        self.iren.SetInteractorStyle(self.style)

        # Initialize
        self.show()
        self.iren.Initialize()

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

    def loadButtonClicked(self):
        reply = QtGui.QMessageBox.question(self, 'Message',
            "Are you loading a file? The alternative is a directory",
            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            # Ask use for input file
            self.inputFileName = str(QtGui.QFileDialog.getOpenFileName())
        else:
            # Ask use for input directory
            self.inputFileName = str(QtGui.QFileDialog.getExistingDirectory())

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
        self.resampleSpinBox.setEnabled(True)
        self.resampleSpinBox.setValue(1)

        # Enable resample spin box
        self.gaussSigmaSpinBox.setEnabled(True)
        self.gaussSigmaSpinBox.setValue(1)

        # Enable resample spin box
        self.gaussRadiusSpinBox.setEnabled(True)
        self.gaussRadiusSpinBox.setValue(10)

        # Set contour value
        scalarRange = self.reader.GetOutput().GetScalarRange()
        self.contourSlider.setEnabled(True)
        self.contourSlider.setMinimum(scalarRange[0])
        self.contourSlider.setMaximum(scalarRange[1])
        self.contourSlider.setValue(scalarRange[0])

    def contourSliderChanged(self, value):
        self.marchingCubes.SetValue(0, value)
        self.contourSliderLabel.setText(self.tr('Iso Value = {}'.format(value)))
        #self.vtkWidget.Render()

    def saveButtonClicked(self):
        self.saveFile = str(QtGui.QFileDialog.getSaveFileName())
        print(self.saveFile)

        if os.path.exists(self.inputFileName):
            reply = QtGui.QMessageBox.question(self, 'Message',
            "File exists. Overwrite?", QtGui.QMessageBox.Yes |
            QtGui.QMessageBox.No, QtGui.QMessageBox.No)

            if reply == QtGui.QMessageBox.No:
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
            self.marchingCubes.SetUpdateExtentToWholeExtent() # DO NOT REMOVE!

    def gaussSigmaSpinBoxChanged(self, value):
        if value > 0:
            self.noiseFilter.SetStandardDeviation(value, value, value)
            self.marchingCubes.SetUpdateExtentToWholeExtent() # DO NOT REMOVE!

    def gaussRadiusSpinBoxChanged(self, value):
        if value > 0:
            self.noiseFilter.SetRadiusFactors(value, value, value)
            self.marchingCubes.SetUpdateExtentToWholeExtent() # DO NOT REMOVE!

def main():
    app = QtGui.QApplication(os.sys.argv)
    window = MainWindow()
    window.show()
    os.sys.exit(app.exec_())

if __name__ == '__main__':
    main()
