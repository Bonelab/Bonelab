#---------------------------------------------------------------
# Copyright (C) 2020 Bone Imaging Laboratory
# All rights reserved.
# bonelab@ucalgary.ca
#---------------------------------------------------------------
# Created December 4, 2020
# Steven Boyd
#---------------------------------------------------------------
# This class implements all the features of a VTK pipeline and
# is designed to accomodate reading of polygon data or image
# data. It stores a copy of the transform that the defines
# for retrieval.
#---------------------------------------------------------------

import os
import sys
import vtk
import vtkbone
from vtk.util.numpy_support import vtk_to_numpy
import numpy as np

from bonelab.io.vtk_helpers import get_vtk_reader

class Pipeline():
  """A class that defines the imaging VTK pipeline"""
  def __init__(self, parent=None):
    
    # Defaults
    self.filename = ""
    self.gaussStandardDeviation = 1.2
    self.gaussRadius = 2
    self.magnification = 1
    self.isosurface = 1
    self.actorColor = [1.000, 0.000, 0.000]
    self.actorOpacity = 1.0
    self.actorVisibility = 1
    self.actorPickable = 1
    
    self.pipelineType = "MarchingCubes" # In the future we could define other types of pipelines
    self.pipelineDataType = None
    self.actorAdded = False
    
    self.processing_log = None
    self.image_info = None
    
    # Elements of the VTK pipeline
    self.reader = None
    self.gauss = vtk.vtkImageGaussianSmooth()
    self.pad = vtk.vtkImageConstantPad()
    self.resampler = vtk.vtkImageResize()
    self.marchingCubes = vtk.vtkImageMarchingCubes()
    self.mapper = vtk.vtkPolyDataMapper()
    self.mapperDS = vtk.vtkDataSetMapper()
    self.actor = vtk.vtkActor()
    self.transformPolyData = vtk.vtkTransformPolyDataFilter()
    
    # The vtkTransform is part of the pipeline. The matrix defines the vtkTransform, but we
    # store a copy in self.matrix for retrieval later.
    self.rigidBodyTransform = vtk.vtkTransform()
    self.rigidBodyTransform.Identity()
    self.rigidBodyTransform.PostMultiply() # Important so that transform concatenation is correct!

    self.matrix = vtk.vtkMatrix4x4()
    self.dim = [1,1,1]
    self.pos = [0,0,0]
    self.el_size_mm = [0.082,0.082,0.082]
    self.extent = [0,1,0,1,0,1]
    self.origin = [0,0,0]
    self.validForExtrusion = False
    
  ########################################
  # Initialize Pipeline when we read a file  
  ########################################
  def constructPipeline(self, _filename):
    self.filename = _filename
    if self.filename.lower().endswith(".stl"):
      self.reader = vtk.vtkSTLReader()
      self.pipelineType = "PolyData"
      self.pipelineDataType = "PolyData"
    else:  
      self.reader = get_vtk_reader(self.filename)
      self.pipelineDataType = "ImageData"
      
    if self.reader is None:
        os.sys.exit("[ERROR] Cannot find reader for file \"{}\"".format(self.filename))
    self.reader.SetFileName(self.filename)
    self.reader.Update()
    
    if self.pipelineDataType == "ImageData":
      self.setImageDataInfoLog(self.reader.GetOutput())
    elif self.pipelineDataType == "PolyData":
      self.setPolyDataInfoLog(self.reader.GetOutput())
    else:
      print("ERROR: Unknown data type.")
      exit(0)
    
    # Capture the log file if it exists
    if (self.reader.GetClassName() == "vtkboneAIMReader"):
      self.processing_log = self.reader.GetProcessingLog()
      self.dim = self.reader.GetOutput().GetDimensions()
      self.pos = self.reader.GetPosition()
      self.el_size_mm = self.reader.GetElementSize()
      self.extent = self.reader.GetOutput().GetExtent()
      self.origin = self.reader.GetOutput().GetOrigin()
      self.validForExtrusion = True
    else:
      self.processing_log = "No processing log available."
      
    # If the input file is a .stl then start a different pipeline
    
    # Set up the pipeline
    if self.pipelineType == "MarchingCubes":
      
      # Gaussian smoothing
      self.gauss.SetStandardDeviation(self.gaussStandardDeviation, self.gaussStandardDeviation, self.gaussStandardDeviation)
      self.gauss.SetRadiusFactors(self.gaussRadius, self.gaussRadius, self.gaussRadius)
      self.gauss.SetInputConnection(self.reader.GetOutputPort())
      
      # Padding 
      image_extent = self.reader.GetOutput().GetExtent()
      self.pad.SetConstant(0)
      self.pad.SetOutputWholeExtent(image_extent[0]-1,image_extent[1]+1,
                                    image_extent[2]-1,image_extent[3]+1,
                                    image_extent[4]-1,image_extent[5]+1)
      self.pad.SetInputConnection(self.gauss.GetOutputPort())
      
      # Image Resize
      self.resampler.SetResizeMethodToMagnificationFactors()
      self.resampler.SetMagnificationFactors(self.magnification, self.magnification, self.magnification)
      self.resampler.BorderOn()
      self.resampler.SetInputConnection(self.pad.GetOutputPort())
      
      # Marching Cubes
      self.marchingCubes.SetInputConnection(self.resampler.GetOutputPort())
      self.marchingCubes.ComputeGradientsOn()
      self.marchingCubes.ComputeNormalsOn()
      self.marchingCubes.ComputeScalarsOff()
      self.marchingCubes.SetNumberOfContours(1)
      self.marchingCubes.SetValue(0, self.isosurface)
      
      # Transform
      self.transformPolyData.SetInputConnection(self.marchingCubes.GetOutputPort())
      self.transformPolyData.SetTransform(self.rigidBodyTransform)
      
      # Set mapper for image data
      self.mapper.SetInputConnection(self.transformPolyData.GetOutputPort())
      
      # Actor
      self.actor.SetMapper(self.mapper)
      self.actor.GetProperty().SetOpacity(self.actorOpacity)
      self.actor.GetProperty().SetColor(self.actorColor)
      self.actor.SetVisibility(self.actorVisibility)
      self.actor.SetPickable(self.actorPickable)
      
    elif self.pipelineType == "PolyData":
      
      # Transform
      self.transformPolyData.SetInputConnection(self.reader.GetOutputPort())
      self.transformPolyData.SetTransform(self.rigidBodyTransform)
      
      # Set mapper for dataset
      self.mapperDS = vtk.vtkDataSetMapper()
      self.mapperDS.SetInputConnection(self.transformPolyData.GetOutputPort())
      
      # Actor
      self.actor.SetMapper(self.mapperDS)
      self.actor.GetProperty().SetOpacity(self.actorOpacity)
      self.actor.GetProperty().SetColor(self.actorColor)
      self.actor.SetVisibility(self.actorVisibility)
      self.actor.SetPickable(self.actorPickable)
      
    else:
      print("ERROR: No appropriate pipeline!")
      exit(0)
      
  def setImageDataInfoLog(self, _im):
    array = vtk_to_numpy(_im.GetPointData().GetScalars()).ravel()
    zero_els = np.count_nonzero(array==0)
    dim = _im.GetDimensions()
    el_size_mm = _im.GetSpacing()
    origin = _im.GetOrigin()
    phys_dim = [x*y for x,y in zip(dim, el_size_mm)]
    ncells = _im.GetNumberOfCells()
    npoints = _im.GetNumberOfPoints()
    bv = (npoints-zero_els) * el_size_mm[0] * el_size_mm[1] * el_size_mm[2]
    tv = phys_dim[0] * phys_dim[1] * phys_dim[2]
    bvtv = bv/tv*100.0 # This isn't accurate for data that is not 'char' type
    
    log = ""
    guard = "!-------------------------------------------------------------------------------\n"
    log = log + guard
    log = log + "!> dim                            {: >6}  {: >6}  {: >6}\n".format(dim[0],dim[1],dim[2])
    log = log + "!> origin                         {:.4f}  {:.4f}  {:.4f}\n".format(origin[0],origin[1],origin[2])
    log = log + "!> element size in mm             {:.4f}  {:.4f}  {:.4f}\n".format(el_size_mm[0],el_size_mm[1],el_size_mm[2])
    log = log + "!> phys dim in mm                 {:.4f}  {:.4f}  {:.4f}\n".format(phys_dim[0],phys_dim[1],phys_dim[2])
    log = log + "!>\n"
    log = log + "!> data type                      {}\n".format(_im.GetScalarTypeAsString())
    log = log + "!> number of cells                {: >6}\n".format(ncells)
    log = log + "!> number of points               {: >6}\n".format(npoints)
    log = log + "!> volume (BV, TV, BV/TV)         {:.4f}  {:.4f}  {:.3f}%\n".format(bv,tv,bvtv)
    log = log + "!>\n"
    log = log + "!> Max                            {:.4f}\n".format(array.max())
    log = log + "!> Min                            {:.4f}\n".format(array.min())
    log = log + "!> Mean                           {:.4f}\n".format(array.mean())
    log = log + "!> SD                             {:.4f}\n".format(array.std())
    log = log + guard
    
    self.image_info = log

  def setPolyDataInfoLog(self, _pd):
    bounds = _pd.GetBounds()
    ncells = _pd.GetNumberOfCells()
    npoints = _pd.GetNumberOfPoints()
    
    log = ""
    guard = "!-------------------------------------------------------------------------------\n"
    log = log + guard
    log = log + "!> bounds (x_min, y_min, z_min)   {:.4f}  {:.4f}  {:.4f}\n".format(bounds[0],bounds[2],bounds[4])
    log = log + "!>        (x_max, y_max, z_max)   {:.4f}  {:.4f}  {:.4f}\n".format(bounds[1],bounds[3],bounds[5])
    log = log + "!>\n"
    log = log + "!> number of cells                {: >6}\n".format(ncells)
    log = log + "!> number of points               {: >6}\n".format(npoints)
    log = log + guard
    
    self.image_info = log

  def getImageInfoLog(self):
    return self.image_info
    
  def setGaussStandardDeviation(self, _gaussStandardDeviation):
    self.gaussStandardDeviation = _gaussStandardDeviation
    self.gauss.SetStandardDeviation(self.gaussStandardDeviation, self.gaussStandardDeviation, self.gaussStandardDeviation)
  
  def getGaussStandardDeviation(self):
    return self.gaussStandardDeviation
    
  def setGaussRadius(self, _gaussRadius):
    self.gaussRadius = _gaussRadius
    self.gauss.SetRadiusFactors(self.gaussRadius, self.gaussRadius, self.gaussRadius)
  
  def getGaussRadius(self):
    return self.gaussRadius
  
  def setIsosurface(self, _isosurface):
    self.isosurface = _isosurface
    self.marchingCubes.SetValue(0, self.isosurface)
  
  def getIsosurface(self):
    return self.isosurface
  
  def setActorColor(self, _actorColor):
    self.actorColor = _actorColor
    self.actor.GetProperty().SetColor(self.actorColor)

  def setActorOpacity(self, _actorOpacity):
    self.actorOpacity = _actorOpacity
    self.actor.GetProperty().SetOpacity(self.actorOpacity)
  
  def setActorVisibility(self, _actorVisibility):
    self.actorVisibility = _actorVisibility
    self.actor.SetVisibility(self.actorVisibility)

  def setActorPickable(self, _actorPickable):
    self.actorPickable = _actorPickable
    self.actor.SetPickable(self.actorPickable)
  
  def addActor(self, _renderer):
    if (not self.actorAdded):
      _renderer.AddActor(self.actor)
      self.actorAdded = True

  def getActor(self):
    return self.actor

  def getProcessingLog(self):
    return self.processing_log
    
  def getFilename(self):
    return self.filename
    
  def getPolyData(self):
    return self.transformPolyData.GetOutput()
  
  def getDimensions(self):
    return self.dim
    
  def getPosition(self):
    return self.pos
  
  def getElementSize(self):
    return self.el_size_mm
  
  def getExtent(self):
    return self.extent
  
  def getOrigin(self):
    return self.origin
  
  def getIsValidForExtrusion(self):
    return self.validForExtrusion
    
  def getMatrix(self):
    return self.matrix

  def setMatrix(self, _mat):
    self.matrix = _mat
    return
  
  def setRigidBodyTransformToIdentity(self):
    #mat = vtk.vtkMatrix4x4()
    #mat.Identity()
    #self.rigidBodyTransform.SetMatrix( mat )
    self.rigidBodyTransform.Identity()
    self.rigidBodyTransform.Update()
    #self.matrix = self.rigidBodyTransform.GetMatrix() # Keep a copy (need a deep copy?)
    self.matrix.DeepCopy( self.rigidBodyTransform.GetMatrix() )
    return
  
  def setRigidBodyTransformSetMatrix(self, _mat):
    #elements = np.ones(16)
    #for i in range(4):
    #  for j in range(4):
    #    elements[i*4+j] = _mat.GetElement(i,j)
    #
    #self.rigidBodyTransform.SetMatrix( elements )
    self.rigidBodyTransform.SetMatrix( _mat )
    self.rigidBodyTransform.Update()
    #self.matrix = self.rigidBodyTransform.GetMatrix() # Keep a copy (need a deep copy?)
    #self.matrix.DeepCopy( self.rigidBodyTransform.GetMatrix() )
    return

  def setRigidBodyTransformConcatenateMatrix(self, _mat):
    self.rigidBodyTransform.Concatenate( _mat )
    self.rigidBodyTransform.Update()
    #self.matrix = self.rigidBodyTransform.GetMatrix() # Keep a copy (need a deep copy?)
    self.matrix.DeepCopy( self.rigidBodyTransform.GetMatrix() )
    return
  
  def useTransform(self, _applyTransform):
    if (_applyTransform):
      self.rigidBodyTransform.SetMatrix( self.getMatrix() )
      #self.setRigidBodyTransformSetMatrix( self.getMatrix() )
    else:
      self.rigidBodyTransform.SetMatrix( vtk.vtkMatrix4x4() )
    self.rigidBodyTransform.Update()
