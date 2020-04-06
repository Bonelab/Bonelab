# History:
#   2017.02.07  babesler@ucalgary.ca    Created
#
# Description:
#   Direct volume rendering
#
# Notes:
#   - See http://www.vtk.org/gitweb?p=VTK.git;a=blob;f=Examples/Medical/Python/Medical4.py
#       and http://www.vtk.org/gitweb?p=VTK.git;a=blob;f=Examples/GUI/Python/ImageTracerWidget.py
#   - The osirix server was down so I didn't get to try other data. Their data
#       probably has better contrast and can be rendered really smoothly.
#
# Usage:
#   python volumeRendering.py

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
        self.setWindowTitle('Direct Volume Rendering')
        self.centralWidget = DirectVolumeRendering()
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

class DirectVolumeRendering(QtGui.QMainWindow):
    def __init__(self, parent = None):
        super(DirectVolumeRendering, self).__init__()

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

        self.ambientSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.ambientSlider.setDisabled(True)
        self.ambientSlider.setMinimum(0)
        self.ambientSlider.setMaximum(1000)
        self.ambientSlider.setValue(400)
        QtCore.QObject.connect(self.ambientSlider, QtCore.SIGNAL('valueChanged(int)'), self.ambientSliderChanged)
        self.ambientSliderLabel = QtGui.QLabel(self.tr('Ambient'))

        self.diffuseSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.diffuseSlider.setDisabled(True)
        self.diffuseSlider.setMinimum(0)
        self.diffuseSlider.setMaximum(1000)
        self.diffuseSlider.setValue(600)
        QtCore.QObject.connect(self.diffuseSlider, QtCore.SIGNAL('valueChanged(int)'), self.diffuseSliderChanged)
        self.diffuseSliderLabel = QtGui.QLabel(self.tr('Diffuse'))

        self.specularSlider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.specularSlider.setDisabled(True)
        self.specularSlider.setMinimum(0)
        self.specularSlider.setMaximum(1000)
        self.specularSlider.setValue(200)
        QtCore.QObject.connect(self.specularSlider, QtCore.SIGNAL('valueChanged(int)'), self.specularSliderChanged)
        self.specularSliderLabel = QtGui.QLabel(self.tr('Specular'))

        self.tfComboBox = QtGui.QComboBox()
        self.tfComboBox.addItem('head')
        self.tfComboBox.addItem('head2')
        self.tfComboBox.addItem('Thorax')
        self.tfComboBox.addItem('Hip')
        QtCore.QObject.connect(self.tfComboBox, QtCore.SIGNAL('currentIndexChanged(QString)'), self.tfComboBoxChanged)

        self.userInputLayout = QtGui.QGridLayout()
        self.userInputLayout.addWidget(self.loadButton, 0, 0)
        self.userInputLayout.addWidget(self.saveButton, 0, 1)
        self.userInputLayout.addWidget(self.ambientSliderLabel, 1, 0)
        self.userInputLayout.addWidget(self.ambientSlider, 1, 1)
        self.userInputLayout.addWidget(self.diffuseSliderLabel, 2, 0)
        self.userInputLayout.addWidget(self.diffuseSlider, 2, 1)
        self.userInputLayout.addWidget(self.specularSliderLabel, 3, 0)
        self.userInputLayout.addWidget(self.specularSlider, 3, 1)
        self.userInputLayout.addWidget(self.tfComboBox, 4, 0, 1, 2)

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
        # Caster
        self.caster = vtk.vtkImageShiftScale()
        self.caster.SetOutputScalarTypeToUnsignedChar()
        self.caster.ClampOverflowOn()

        # Setup composite ray cast function
        self.rayCastFunction = vtk.vtkVolumeRayCastCompositeFunction()

        # Add to mapper
        self.volumeMapper = vtk.vtkVolumeRayCastMapper()
        self.volumeMapper.SetInputConnection(self.caster.GetOutputPort())
        self.volumeMapper.SetVolumeRayCastFunction(self.rayCastFunction)

        # The color transfer function maps voxel intensities to colors.
        self.volumeColor = vtk.vtkColorTransferFunction()
        self.volumeColor.AddRGBPoint(0,    0.0, 0.0, 0.0)
        self.volumeColor.AddRGBPoint(255,  1.0, 1.0, 1.0)

        # The opacity transfer function (tissue opacity)
        self.volumeScalarOpacity = vtk.vtkPiecewiseFunction()
        self.volumeScalarOpacity.AddPoint(0,    0.00)
        self.volumeScalarOpacity.AddPoint(255,  1)

        # The gradient opacity function (decrease opacity in flat regions)
        self.volumeGradientOpacity = vtk.vtkPiecewiseFunction()
        self.volumeGradientOpacity.AddPoint(0,   0.0)
        self.volumeGradientOpacity.AddPoint(90,  0.5)
        self.volumeGradientOpacity.AddPoint(100, 1.0)

        # Property
        self.volumeProperty = vtk.vtkVolumeProperty()
        self.volumeProperty.SetColor(self.volumeColor)
        self.volumeProperty.SetScalarOpacity(self.volumeScalarOpacity)
        self.volumeProperty.SetGradientOpacity(self.volumeGradientOpacity)
        self.volumeProperty.SetInterpolationTypeToLinear()
        self.volumeProperty.ShadeOn()
        self.volumeProperty.SetAmbient(1)
        self.volumeProperty.SetDiffuse(1)
        self.volumeProperty.SetSpecular(0.2)

        # Prop
        self.volume = vtk.vtkVolume()
        self.volume.SetMapper(self.volumeMapper)
        self.volume.SetProperty(self.volumeProperty)

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
        # Determine rescale range
        self.reader.Update()
        srange = self.reader.GetOutput().GetScalarRange()
        minRange = srange[0]
        maxRange = srange[1]

        diff = maxRange-minRange
        self.slope = 255.0/diff
        inter = -self.slope*minRange
        self.shift = inter/self.slope
        print('tf = {} * (x + {})'.format(self.slope, self.shift))

        # Connect the reader to the filter
        self.caster.SetInputConnection(self.reader.GetOutputPort())
        self.caster.SetShift(self.shift)
        self.caster.SetScale(self.slope)
        self.caster.Update()
        print('New scalar range: {}'.format(self.caster.GetOutput().GetScalarRange()))


        # Put it all together
        self.ren.AddViewProp(self.volume)
        self.ren.ResetCamera()
        self.ren.Render()

    def updateUI(self):
        # Enable resample spin box
        self.ambientSlider.setEnabled(True)
        self.ambientSlider.setValue(1000)

        self.diffuseSlider.setEnabled(True)
        self.diffuseSlider.setValue(1000)

        self.specularSlider.setEnabled(True)
        self.specularSlider.setValue(200)

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

    def ambientSliderChanged(self, value):
        self.volumeProperty.SetAmbient(value/1000.0)

    def diffuseSliderChanged(self, value):
        self.volumeProperty.SetDiffuse(value/1000.0)

    def specularSliderChanged(self, value):
        self.volumeProperty.SetSpecular(value/1000.0)

    def tfComboBoxChanged(self, value):
        value = str(value)
        if value.lower() == 'head':
            self.setHeadTF()
        if value.lower() == 'head2':
            self.setHead2TF()
        if value.lower() == 'thorax':
            self.setThoraxTF()
        if value.lower() == 'hip':
            self.setHipTF()

    def tf(self, value):
        return self.slope * (value + self.shift)

    def setHeadTF(self):
        # The color transfer function maps voxel intensities to colors.
        self.volumeColor.RemoveAllPoints()
        self.volumeColor.AddRGBPoint(self.tf(99), 0.0, 0.0, 0.0)
        self.volumeColor.AddRGBPoint(self.tf(100), 1.0, 0.88, 0.74)
        self.volumeColor.AddRGBPoint(self.tf(450), 1.0, 0.88, 0.74)
        self.volumeColor.AddRGBPoint(self.tf(451), 1.0, 0.88, 0.74)
        self.volumeColor.AddRGBPoint(self.tf(799), 1.0, 0.88, 0.74)
        self.volumeColor.AddRGBPoint(self.tf(800), 1.0, 1.0, 0.9)

        # The opacity transfer function (tissue opacity)
        self.volumeScalarOpacity.RemoveAllPoints()
        self.volumeScalarOpacity.AddPoint(self.tf(99),  0.0)
        self.volumeScalarOpacity.AddPoint(self.tf(100), 0.10)
        self.volumeScalarOpacity.AddPoint(self.tf(450), 0.10)
        self.volumeScalarOpacity.AddPoint(self.tf(451), 0.95)
        self.volumeScalarOpacity.AddPoint(self.tf(799), 0.95)
        self.volumeScalarOpacity.AddPoint(self.tf(800), 0.95)

        # The gradient opacity function (decrease opacity in flat regions)
        self.volumeGradientOpacity.RemoveAllPoints()
        self.volumeGradientOpacity.AddPoint(0,   0.0)
        self.volumeGradientOpacity.AddPoint(90,  0.5)
        self.volumeGradientOpacity.AddPoint(100, 1.0)

    def setHead2TF(self):
        # The color transfer function maps voxel intensities to colors.
        self.volumeColor.RemoveAllPoints()
        self.volumeColor.AddRGBPoint(self.tf(600), 0.0, 0.0, 0.0)
        self.volumeColor.AddRGBPoint(self.tf(601), 1.0, 1.0, 0.9)

        # The opacity transfer function (tissue opacity)
        self.volumeScalarOpacity.RemoveAllPoints()
        self.volumeScalarOpacity.AddPoint(self.tf(600), 0.0)
        self.volumeScalarOpacity.AddPoint(self.tf(601), 0.95)

        # The gradient opacity function (decrease opacity in flat regions)
        self.volumeGradientOpacity.RemoveAllPoints()
        self.volumeGradientOpacity.AddPoint(0,   0.0)
        self.volumeGradientOpacity.AddPoint(90,  0.5)
        self.volumeGradientOpacity.AddPoint(100, 1.0)

    def setThoraxTF(self):
        # The color transfer function maps voxel intensities to colors.
        self.volumeColor.RemoveAllPoints()
        self.volumeColor.AddRGBPoint(self.tf(-501), 0.0, 0.0, 0.0)
        self.volumeColor.AddRGBPoint(self.tf(-500), 1.0, 0.3, 0.3)
        self.volumeColor.AddRGBPoint(self.tf(500), 1.0, 0.3, 0.3)
        self.volumeColor.AddRGBPoint(self.tf(501), 1.0, 1.0, 0.9)

        # The opacity transfer function (tissue opacity)
        self.volumeScalarOpacity.RemoveAllPoints()
        self.volumeScalarOpacity.AddPoint(self.tf(-201),  0.0)
        self.volumeScalarOpacity.AddPoint(self.tf(-200), 0.05)
        self.volumeScalarOpacity.AddPoint(self.tf(500), 0.05)
        self.volumeScalarOpacity.AddPoint(self.tf(501), 0.85)

        # The gradient opacity function (decrease opacity in flat regions)
        self.volumeGradientOpacity.RemoveAllPoints()
        self.volumeGradientOpacity.AddPoint(0,   0.0)
        self.volumeGradientOpacity.AddPoint(90,  0.5)
        self.volumeGradientOpacity.AddPoint(100, 1.0)

    def setHipTF(self):
        # The color transfer function maps voxel intensities to colors.
        self.volumeColor.RemoveAllPoints()
        self.volumeColor.AddRGBPoint(self.tf(-150),    0.0, 0.0, 0.0)
        self.volumeColor.AddRGBPoint(self.tf(-100),  0.5, 0, 0)
        self.volumeColor.AddRGBPoint(self.tf(100), 0.5, 0, 0)
        self.volumeColor.AddRGBPoint(self.tf(150), 1.0, 0.3, 0.3)
        self.volumeColor.AddRGBPoint(self.tf(300), 1.0, 0.3, 0.3)
        self.volumeColor.AddRGBPoint(self.tf(350), 1.0, 1.0, 0.9)

        # The opacity transfer function (tissue opacity)
        self.volumeScalarOpacity.RemoveAllPoints()
        self.volumeScalarOpacity.AddPoint(self.tf(-150),    0.00)
        self.volumeScalarOpacity.AddPoint(self.tf(-100),  0.05)
        self.volumeScalarOpacity.AddPoint(self.tf(100),  0.05)
        self.volumeScalarOpacity.AddPoint(self.tf(150), 0.15)
        self.volumeScalarOpacity.AddPoint(self.tf(300), 0.15)
        self.volumeScalarOpacity.AddPoint(self.tf(350), 0.85)

        # The gradient opacity function (decrease opacity in flat regions)
        self.volumeGradientOpacity.RemoveAllPoints()
        self.volumeGradientOpacity.AddPoint(0,   0.0)
        self.volumeGradientOpacity.AddPoint(90,  0.5)
        self.volumeGradientOpacity.AddPoint(100, 1.0)

def main():
    app = QtGui.QApplication(os.sys.argv)
    window = MainWindow()
    window.show()
    os.sys.exit(app.exec_())

if __name__ == '__main__':
    main()
