#---------------------------------------------------------------
# Copyright (C) 2021 Bone Imaging Laboratory
# All rights reserved.
# bonelab@ucalgary.ca
#---------------------------------------------------------------
# Created February 2, 2021
# Steven Boyd
#---------------------------------------------------------------
# The MainWindow class is defined for the Qt GUI as well as
# the signals and slots that make the GUI functional. 
#---------------------------------------------------------------

import os
import sys
import vtk

from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg

class MainWindow(qtw.QMainWindow):
  
  def __init__(self,
               input_file,
               gaussian,
               radius,
               isosurface,
               window_size,
               *args, **kwargs):
    """MainWindow constructor"""
    super().__init__(*args, **kwargs)
    
    # Window setup
    self.resize(window_size[0],window_size[1])
    self.title = "Basic Qt Viewer for MDSC 689.03"

    self.statusBar().showMessage("Welcome.",8000)
    
    # Capture defaults
    self.gaussian = gaussian
    self.radius = radius
    self.isosurface = isosurface
    
    # Initialize the window
    self.initUI()
    
    # Set up some VTK pipeline classes
    self.reader = None
    self.gauss = vtk.vtkImageGaussianSmooth()
    self.marchingCubes = vtk.vtkImageMarchingCubes()
    self.mapper = vtk.vtkPolyDataMapper()
    self.actor = vtk.vtkActor()
    
    # Take inputs from command line. Only use these if there is an input file specified
    if (input_file != None):
      if (not os.path.exists(input_file)):
        qtw.QMessageBox.warning(self, "Error", "Invalid input file.")
        return
        
      #_,ext = os.path.splitext(input_file)
      #if not (self.validExtension(ext.lower())):
      #  qtw.QMessageBox.warning(self, "Error", "Invalid file type.")
      #  return
      
      self.createPipeline(input_file)
      self.statusBar().showMessage("Loading file " + input_file,4000)
      self.changeSigma(gaussian)
      self.changeRadius(radius)
      self.changeIsosurface(isosurface)
      
    
  def initUI(self):
    ########################################
    # Create Widgets
    ########################################
        
    self.loadPushButton = qtw.QPushButton(
      "Load Image",
      self,
      objectName = "loadPushButton",
      shortcut=qtg.QKeySequence("Ctrl+f")
    )
    self.sigmaSpinBox = qtw.QDoubleSpinBox(
      self, 
      objectName = "sigmaSpinBox",
      value=self.gaussian, 
      decimals=1, 
      maximum=20.0, 
      minimum=0.1, 
      singleStep=0.1,
      keyboardTracking=False
    )
    self.radiusSpinBox = qtw.QSpinBox(
      self, 
      objectName = "radiusSpinBox",
      value=self.radius, 
      maximum=20, 
      minimum=1, 
      singleStep=1,
      keyboardTracking=False
    )
    self.isosurfaceSpinBox = qtw.QSpinBox(
      self, 
      objectName = "isosurfaceSpinBox",
      value=self.isosurface, 
      maximum=32768, 
      minimum=0, 
      singleStep=1,
      keyboardTracking=False
    )
    
    # Create the menu options --------------------------------------------------------------------
    menubar = qtw.QMenuBar()
    self.setMenuBar(menubar)
    menubar.setNativeMenuBar(False)

    file_menu = menubar.addMenu("File")
    open_action = file_menu.addAction("Open Image")
    file_menu.addSeparator()
    about_action = file_menu.addAction("About")
    quit_action = file_menu.addAction("Quit")

    # Lay out the GUI ----------------------------------------------------------------------------
    self.mainGroupBox = qtw.QGroupBox("Image Controls")
    self.mainGroupBox.setLayout(qtw.QHBoxLayout())
  
    self.isosurfaceGroupBox = qtw.QGroupBox("Isosurface controls")
    self.isosurfaceGroupBox.setLayout(qtw.QVBoxLayout())
    self.isosurfaceFormLayout = qtw.QFormLayout()
    self.isosurfaceFormLayout.addRow("Sigma",self.sigmaSpinBox)
    self.isosurfaceFormLayout.addRow("Radius",self.radiusSpinBox)
    self.isosurfaceFormLayout.addRow("Isosurface",self.isosurfaceSpinBox)
    self.isosurfaceGroupBox.layout().addLayout(self.isosurfaceFormLayout)
    
    self.mainGroupBox.layout().addWidget(self.loadPushButton)
    self.mainGroupBox.layout().addWidget(self.isosurfaceGroupBox)
  
    # Assemble the side control panel and put it in a QPanel widget ------------------------------
    self.panel = qtw.QVBoxLayout()
    self.panel.addWidget(self.mainGroupBox)
    self.panelWidget = qtw.QFrame()
    self.panelWidget.setLayout(self.panel)    
    
    # Create the VTK rendering window ------------------------------------------------------------
    self.vtkWidget = QVTKRenderWindowInteractor()
    self.vtkWidget.AddObserver("ExitEvent", lambda o, e, a=self: a.quit())
    self.vtkWidget.AddObserver("KeyReleaseEvent", self.keyEventDetected)
    self.vtkWidget.AddObserver("LeftButtonPressEvent", self.mouseEventDetected)
    
    # Create main layout and add VTK window and control panel
    self.mainLayout = qtw.QHBoxLayout()
    self.mainLayout.addWidget(self.vtkWidget,4)
    self.mainLayout.addWidget(self.panelWidget,1)

    self.frame = qtw.QFrame()
    self.frame.setLayout(self.mainLayout)
    self.setCentralWidget(self.frame)
    
    self.setWindowTitle(self.title)
    self.centreWindow()
    
    # Set size policies --------------------------------------------------------------------------
    self.sigmaSpinBox.setMinimumSize(70,20) 
    self.radiusSpinBox.setMinimumSize(70,20) 
    self.isosurfaceSpinBox.setMinimumSize(70,20) 
  
    self.mainGroupBox.setMaximumSize(1000,200)
    
    self.vtkWidget.setSizePolicy(
      qtw.QSizePolicy.MinimumExpanding,
      qtw.QSizePolicy.MinimumExpanding
    )
    
    self.mainGroupBox.setSizePolicy(
      qtw.QSizePolicy.Maximum,
      qtw.QSizePolicy.Maximum
    )
    
    # Connect signals and slots ------------------------------------------------------------------
    self.loadPushButton.clicked.connect(self.openFile)
    self.sigmaSpinBox.valueChanged.connect(lambda s: self.changeSigma(s))
    self.radiusSpinBox.valueChanged.connect(lambda s: self.changeRadius(s))
    self.isosurfaceSpinBox.valueChanged.connect(lambda s: self.changeIsosurface(s))

    self.initRenderWindow()
    
    # Menu actions
    open_action.triggered.connect(self.openFile)
    about_action.triggered.connect(self.about)
    quit_action.triggered.connect(self.quit)
    
    self.pipe = None
    
    # End main UI code
    self.show()
    
    ########################################
    # Define methods for controlling GUI
    ########################################

  def centreWindow(self):
    qr = self.frameGeometry()
    cp = qtw.QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    self.move(qr.topLeft())
  
  def initRenderWindow(self):
    # Create renderer
    self.renderer = vtk.vtkRenderer()
    self.renderer.SetBackground((0.000, 0.000, 204.0/255.0)) # Scanco blue

    # Create interactor
    self.renWin = self.vtkWidget.GetRenderWindow()
    self.renWin.AddRenderer(self.renderer)
    self.iren = self.renWin.GetInteractor()
    self.iren.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())

    # Initialize
    self.iren.Initialize()
    self.iren.Start()

  def createPipeline(self, _filename):
    # Read in the file
    if _filename.lower().endswith('.nii'):
      self.reader = vtk.vtkNIFTIImageReader()
      self.reader.SetFileName(_filename)
    elif _filename.lower().endswith('.nii.gz'):
      self.reader = vtk.vtkNIFTIImageReader()
      self.reader.SetFileName(_filename)
    elif _filename.lower().endswith('.dcm'):
      self.reader = vtk.vtkDICOMImageReader()
      self.reader.SetDirectoryName(os.path.dirname(_filename))
    elif os.path.isdir(_filename):
      self.reader = vtk.vtkDICOMImageReader()
      self.reader.SetDirectoryName(_filename)
      
    if self.reader is None:
        os.sys.exit("[ERROR] Cannot find reader for file \"{}\"".format(self.filename))
    self.reader.Update()
    
    # Gaussian smoothing
    self.gauss.SetStandardDeviation(self.gaussian, self.gaussian, self.gaussian)
    self.gauss.SetRadiusFactors(self.radius, self.radius, self.radius)
    self.gauss.SetInputConnection(self.reader.GetOutputPort())
    
    # Marching Cubes
    self.marchingCubes.SetInputConnection(self.gauss.GetOutputPort())
    self.marchingCubes.ComputeGradientsOn()
    self.marchingCubes.ComputeNormalsOn()
    self.marchingCubes.ComputeScalarsOff()
    self.marchingCubes.SetNumberOfContours(1)
    self.marchingCubes.SetValue(0, self.isosurface)
    
    # Set mapper for image data
    self.mapper.SetInputConnection(self.marchingCubes.GetOutputPort())
    
    # Actor
    self.actor.SetMapper(self.mapper)
    self.actor.GetProperty().SetColor((0.890, 0.855, 0.788))
    self.renderer.AddActor(self.actor)
    
    self.refreshRenderWindow()
    return
          
  def changeSigma(self, _value):
    self.gauss.SetStandardDeviation(_value, _value, _value)
    self.statusBar().showMessage(f"Changing standard deviation to {_value}",4000)
    self.refreshRenderWindow()
    return
    
  def changeRadius(self, _value):
    self.gauss.SetRadiusFactors(_value, _value, _value)
    self.statusBar().showMessage(f"Changing radius to {_value}",4000)
    self.refreshRenderWindow()
    return
    
  def changeIsosurface(self, _value):
    self.marchingCubes.SetValue(0, _value)
    self.statusBar().showMessage(f"Changing isosurface to {_value}",4000)
    self.refreshRenderWindow()
    return

  def keyEventDetected(self,obj,event):
    key = self.vtkWidget.GetKeySym()
    print("key press – clicked "+key+"!")
    return
  
  def mouseEventDetected(self,obj,event):
    print("mouse press – click!")
    return
  
  def validExtension(self, extension):
    if (extension == ".nii" or \
        extension == ".dcm"):
      return True
    else:
      return False
      
  def openFile(self):
    self.statusBar().showMessage("Load image types (.nii, .dcm)",4000)
    filename, _ = qtw.QFileDialog.getOpenFileName(
      self,
      "Select a 3D image file to open…",
      qtc.QDir.homePath(),
      "Nifti Files (*.nii) ;;DICOM Files (*.dcm) ;;All Files (*)",
      "All Files (*)",
      qtw.QFileDialog.DontUseNativeDialog |
      qtw.QFileDialog.DontResolveSymlinks
    )
    
    if filename:
      _,ext = os.path.splitext(filename)
      if not (self.validExtension(ext.lower())):
        qtw.QMessageBox.warning(self, "Error", "Invalid file type.")
        return
      
      self.createPipeline(filename)
      self.statusBar().showMessage("Loading file " + filename,4000)
    return
    
  def quit(self):
    reply = qtw.QMessageBox.question(self, "Message",
      "Are you sure you want to quit?", qtw.QMessageBox.Yes |
      qtw.QMessageBox.No, qtw.QMessageBox.Yes)
    if reply == qtw.QMessageBox.Yes:
      exit(0)

  def about(self):
    about = qtw.QMessageBox(self)
    about.setText("blQtBasic 1.0")
    about.setInformativeText("Copyright (C) 2021\nBone Imaging Laboratory\nAll rights reserved.\nbonelab@ucalgary.ca")
    about.setStandardButtons(qtw.QMessageBox.Ok | qtw.QMessageBox.Cancel)
    about.exec_()
   