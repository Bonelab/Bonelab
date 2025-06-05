#---------------------------------------------------------------
# Copyright (C) 2020 Bone Imaging Laboratory
# All rights reserved.
# bonelab@ucalgary.ca
#---------------------------------------------------------------
# Created December 4, 2020
# Steven Boyd
#---------------------------------------------------------------
# The MainWindow class is defined for the Qt GUI as well as
# the signals and slots that make the GUI functional. 
# The transforms applied to image2 are calculated by various 
# means such as ICP and Landmarks, but stored in the Pipeline()
# class. 
#---------------------------------------------------------------
# TODO: 
# 2. The Icon needs a relative path. Where does the Icon show?
# 3. The ColorPalette idea is a bad one. Needs to be replaced.
#---------------------------------------------------------------

import os
import sys
import vtk
import vtkbone

from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from bonelab.gui.qtviewer.interactor import MyInteractorStyle
from bonelab.gui.qtviewer.pipeline import Pipeline
from bonelab.gui.qtviewer.colourpalette import ColourPalette
from bonelab.gui.qtviewer.scancomatrixconverter import ScancoMatrixConverter
from bonelab.gui.qtviewer.resources import *

from PyQt6 import QtWidgets as qtw
from PyQt6 import QtCore as qtc
from PyQt6 import QtGui as qtg

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
    self.title = "Bone Imaging Laboratory – Viewer"
    self.iconPath = os.path.join(os.getcwd(), "qtviewer")
    self.iconPath = os.path.abspath(os.path.join(self.iconPath, "icon.png"))

    self.statusBar().showMessage("Welcome.",8000)
    
    # Initialize the window
    self.initUI()
    
    # Default filepath 
    self.default_path = qtc.QDir.homePath()
    
    # Take inputs from command line. Only use these if there is an input file specified
    if (input_file != None):
      if (not os.path.exists(input_file)):
        qtw.QMessageBox.warning(self, "Error", "Invalid input file.")
        return
        
      _,ext = os.path.splitext(input_file)
      if not (self.validExtension(ext.lower())):
        qtw.QMessageBox.warning(self, "Error", "Invalid file type.")
        return
      
      self.createPipeline(input_file, "in1")
      self.statusBar().showMessage("Loading file " + input_file,4000)
      self.changeSigma(gaussian, "in1")
      self.changeRadius(radius, "in1")
      self.changeIsosurface(isosurface, "in1")
      self.updateGUI()
      
    
  def initUI(self):
    ########################################
    # Create Widgets
    ########################################
        
    # Fixed image (in1)    
    self.in1_loadPushButton = qtw.QPushButton(
      "Load Image 1",
      self,
      objectName = "in1_loadPushButton",
      shortcut=qtg.QKeySequence("Ctrl+f")
    )
    self.in1_pickableCheckBox = qtw.QCheckBox(
      "Pickable",
      self,
      objectName = "in1_pickableCheckBox",
      checkable=True,
      checked=True
    )
    self.in1_visibilityCheckBox = qtw.QCheckBox(
      "Visibility",
      self,
      objectName = "in1_visibilityCheckBox",
      checkable=True,
      checked=True
    )
    self.in1_filenameLabel = qtw.QLabel(
      "",
      self
    )
    
    self.in1_sigmaSpinBox = qtw.QDoubleSpinBox(
      self, 
      objectName = "in1_sigmaSpinBox",
      value=1.2, 
      decimals=1, 
      maximum=20.0, 
      minimum=0.1, 
      singleStep=0.1,
      keyboardTracking=False
    )
    self.in1_radiusSpinBox = qtw.QSpinBox(
      self, 
      objectName = "in1_radiusSpinBox",
      value=2, 
      maximum=20, 
      minimum=1, 
      singleStep=1,
      keyboardTracking=False
    )
    self.in1_isosurfaceSpinBox = qtw.QSpinBox(
      self, 
      objectName = "in1_isosurfaceSpinBox",
      value=0, 
      maximum=32768, 
      minimum=0, 
      singleStep=1,
      keyboardTracking=False
    )
    
    # Moving image (in2)    
    self.in2_loadPushButton = qtw.QPushButton(
      "Load Image 2",
      self,
      objectName = "in2_loadPushButton",
      shortcut=qtg.QKeySequence("Ctrl+m")
    )
    self.in2_pickableCheckBox = qtw.QCheckBox(
      "Pickable",
      self,
      objectName = "in2_pickableCheckBox",
      checkable=True,
      checked=False
    )
    self.in2_visibilityCheckBox = qtw.QCheckBox(
      "Visibility",
      self,
      objectName = "in2_visibilityCheckBox",
      checkable=True,
      checked=True
    )
    self.in2_filenameLabel = qtw.QLabel(
      "",
      self
    )
    
    self.in2_sigmaSpinBox = qtw.QDoubleSpinBox(
      self, 
      objectName = "in2_sigmaSpinBox",
      value=1.2, 
      decimals=1, 
      maximum=20.0, 
      minimum=0.1, 
      singleStep=0.1,
      keyboardTracking=False
    ) 
    self.in2_radiusSpinBox = qtw.QSpinBox(
      self, 
      objectName = "in2_radiusSpinBox",
      value=2, 
      maximum=20, 
      minimum=1, 
      singleStep=1,
      keyboardTracking=False
    )    
    self.in2_isosurfaceSpinBox = qtw.QSpinBox(
      self, 
      objectName = "in2_isosurfaceSpinBox",
      value=0, 
      maximum=32768, 
      minimum=0, 
      singleStep=1,
      keyboardTracking=False
    ) 
    
    # Camera controls
    self.rollCameraPushButton = qtw.QPushButton(
      "Roll", self,
      objectName = "rollCameraPushButton"
    )
    self.elevationCameraPushButton = qtw.QPushButton(
      "Elevation", self,
      objectName = "elevationCameraPushButton"
    )
    self.azimuthCameraPushButton = qtw.QPushButton(
      "Azimuth", self,
      objectName = "azimuthCameraPushButton"
    )
    self.incrementCameraSpinBox = qtw.QSpinBox(
      self, 
      objectName = "incrementCameraSpinBox",
      value=90, 
      maximum=90, 
      minimum=-90, 
      singleStep=10
    )    
    
    # Landmark transform
    self.landmarkTransformPushButton = qtw.QPushButton(
      "Landmark",
      self,
      objectName = "Landmark Transform",
      enabled=False,
      shortcut=qtg.QKeySequence("Ctrl+l")
    )
    
    # ICP transform
    self.icpTransformPushButton = qtw.QPushButton(
      "ICP",
      self,
      objectName = "ICP Transform",
      enabled=True,
      shortcut=qtg.QKeySequence("Ctrl+i")
    )
    
    # Reset transform
    self.resetTransformPushButton = qtw.QPushButton(
      "Reset",
      self,
      objectName = "Reset Transform",
      enabled=True,
      shortcut=qtg.QKeySequence("Ctrl+r")
    )
    
    self.viewTransformCheckBox = qtw.QCheckBox(
      "Toggle View",
      self,
      objectName = "View Transform",
      checkable=True,
      checked=True
    )
    
    self.in1_points_count_label = qtw.QLabel(
      "in1_points_label",
      self,
      text="Points"
    )
    self.in2_points_count_label = qtw.QLabel(
      "in2_points_label",
      self,
      text="Points"
    )
    self.in1_points_count = qtw.QLCDNumber(
      self,
      intValue=0,
      segmentStyle=qtw.QLCDNumber.SegmentStyle.Flat
    )
    self.in2_points_count = qtw.QLCDNumber(
      self,
      intValue=0,
      segmentStyle=qtw.QLCDNumber.SegmentStyle.Flat
    )
    
    # Vectors
    self.rot1 = qtw.QLabel("rot1",self,text="  0.000")
    self.rot2 = qtw.QLabel("rot2",self,text="  0.000")
    self.rot3 = qtw.QLabel("rot3",self,text="  0.000")
    self.trans1 = qtw.QLabel("trans1",self,text="  0.000")
    self.trans2 = qtw.QLabel("trans2",self,text="  0.000")
    self.trans3 = qtw.QLabel("trans3",self,text="  0.000")
    self.rotLabel = qtw.QLabel("R:",self)
    self.transLabel = qtw.QLabel("T:",self)
    
    # 4x4 matrix
    self.mat11 = qtw.QLabel("mat11",self,text="  0.000")
    self.mat12 = qtw.QLabel("mat12",self,text="  0.000")
    self.mat13 = qtw.QLabel("mat13",self,text="  0.000")
    self.mat14 = qtw.QLabel("mat14",self,text="  0.000")
    self.mat21 = qtw.QLabel("mat21",self,text="  0.000")
    self.mat22 = qtw.QLabel("mat22",self,text="  0.000")
    self.mat23 = qtw.QLabel("mat23",self,text="  0.000")
    self.mat24 = qtw.QLabel("mat24",self,text="  0.000")
    self.mat31 = qtw.QLabel("mat31",self,text="  0.000")
    self.mat32 = qtw.QLabel("mat32",self,text="  0.000")
    self.mat33 = qtw.QLabel("mat33",self,text="  0.000")
    self.mat34 = qtw.QLabel("mat34",self,text="  0.000")
    self.mat41 = qtw.QLabel("mat41",self,text="  0.000")
    self.mat42 = qtw.QLabel("mat42",self,text="  0.000")
    self.mat43 = qtw.QLabel("mat43",self,text="  0.000")
    self.mat44 = qtw.QLabel("mat44",self,text="  0.000")
    
    self.updateMatrixGUI(vtk.vtkMatrix4x4())
    
    # Log window
    self.log_window = qtw.QTextEdit(
      self,
      objectName = "log_window",
      acceptRichText=False,
      lineWrapMode=qtw.QTextEdit.LineWrapMode.NoWrap,
      lineWrapColumnOrWidth=80,
      placeholderText="Ready..."
    )

    # Create the menu options --------------------------------------------------------------------
    menubar = qtw.QMenuBar()
    self.setMenuBar(menubar)
    menubar.setNativeMenuBar(False)

    file_menu = menubar.addMenu("File")
    open_in1_action = file_menu.addAction("Open Image1")
    open_in2_action = file_menu.addAction("Open Image2")
    file_menu.addSeparator()
    about_action = file_menu.addAction("About")
    quit_action = file_menu.addAction("Quit")

    save_menu = menubar.addMenu("Save")
    save_log_action = save_menu.addAction("Log Window")
    save_menu.addSeparator()
    save_points_action = save_menu.addAction("Points")
    save_transform_matrix_action = save_menu.addAction("Transform Matrix")
    save_transform_vector_action = save_menu.addAction("Transform Vector")
    save_menu.addSeparator()
    save_extrusion_action = save_menu.addAction("Extruded Shape")
    
    ########################################
    # Layouts
    ########################################
    
    # Fixed Image (in1) --------------------------------------------------------------------------
    self.in1_mainGroupBox = qtw.QGroupBox("Fixed Image (in1) [white]")
    self.in1_mainGroupBox.setLayout(qtw.QHBoxLayout())
    
    self.in1_pointWidget = qtw.QFrame()
    self.in1_pointWidget.setLayout(qtw.QHBoxLayout())
    self.in1_pointWidget.layout().addWidget(self.in1_points_count_label)
    self.in1_pointWidget.layout().addWidget(self.in1_points_count)
    
    self.in1_loadGridLayout = qtw.QGridLayout()
    self.in1_loadGridLayout.addWidget(self.in1_loadPushButton,0,0,1,1)
    self.in1_loadGridLayout.addWidget(self.in1_pickableCheckBox,0,1,1,1)
    self.in1_loadGridLayout.addWidget(self.in1_pointWidget,1,0,1,1)
    self.in1_loadGridLayout.addWidget(self.in1_visibilityCheckBox,1,1,1,1)
    self.in1_loadGridLayout.addWidget(self.in1_filenameLabel,2,0,1,4)
    
    self.in1_isosurfaceGroupBox = qtw.QGroupBox("Isosurface controls")
    self.in1_isosurfaceGroupBox.setLayout(qtw.QVBoxLayout())
    self.in1_isosurfaceFormLayout = qtw.QFormLayout()
    self.in1_isosurfaceFormLayout.addRow("Sigma",self.in1_sigmaSpinBox)
    self.in1_isosurfaceFormLayout.addRow("Radius",self.in1_radiusSpinBox)
    self.in1_isosurfaceFormLayout.addRow("Isosurface",self.in1_isosurfaceSpinBox)
    self.in1_isosurfaceGroupBox.layout().addLayout(self.in1_isosurfaceFormLayout)
    
    self.in1_mainGroupBox.layout().addLayout(self.in1_loadGridLayout)
    self.in1_mainGroupBox.layout().addWidget(self.in1_isosurfaceGroupBox)
        
    # Moving Image (in2) -------------------------------------------------------------------------
    self.in2_mainGroupBox = qtw.QGroupBox("Moving Image (in2) [yellow]")
    self.in2_mainGroupBox.setLayout(qtw.QHBoxLayout())
    
    self.in2_pointWidget = qtw.QFrame()
    self.in2_pointWidget.setLayout(qtw.QHBoxLayout())
    self.in2_pointWidget.layout().addWidget(self.in2_points_count_label)
    self.in2_pointWidget.layout().addWidget(self.in2_points_count)
    
    self.in2_loadGridLayout = qtw.QGridLayout()
    self.in2_loadGridLayout.addWidget(self.in2_loadPushButton,0,0,1,1)
    self.in2_loadGridLayout.addWidget(self.in2_pickableCheckBox,0,1,1,1)
    self.in2_loadGridLayout.addWidget(self.in2_pointWidget,1,0,1,1)
    self.in2_loadGridLayout.addWidget(self.in2_visibilityCheckBox,1,1,1,1)
    self.in2_loadGridLayout.addWidget(self.in2_filenameLabel,2,0,1,4)
    
    self.in2_isosurfaceGroupBox = qtw.QGroupBox("Isosurface controls")
    self.in2_isosurfaceGroupBox.setLayout(qtw.QVBoxLayout())
    self.in2_isosurfaceFormLayout = qtw.QFormLayout()
    self.in2_isosurfaceFormLayout.addRow("Sigma",self.in2_sigmaSpinBox)
    self.in2_isosurfaceFormLayout.addRow("Radius",self.in2_radiusSpinBox)
    self.in2_isosurfaceFormLayout.addRow("Isosurface",self.in2_isosurfaceSpinBox)
    self.in2_isosurfaceGroupBox.layout().addLayout(self.in2_isosurfaceFormLayout)
    
    self.in2_mainGroupBox.layout().addLayout(self.in2_loadGridLayout)
    self.in2_mainGroupBox.layout().addWidget(self.in2_isosurfaceGroupBox)

    # Camera controls panel ----------------------------------------------------------------------
    self.cameraControlsGroupBox = qtw.QGroupBox("Camera")
    self.cameraControlsGroupBox.setLayout(qtw.QHBoxLayout())
    self.cameraControlsGroupBox.layout().addWidget(self.rollCameraPushButton)
    self.cameraControlsGroupBox.layout().addWidget(self.elevationCameraPushButton)
    self.cameraControlsGroupBox.layout().addWidget(self.azimuthCameraPushButton)
    self.incrementCameraFormLayout = qtw.QFormLayout()
    self.incrementCameraFormLayout.addRow("Increment",self.incrementCameraSpinBox)
    self.cameraControlsGroupBox.layout().addLayout(self.incrementCameraFormLayout)

    # Transform panel ----------------------------------------------------------------------------
    self.transformPanelGroupBox = qtw.QGroupBox("Transform")
    self.transformPanelGroupBox.setLayout(qtw.QHBoxLayout())
    
    # Transform actions
    self.transformLayout = qtw.QGridLayout()
    self.transformLayout.addWidget(self.landmarkTransformPushButton,0,0,1,1)
    self.transformLayout.addWidget(self.icpTransformPushButton,0,1,1,1)
    self.transformLayout.addWidget(self.resetTransformPushButton,1,0,1,1)
    self.transformLayout.addWidget(self.viewTransformCheckBox,1,1,1,1)
    
    # Vectors display
    self.vectorsLayout = qtw.QGridLayout()
    self.vectorsLayout.addWidget(self.rotLabel,0,0,1,1)
    self.vectorsLayout.addWidget(self.rot1,0,1,1,1)
    self.vectorsLayout.addWidget(self.rot2,0,2,1,1)
    self.vectorsLayout.addWidget(self.rot3,0,3,1,1)
    self.vectorsLayout.addWidget(self.transLabel,1,0,1,1)
    self.vectorsLayout.addWidget(self.trans1,1,1,1,1)
    self.vectorsLayout.addWidget(self.trans2,1,2,1,1)
    self.vectorsLayout.addWidget(self.trans3,1,3,1,1)
    
    self.vectorsGroupBox = qtw.QGroupBox()
    self.vectorsGroupBox.setLayout(self.vectorsLayout)
    self.transformLayout.addWidget(self.vectorsGroupBox,2,0,2,2)
    
    # Matrix display
    self.matrixLayout = qtw.QGridLayout()
    self.matrixLayout.addWidget(self.mat11,0,0,1,1)
    self.matrixLayout.addWidget(self.mat12,0,1,1,1)
    self.matrixLayout.addWidget(self.mat13,0,2,1,1)
    self.matrixLayout.addWidget(self.mat14,0,3,1,1)
    self.matrixLayout.addWidget(self.mat21,1,0,1,1)
    self.matrixLayout.addWidget(self.mat22,1,1,1,1)
    self.matrixLayout.addWidget(self.mat23,1,2,1,1)
    self.matrixLayout.addWidget(self.mat24,1,3,1,1)
    self.matrixLayout.addWidget(self.mat31,2,0,1,1)
    self.matrixLayout.addWidget(self.mat32,2,1,1,1)
    self.matrixLayout.addWidget(self.mat33,2,2,1,1)
    self.matrixLayout.addWidget(self.mat34,2,3,1,1)
    self.matrixLayout.addWidget(self.mat41,3,0,1,1)
    self.matrixLayout.addWidget(self.mat42,3,1,1,1)
    self.matrixLayout.addWidget(self.mat43,3,2,1,1)
    self.matrixLayout.addWidget(self.mat44,3,3,1,1)
    
    self.matrixGroupBox = qtw.QGroupBox("Matrix4x4 (in2)")
    self.matrixGroupBox.setLayout(self.matrixLayout)
    
    self.transformPanelGroupBox.layout().addLayout(self.transformLayout)
    self.transformPanelGroupBox.layout().addWidget(self.matrixGroupBox)
    
    # Set up the log window ----------------------------------------------------------------------
    font = qtg.QFont("Courier")
    font.setStyleHint(qtg.QFont.StyleHint.TypeWriter)
    font.setWeight(25)
    self.log_window.setTextColor(qtg.QColor("blue"))
    self.log_window.setCurrentFont(font)
    
    # Add logo -----------------------------------------------------------------------------------
    logo = qtg.QPixmap(':/bonelab/icon.png')
    self.logoLabel = qtw.QLabel("",self)
    self.logoLabel.setPixmap(logo)
    
    # Assemble the side control panel and put it in a QPanel widget ------------------------------
    self.panel = qtw.QVBoxLayout()
    self.panel.addWidget(self.in1_mainGroupBox)
    self.panel.addWidget(self.in2_mainGroupBox)
    self.panel.addWidget(self.cameraControlsGroupBox)
    self.panel.addWidget(self.transformPanelGroupBox)
    self.panel.addWidget(self.log_window)
    self.panel.addWidget(self.logoLabel, alignment=qtc.Qt.AlignmentFlag.AlignRight)
    self.panelWidget = qtw.QFrame()
    self.panelWidget.setLayout(self.panel)    
    
    # Create the VTK rendering window ------------------------------------------------------------
    self.vtkWidget = QVTKRenderWindowInteractor()
    self.vtkWidget.AddObserver("ExitEvent", lambda o, e, a=self: a.quit())
    #self.vtkWidget.AddObserver("KeyReleaseEvent", self.keyEventDetected)
    #self.vtkWidget.AddObserver("LeftButtonReleaseEvent", self.mouseEventDetected)
    
    # Create main layout and add VTK window and control panel
    self.mainLayout = qtw.QHBoxLayout()
    self.mainLayout.addWidget(self.vtkWidget,4)
    self.mainLayout.addWidget(self.panelWidget,2)

    self.frame = qtw.QFrame()
    self.frame.setLayout(self.mainLayout)
    self.setCentralWidget(self.frame)
    
    self.setWindowTitle(self.title)
    self.centreWindow()
    #print(self.iconPath)
    self.setWindowIcon(qtg.QIcon(self.iconPath))       
    
    self.cp = ColourPalette()
    
    # Set size policies --------------------------------------------------------------------------
    self.in1_sigmaSpinBox.setMinimumSize(70,20) 
    self.in1_radiusSpinBox.setMinimumSize(70,20) 
    self.in1_isosurfaceSpinBox.setMinimumSize(70,20) 
    
    self.in2_sigmaSpinBox.setMinimumSize(70,20) 
    self.in2_radiusSpinBox.setMinimumSize(70,20) 
    self.in2_isosurfaceSpinBox.setMinimumSize(70,20)
    
    self.in1_mainGroupBox.setMaximumSize(1000,1000)
    self.in2_mainGroupBox.setMaximumSize(1000,1000)
    self.transformPanelGroupBox.setMaximumSize(1000,1000)
    
    self.rotLabel.setMaximumSize(15,20)
    self.transLabel.setMaximumSize(15,20)
    
    self.vtkWidget.setSizePolicy(
      qtw.QSizePolicy.Policy.MinimumExpanding,
      qtw.QSizePolicy.Policy.MinimumExpanding
    )
    
    self.in1_points_count.setMaximumSize(50,30)
    self.in2_points_count.setMaximumSize(50,30)
    
    self.in1_mainGroupBox.setSizePolicy(
      qtw.QSizePolicy.Policy.Maximum,
      qtw.QSizePolicy.Policy.Maximum
    )
    
    self.in2_mainGroupBox.setSizePolicy(
      qtw.QSizePolicy.Policy.Maximum,
      qtw.QSizePolicy.Policy.Maximum
    )
    
    self.transformPanelGroupBox.setSizePolicy(
      qtw.QSizePolicy.Policy.Maximum,
      qtw.QSizePolicy.Policy.Maximum
    )

    self.log_window.setSizePolicy(
      qtw.QSizePolicy.Policy.MinimumExpanding,
      qtw.QSizePolicy.Policy.MinimumExpanding
    )
    
    # Connect signals and slots ------------------------------------------------------------------
    # The use of the lambda function is so that the same slot can be used for either pipeline
    self.in1_loadPushButton.clicked.connect(lambda: self.openFile("in1"))
    self.in1_pickableCheckBox.stateChanged.connect(lambda s: self.togglePickable(s,"in1"))
    self.in1_visibilityCheckBox.stateChanged.connect(lambda s: self.toggleVisibility(s,"in1"))
    self.in1_sigmaSpinBox.valueChanged.connect(lambda s: self.changeSigma(s,"in1"))
    self.in1_radiusSpinBox.valueChanged.connect(lambda s: self.changeRadius(s,"in1"))
    self.in1_isosurfaceSpinBox.valueChanged.connect(lambda s: self.changeIsosurface(s,"in1"))
      
    self.in2_loadPushButton.clicked.connect(lambda: self.openFile("in2"))
    self.in2_pickableCheckBox.stateChanged.connect(lambda s: self.togglePickable(s,"in2"))
    self.in2_visibilityCheckBox.stateChanged.connect(lambda s: self.toggleVisibility(s,"in2"))
    self.in2_sigmaSpinBox.valueChanged.connect(lambda s: self.changeSigma(s,"in2"))
    self.in2_radiusSpinBox.valueChanged.connect(lambda s: self.changeRadius(s,"in2"))
    self.in2_isosurfaceSpinBox.valueChanged.connect(lambda s: self.changeIsosurface(s,"in2"))

    self.initRenderWindow()
    self.in2_mainGroupBox.setEnabled(False) # Force user to load in1 before in2
    
    # Camera
    self.rollCameraPushButton.clicked.connect(lambda: self.updateCamera("roll"))
    self.elevationCameraPushButton.clicked.connect(lambda: self.updateCamera("elevation"))
    self.azimuthCameraPushButton.clicked.connect(lambda: self.updateCamera("azimuth"))
    
    # Transform
    self.landmarkTransformPushButton.clicked.connect(self.applyLandmarkTransform)
    self.icpTransformPushButton.clicked.connect(self.applyICPTransform)
    self.resetTransformPushButton.clicked.connect(self.resetTransform)
    self.viewTransformCheckBox.stateChanged.connect(self.toggleTransformApplied)
    
    # Menu actions
    open_in1_action.triggered.connect(lambda: self.openFile("in1"))
    open_in2_action.triggered.connect(lambda: self.openFile("in2"))
    about_action.triggered.connect(self.about)
    quit_action.triggered.connect(self.quit)

    save_log_action.triggered.connect(self.saveLogFile)
    save_points_action.triggered.connect(self.savePointsFile)
    save_transform_matrix_action.triggered.connect(lambda: self.saveTransformFile("matrix"))
    save_transform_vector_action.triggered.connect(lambda: self.saveTransformFile("vector"))
    save_extrusion_action.triggered.connect(self.extrudeFromPoints)
    
    # Variables for managing the VTK pipelines
    self.in1_pipe = None
    self.in2_pipe = None
    
    # End main UI code
    self.show()
    
  def centreWindow(self):
    qr = self.frameGeometry()
    screen = qtw.QApplication.primaryScreen()
    cp = screen.availableGeometry().center()
    qr.moveCenter(cp)
    self.move(qr.topLeft())
  
  def doit(self):
      print('hi')
      
  def initRenderWindow(self):
    # Create renderer
    self.renderer = vtk.vtkRenderer()
    self.renderer.SetBackground(self.cp.getColour("background2"))

    # Create interactor
    self.renWin = self.vtkWidget.GetRenderWindow()
    self.renWin.AddRenderer(self.renderer)
    self.iren = self.renWin.GetInteractor()
    
    #self.iren.AddObserver("KeyPressEvent",self.doit())
    
    self.pickerstyle = MyInteractorStyle()
    self.pickerstyle.AddObserver("UpdateEvent", self.keyEventDetected)
    self.iren.SetInteractorStyle(self.pickerstyle)
    #self.pickerstyle.SetCurrentStyleToTrackballCamera()
    #self.iren.SetInteractorStyle(vtk.vtkInteractorStyleSwitch())
    #print(self.iren.GetInteractorStyle().GetClassName())
    
    # Initialize
    self.iren.Initialize()
    # self.iren.Start()

  def refreshRenderWindow(self):
    self.renWin.Render()
    self.renderer.ResetCamera()
    self.iren.Render()

  def setPipelineAttributesFromGUI(self, pipeline):
    if (pipeline == "in1"):
      if self.in1_pickableCheckBox.isChecked():
        self.in1_pipe.setActorPickable(1)
      else:
        self.in1_pipe.setActorPickable(0)
      if self.in1_visibilityCheckBox.isChecked():
        self.in1_pipe.setActorVisibility(1)
      else:
        self.in1_pipe.setActorVisibility(0)
      self.in1_pipe.setGaussStandardDeviation(self.in1_sigmaSpinBox.value())
      self.in1_pipe.setGaussRadius(self.in1_radiusSpinBox.value())
      self.in1_pipe.setIsosurface(self.in1_isosurfaceSpinBox.value())
    elif (pipeline == "in2"):
      if self.in2_pickableCheckBox.isChecked():
        self.in2_pipe.setActorPickable(1)
      else:
        self.in2_pipe.setActorPickable(0)
      if self.in2_visibilityCheckBox.isChecked():
        self.in2_pipe.setActorVisibility(1)
      else:
        self.in2_pipe.setActorVisibility(0)
      self.in2_pipe.setGaussStandardDeviation(self.in2_sigmaSpinBox.value())
      self.in2_pipe.setGaussRadius(self.in2_radiusSpinBox.value())
      self.in2_pipe.setIsosurface(self.in2_isosurfaceSpinBox.value())
    else:
      return
    
  def createPipeline(self, _filename, pipeline):
    # Remove any existing pipelines before creating a new one
    if (pipeline == "in1"):
      if (self.in1_pipe != None):
        self.renderer.RemoveActor(self.in1_pipe.getActor())
        self.pickerstyle.removePoints("in1_pipeline")
        del self.in1_pipe
        self.in1_pipe = None
      self.in1_pipe = Pipeline()
      self.in1_pipe.setActorColor(self.cp.getColour("bone1"))
      self.in1_filenameLabel.setText(os.path.basename(_filename))
      self.in1_filenameLabel.setToolTip(_filename)  
      ptr = self.in1_pipe
    elif (pipeline == "in2"):
      if (self.in2_pipe != None):
        self.renderer.RemoveActor(self.in2_pipe.getActor())
        self.pickerstyle.removePoints("in2_pipeline")
        del self.in2_pipe
        self.in2_pipe = None
      self.in2_pipe = Pipeline()
      self.in2_pipe.setActorColor(self.cp.getColour("bone2"))
      self.in2_filenameLabel.setText(os.path.basename(_filename))
      self.in2_filenameLabel.setToolTip(_filename)  
      ptr = self.in2_pipe
    else:
      return

    self.setPipelineAttributesFromGUI(pipeline)
    ptr.constructPipeline(_filename)
    ptr.addActor(self.renderer)
    self.pickerstyle.setMainActor(ptr.getActor(), (pipeline+"_pipeline"))
    self.log_window.append(ptr.getProcessingLog())
    self.log_window.append(ptr.getImageInfoLog())
    self.refreshRenderWindow()
    self.updateGUI()
    return
      
  def togglePickable(self, _state, pipeline):
    if (pipeline == "in1"):
      if (self.in1_pipe != None):
        ptr = self.in1_pipe
      else:
        return
    elif (pipeline == "in2"):
      if (self.in2_pipe != None):
        ptr = self.in2_pipe
      else:
        return
      
    # Only two states are possible
    if (qtc.Qt.CheckState.Checked == _state):
      ptr.setActorPickable(1)
      self.statusBar().showMessage("Toggling actor pickability ON",4000)
      self.refreshRenderWindow()
    else:
      ptr.setActorPickable(0)
      self.statusBar().showMessage("Toggling actor pickability OFF",4000)
      self.refreshRenderWindow()
    return  

  def toggleVisibility(self, _state, pipeline):
    if (pipeline == "in1"):
      if (self.in1_pipe != None):
        name = "in1_pipeline"
        ptr = self.in1_pipe
      else:
        return
    elif (pipeline == "in2"):
      if (self.in2_pipe != None):
        name = "in2_pipeline"
        ptr = self.in2_pipe
      else:
        return

    # Only two states are possible
    if (qtc.Qt.CheckState.Checked == _state):
      ptr.setActorVisibility(1)
      self.pickerstyle.setVisibilityOfPoints(name, 1)
      self.statusBar().showMessage("Toggling actor visibility ON",4000)
      self.refreshRenderWindow()
    else:
      ptr.setActorVisibility(0)
      self.pickerstyle.setVisibilityOfPoints(name, 0)
      self.statusBar().showMessage("Toggling actor visibility OFF",4000)
      self.refreshRenderWindow()
    return
    
  def changeSigma(self, _value, pipeline):
    if (pipeline == "in1"):
      if (self.in1_pipe != None):
        self.in1_pipe.setGaussStandardDeviation(_value)
        self.statusBar().showMessage(f"Changing standard deviation to {_value}",4000)
        self.refreshRenderWindow()
    elif (pipeline == "in2"):
      if (self.in2_pipe != None):
        self.in2_pipe.setGaussStandardDeviation(_value)
        self.statusBar().showMessage(f"Changing standard deviation to {_value}",4000)
        self.refreshRenderWindow()
    else:
      return
    return
    
  def changeRadius(self, _value, pipeline):
    if (pipeline == "in1"):
      if (self.in1_pipe != None):
        self.in1_pipe.setGaussRadius(_value)
        self.statusBar().showMessage(f"Changing radius to {_value}",4000)
        self.refreshRenderWindow()
    elif (pipeline == "in2"):
      if (self.in2_pipe != None):
        self.in2_pipe.setGaussRadius(_value)
        self.statusBar().showMessage(f"Changing radius to {_value}",4000)
        self.refreshRenderWindow()
    else:
      return
    return
    
  def changeIsosurface(self, _value, pipeline):
    if (pipeline == "in1"):
      if (self.in1_pipe != None):
        self.in1_pipe.setIsosurface(_value)
        self.statusBar().showMessage(f"Changing isosurface to {_value}",4000)
        self.refreshRenderWindow()
    elif (pipeline == "in2"):
      if (self.in2_pipe != None):
        self.in2_pipe.setIsosurface(_value)
        self.statusBar().showMessage(f"Changing isosurface to {_value}",4000)
        self.refreshRenderWindow()
    else:
      return
    return
  
  def updateCamera(self, type):
    camera = self.renderer.GetActiveCamera()
    inc = self.incrementCameraSpinBox.value()
    
    if (type == "roll"):
      camera.Roll(inc)
    if (type == "elevation"):
      camera.Elevation(inc)
    if (type == "azimuth"):
      camera.Azimuth(inc)
    
    camera.OrthogonalizeViewUp()
    self.refreshRenderWindow()
    return

  def applyLandmarkTransform(self):
    if (self.in2_pipe != None):
      in1_pts = self.pickerstyle.getNumberOfPoints("in1_pipeline")
      in2_pts = self.pickerstyle.getNumberOfPoints("in2_pipeline")
      if (in1_pts == in2_pts and in1_pts >= 3):
        lm = vtk.vtkLandmarkTransform()
        lm.SetTargetLandmarks( self.pickerstyle.getPoints("in1_pipeline") )
        lm.SetSourceLandmarks( self.pickerstyle.getPoints("in2_pipeline") )
        lm.SetModeToRigidBody()
        lm.Update()
        mat = lm.GetMatrix()
        self.in2_pipe.setRigidBodyTransformConcatenateMatrix(mat)
        self.pickerstyle.removePoints("in1_pipeline")
        self.pickerstyle.removePoints("in2_pipeline")
        self.refreshRenderWindow()
        self.updateGUI()
        self.statusBar().showMessage(f"Landmark transform complete based on {in1_pts}",4000)
      else:
        self.statusBar().showMessage("ERROR: Landmark transform could not be executed",4000)
    
  def applyICPTransform(self):
    if (self.in2_pipe != None):
      icp = vtk.vtkIterativeClosestPointTransform()
      icp.SetTarget( self.in1_pipe.getPolyData() )
      icp.SetSource( self.in2_pipe.getPolyData() )
      icp.SetMaximumNumberOfIterations( 10 )
      icp.StartByMatchingCentroidsOn()
      icp.GetInverse()
      icp.Update()
      # Concatenate the transform
      mat = icp.GetMatrix()
      self.in2_pipe.setRigidBodyTransformConcatenateMatrix(mat)
      # Clean up
      self.pickerstyle.removePoints("in1_pipeline")
      self.pickerstyle.removePoints("in2_pipeline")
      self.refreshRenderWindow()
      self.updateGUI()
      self.statusBar().clearMessage()
      self.statusBar().showMessage("ICP transform complete",4000)
    
  def resetTransform(self):
    if (self.in2_pipe != None):
      reply = qtw.QMessageBox.question(self, "Message",
        "Are you sure you want to reset the transform?", qtw.QMessageBox.StandardButton.Yes |
        qtw.QMessageBox.StandardButton.No, qtw.QMessageBox.StandardButton.Yes)
      if reply == qtw.QMessageBox.StandardButton.Yes:
        self.in2_pipe.setRigidBodyTransformToIdentity()
        self.pickerstyle.removePoints("in1_pipeline")
        self.pickerstyle.removePoints("in2_pipeline")
        self.refreshRenderWindow()
        self.updateGUI()
        self.statusBar().showMessage("Reset transform complete",4000)
    
  def toggleTransformApplied(self, _state):
    if (self.in2_pipe != None):
      if (qtc.Qt.CheckState.Checked == _state):
        self.in2_pipe.useTransform(True)
        self.statusBar().showMessage("Toggling transform ON",4000)
      else:
        self.in2_pipe.useTransform(False)
        self.statusBar().showMessage("Toggling transform OFF",4000)
      self.refreshRenderWindow()
  
  def updateMatrixGUI(self, _mat):
    precision = 3
    formatter = "{{:6.{}f}}".format(precision)
    self.mat11.setText(formatter.format(float(_mat.GetElement(0,0))))
    self.mat12.setText(formatter.format(float(_mat.GetElement(0,1))))
    self.mat13.setText(formatter.format(float(_mat.GetElement(0,2))))
    self.mat14.setText(formatter.format(float(_mat.GetElement(0,3))))
    self.mat21.setText(formatter.format(float(_mat.GetElement(1,0))))
    self.mat22.setText(formatter.format(float(_mat.GetElement(1,1))))
    self.mat23.setText(formatter.format(float(_mat.GetElement(1,2))))
    self.mat24.setText(formatter.format(float(_mat.GetElement(1,3))))
    self.mat31.setText(formatter.format(float(_mat.GetElement(2,0))))
    self.mat32.setText(formatter.format(float(_mat.GetElement(2,1))))
    self.mat33.setText(formatter.format(float(_mat.GetElement(2,2))))
    self.mat34.setText(formatter.format(float(_mat.GetElement(2,3))))
    self.mat41.setText(formatter.format(float(_mat.GetElement(3,0))))
    self.mat42.setText(formatter.format(float(_mat.GetElement(3,1))))
    self.mat43.setText(formatter.format(float(_mat.GetElement(3,2))))
    self.mat44.setText(formatter.format(float(_mat.GetElement(3,3))))
    return

  def updateVectorsGUI(self):
    if (self.in2_pipe == None):
      return
    converter = ScancoMatrixConverter()
    mat = self.in2_pipe.getMatrix()
    converter.setDimImage1(self.in1_pipe.getDimensions())
    converter.setDimImage2(self.in2_pipe.getDimensions())
    converter.setPosImage1(self.in1_pipe.getPosition())
    converter.setPosImage2(self.in2_pipe.getPosition())
    converter.setElSizeMMImage1(self.in1_pipe.getElementSize())
    converter.setElSizeMMImage2(self.in2_pipe.getElementSize())
    converter.setTransform(mat)
    converter.calculateVectors()
    
    rot = converter.getRotationVector()
    trans = converter.getTranslationVector()
    
    precision = 3
    formatter = "{{:6.{}f}}".format(precision)
    self.rot1.setText(formatter.format(float(rot[0])))
    self.rot2.setText(formatter.format(float(rot[1])))
    self.rot3.setText(formatter.format(float(rot[2])))
    self.trans1.setText(formatter.format(float(trans[0])))
    self.trans2.setText(formatter.format(float(trans[1])))
    self.trans3.setText(formatter.format(float(trans[2])))
    return

  def updateGUI(self):
    in1_pts = self.pickerstyle.getNumberOfPoints("in1_pipeline")
    in2_pts = self.pickerstyle.getNumberOfPoints("in2_pipeline")
    #print("There are " + str(in1_pts) + " in1 points.")
    #print("There are " + str(in2_pts) + " in2 points.")
    self.in1_points_count.display(in1_pts)
    self.in2_points_count.display(in2_pts)
    if (in1_pts == in2_pts and in1_pts >= 3):
      self.landmarkTransformPushButton.setEnabled(True)
    else:
      self.landmarkTransformPushButton.setEnabled(False)
    if (self.in1_pipe != None):
      self.in2_mainGroupBox.setEnabled(True)  # activate GUI for in2_pipeline
      self.in1_sigmaSpinBox.setValue(self.in1_pipe.getGaussStandardDeviation())
      self.in1_radiusSpinBox.setValue(self.in1_pipe.getGaussRadius())
      self.in1_isosurfaceSpinBox.setValue(self.in1_pipe.getIsosurface())
    if (self.in2_pipe != None):
      self.updateMatrixGUI(self.in2_pipe.getMatrix())
      self.updateVectorsGUI()
      self.in2_sigmaSpinBox.setValue(self.in2_pipe.getGaussStandardDeviation())
      self.in2_radiusSpinBox.setValue(self.in2_pipe.getGaussRadius())
      self.in2_isosurfaceSpinBox.setValue(self.in2_pipe.getIsosurface())
    return
    
  def keyEventDetected(self,obj,event):
    self.updateGUI()
    key = self.vtkWidget.GetKeySym()
    if (key in 'p') or (key in 'd'): # pick or delete points
      self.log_window.append(self.pickerstyle.getPointActionString())
    # print("keypress – clicked "+key)
    return
  
  def mouseEventDetected(self,obj,event):
    print("mouserelease – click!")
    return
  
  def validExtension(self, extension):
    if (extension == ".aim" or \
        extension == ".nii" or \
        extension == ".nii.gz" or \
        extension == ".dcm" or \
        extension == ".stl"):
      return True
    else:
      return False
      
  def openFile(self, pipeline_name):
    if (pipeline_name == "in2" and self.in1_pipe == None):
      qtw.QMessageBox.warning(self, "Warning", "Image 2 cannot be loaded before image 1.")
      return

    self.statusBar().showMessage("Load image types (.aim, .nii, .dcm)",4000)
    filename, _ = qtw.QFileDialog.getOpenFileName(
      self,
      "Select a 3D image file to open…",
      self.default_path,
      "Aim Files (*.aim) ;;Nifti Files (*.nii) ;;DICOM Files (*.dcm) ;;STL Files (*.stl) ;;All Files (*)",
      "All Files (*)",
      qtw.QFileDialog.Option.DontUseNativeDialog |
      qtw.QFileDialog.Option.DontResolveSymlinks
    )
    self.default_path = qtc.QFileInfo(filename).path()
    
    if filename:
      _,ext = os.path.splitext(filename)
      if 'gz' in ext:
        ext = '.nii' + ext
      
      if not (self.validExtension(ext.lower())):
        qtw.QMessageBox.warning(self, "Error", "Invalid file type.")
        return
      
      self.createPipeline(filename, pipeline_name)
      self.statusBar().showMessage("Loading file " + filename,4000)
    return

  def saveLogFile(self):
    filename, _ = qtw.QFileDialog.getSaveFileName(
      self,
      "Select the file to save to…",
      qtc.QDir.homePath(),
      "Text Files (*.txt) "
    )
    if filename:
      try:
        with open(filename, 'w') as fh:
          fh.write(self.log_window.toPlainText())
      except Exception as e:
        qtw.QMessageBox.critical(self, f"Could not save file: {e}")

  def savePointsFile(self):
    filename, _ = qtw.QFileDialog.getSaveFileName(
      self,
      "Select the file to save to…",
      qtc.QDir.homePath(),
      "Text Files (*.txt) ;;Python Files (*.py) ;;All Files (*)"
    )
    if filename:
      try:
        with open(filename, 'w') as fh:
          fh.write(self.pickerstyle.getAllPointsAsString())
      except Exception as e:
        qtw.QMessageBox.critical(self, f"Could not save file: {e}")

  def saveTransformFile(self,type):
    
    converter = ScancoMatrixConverter()

    if (self.in2_pipe == None):
      mat = vtk.vtkMatrix4x4()
      converter.setDimImage1(self.in1_pipe.getDimensions())
      converter.setPosImage1(self.in1_pipe.getPosition())
      converter.setElSizeMMImage1(self.in1_pipe.getElementSize())
      converter.setTransform(mat)
      converter.calculateVectors()
    else:
      mat = self.in2_pipe.getMatrix()
      converter.setDimImage1(self.in1_pipe.getDimensions())
      converter.setDimImage2(self.in2_pipe.getDimensions())
      converter.setPosImage1(self.in1_pipe.getPosition())
      converter.setPosImage2(self.in2_pipe.getPosition())
      converter.setElSizeMMImage1(self.in1_pipe.getElementSize())
      converter.setElSizeMMImage2(self.in2_pipe.getElementSize())
      converter.setTransform(mat)
      converter.calculateVectors()
    
    filename, _ = qtw.QFileDialog.getSaveFileName(
      self,
      "Select the file to save to…",
      qtc.QDir.homePath(),
      "Text Files (*.txt) ;;Python Files (*.py) ;;All Files (*)"
    )
    if filename:
      try:
        with open(filename, 'w') as fh:
          s = ""
          if (type == "matrix"):
            s += converter.getTransformAsString()
          if (type == "vector"):
            s += converter.getVectorsAsString()
          fh.write(s)
      except Exception as e:
        qtw.QMessageBox.critical(self, f"Could not save file: {e}")
    
  def quit(self):
    reply = qtw.QMessageBox.question(self, "Message",
      "Are you sure you want to quit?", qtw.QMessageBox.StandardButton.Yes |
      qtw.QMessageBox.StandardButton.No, qtw.QMessageBox.StandardButton.Yes)
    if reply == qtw.QMessageBox.StandardButton.Yes:
      exit(0)

  def about(self):
    about = qtw.QMessageBox(self)
    about.setWindowIcon(qtg.QIcon('/bonelab/gui/src/icon.png'))
    about.setIcon(qtw.QMessageBox.Icon.Information)
    about.setText("blQtViewer 1.0")
    about.setInformativeText("Copyright (C) 2020\nBone Imaging Laboratory\nAll rights reserved.\nbonelab@ucalgary.ca")
    about.setStandardButtons(qtw.QMessageBox.StandardButton.Ok | qtw.QMessageBox.StandardButton.Cancel)
    about.exec_()

  def extrudeFromPoints(self):

    pts = self.pickerstyle.getPoints("in1_pipeline")

    if (pts.GetNumberOfPoints() < 3):
      qtw.QMessageBox.warning(self, "Warning", "At least 3 points must be defined on image 1 to create extrusion.")
      return

    if (not self.in1_pipe.getIsValidForExtrusion()):
      qtw.QMessageBox.warning(self, "Warning", "Extrusion may not work properly when input file is not of type AIM.")
    
    # Spline
    spline = vtk.vtkParametricSpline()
    spline.SetPoints(pts)
    spline.ClosedOn()
    
    parametricFunction = vtk.vtkParametricFunctionSource()
    parametricFunction.SetParametricFunction(spline)
    parametricFunction.Update()
    
    # Extrude
    extrusionFactor = 100.0 # mm above and below surface
                            # A large number will cause the extrusion to fill the extent of the input image

    positiveExtruder = vtk.vtkLinearExtrusionFilter()
    positiveExtruder.SetInputConnection(parametricFunction.GetOutputPort())
    positiveExtruder.SetExtrusionTypeToNormalExtrusion()
    positiveExtruder.SetVector(0, 0, 1)
    positiveExtruder.CappingOn()
    positiveExtruder.SetScaleFactor(extrusionFactor)

    posTriFilter = vtk.vtkTriangleFilter()
    posTriFilter.SetInputConnection(positiveExtruder.GetOutputPort())
    
    negativeExtruder = vtk.vtkLinearExtrusionFilter()
    negativeExtruder.SetInputConnection(parametricFunction.GetOutputPort())
    negativeExtruder.SetExtrusionTypeToNormalExtrusion()
    negativeExtruder.SetVector(0, 0, -1)
    negativeExtruder.CappingOn()
    negativeExtruder.SetScaleFactor(extrusionFactor)
    
    negTriFilter = vtk.vtkTriangleFilter()
    negTriFilter.SetInputConnection(negativeExtruder.GetOutputPort())
    
    # Combine data
    combiner = vtk.vtkAppendPolyData()
    combiner.AddInputConnection(posTriFilter.GetOutputPort())
    combiner.AddInputConnection(negTriFilter.GetOutputPort())
    
    cleaner = vtk.vtkCleanPolyData()
    cleaner.SetInputConnection(combiner.GetOutputPort())
    cleaner.Update()
    
    el_size_mm = self.in1_pipe.getElementSize()
    dim = self.in1_pipe.getDimensions()
    extent = self.in1_pipe.getExtent()
    origin = self.in1_pipe.getOrigin()
    foregroundValue = 127
    backgroundValue = 0
    
    # Stencil
    whiteImage = vtk.vtkImageData()
    whiteImage.SetSpacing(el_size_mm)
    whiteImage.SetDimensions(dim)
    whiteImage.SetExtent(extent)
    whiteImage.SetOrigin(origin)
    whiteImage.AllocateScalars(vtk.VTK_CHAR,1)
    whiteImage.GetPointData().GetScalars().Fill(foregroundValue)
    
    # Use our extruded polydata to stencil the solid image
    poly2sten = vtk.vtkPolyDataToImageStencil()
    poly2sten.SetTolerance(0)
    #poly2sten.SetInputConnection(clipper.GetOutputPort())
    poly2sten.SetInputConnection(cleaner.GetOutputPort())
    poly2sten.SetOutputOrigin( origin )
    poly2sten.SetOutputSpacing( el_size_mm )
    poly2sten.SetOutputWholeExtent( whiteImage.GetExtent() )
    
    stencil = vtk.vtkImageStencil()
    stencil.SetInputData(whiteImage)
    stencil.SetStencilConnection(poly2sten.GetOutputPort())
    #stencil.ReverseStencilOff()
    stencil.SetBackgroundValue(backgroundValue)
    stencil.Update()

    # Write image
    filename, _ = qtw.QFileDialog.getSaveFileName(
      self,
      "Select the file to save to…",
      qtc.QDir.homePath(),
      "AIM File (*.aim)"
    )
    
    if (filename):
      writer = vtkbone.vtkboneAIMWriter()
      writer.SetInputConnection(stencil.GetOutputPort())
      writer.SetFileName(filename)
      writer.SetProcessingLog('!-------------------------------------------------------------------------------\n'+'Written by blQtViewer.')
      writer.Update()
      self.statusBar().showMessage("File " + filename + " written.",4000)
    
    
   