#---------------------------------------------------------------
# Copyright (C) 2020 Bone Imaging Laboratory
# All rights reserved.
# bonelab@ucalgary.ca
#---------------------------------------------------------------
# Created December 4, 2020
# Steven Boyd
#---------------------------------------------------------------
# All control of the VTK RenderWindowInteractor is controlled
# here. In particular, point picking and point deletion is 
# managed. The main GUI can get points when needed for writing
# to file.
#---------------------------------------------------------------

import os
import sys
import math
import vtk

from bonelab.gui.qtviewer.colourpalette import ColourPalette
from bonelab.gui.qtviewer.pickercollection import PickerCollection

class MyInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
#class MyInteractorStyle(vtk.vtkInteractorStyleTrackballActor):
#class MyInteractorStyle(vtk.vtkInteractorStyleTrackball):
#class MyInteractorStyle(vtk.vtkInteractorStyleSwitch):
#class MyInteractorStyle(vtk.vtkInteractorStyle):
    def __init__(self, parent=None):
      # Initialize observer
      self.AddObserver("KeyPressEvent", self.KeyPressEvent)
      
      self.in1_collection = PickerCollection()
      self.in1_collection.setCollectionName("in1_pipeline")
      self.in1_collection.setPointActorColour(ColourPalette().getColour("green"))
      
      self.in2_collection = PickerCollection()
      self.in2_collection.setCollectionName("in2_pipeline")
      self.in2_collection.setPointActorColour(ColourPalette().getColour("red"))
            
      self.activityString = "Point picker action!"
    
    def setMainActor(self, _actor, _pipeline_name):
      if (_pipeline_name == "in1_pipeline"):
        self.in1_collection.setMainActor(_actor)
      elif (_pipeline_name == "in2_pipeline"):
        self.in2_collection.setMainActor(_actor)
      else:
        return # do nothing

    def getNumberOfPoints(self, _pipeline_name):
      if (_pipeline_name == "in1_pipeline"):
        return self.in1_collection.getNumberOfPoints()
      elif (_pipeline_name == "in2_pipeline"):
        return self.in2_collection.getNumberOfPoints()
      else:
        return -1
    
    def getPoints(self, _pipeline_name):
      points = vtk.vtkPoints()
      if (_pipeline_name == "in1_pipeline"):
        for idx in range(self.in1_collection.getNumberOfPoints()):
          points.InsertNextPoint(self.in1_collection.getPoint(idx))
      elif (_pipeline_name == "in2_pipeline"):
        for idx in range(self.in2_collection.getNumberOfPoints()):
          points.InsertNextPoint(self.in2_collection.getPoint(idx))
      else:
        print("WARNING in MyInteractorStyle: No points returned.")
      return points
    
    def setVisibilityOfPoints(self, _pipeline_name, _visibility):
      if (_pipeline_name == "in1_pipeline"):
        return self.in1_collection.setPointsVisibility(_visibility)
      elif (_pipeline_name == "in2_pipeline"):
        return self.in2_collection.setPointsVisibility(_visibility)
      else:
        return # do nothing
    
    def removePoints(self, _pipeline_name):
      if (_pipeline_name == "in1_pipeline"):
        npts = self.in1_collection.getNumberOfPoints()
        for idx in range(npts):
          self.renderer.RemoveActor(self.in1_collection.getPointActor(idx))
        self.activityString = "Removed all " + str(npts) + " points from image 1.\n"
        self.InvokeEvent("UpdateEvent")
        self.in1_collection.clearPoints()
      elif (_pipeline_name == "in2_pipeline"):
        npts = self.in2_collection.getNumberOfPoints()
        for idx in range(npts):
          self.renderer.RemoveActor(self.in2_collection.getPointActor(idx))
        self.activityString = "Removed all " + str(npts) + " points from image 2.\n"
        self.InvokeEvent("UpdateEvent")
        self.in2_collection.clearPoints()
      else:
        return # do nothing
    
    def getAllPointsAsString(self):
      s = ""
      s += self.in1_collection.getAllPointsAsString()
      s += self.in2_collection.getAllPointsAsString()
      return s

    def getPointActionString(self):
      return self.activityString
        
    def KeyPressEvent(self, obj, event):
      self.iren = self.GetInteractor()
      self.renderer = self.iren.GetRenderWindow().GetRenderers().GetFirstRenderer()
      self.actorCollection = self.renderer.GetActors()
      self.actorCollection.InitTraversal()
      
      key = self.iren.GetKeySym()

      if key in 'h':
        #print("Press the \'u\' key to output actor transform matrix")
        print("Press the \'p\' key to pick a point")
        print("Press the \'d\' key to delete a point")
        #print("Press the \'a\' key for actor control mode")
        #print("Press the \'c\' key for camera control mode")
        print("Press the \'f\' key to fly to picked point")
        print("Press the \'s\' key to show surfaces")
        print("Press the \'w\' key to show wireframe")
        print("Press the \'q\' key to quit")
      
      #if key in 'c':
      #  self.iren.GetInteractorStyle().SetCurrentStyleToTrackballCamera()
      #
      #if key in 'a':
      #  self.iren.GetInteractorStyle().SetCurrentStyleToTrackballActor()
      #
      #if key in 'u':
      #  for index in range(self.actorCollection.GetNumberOfItems()):
      #    nextActor = self.actorCollection.GetNextActor()
      #    if (nextActor.GetPickable()==1):
      #      printMatrix4x4(self,nextActor.GetMatrix())
                 
      if key in 'p':
        x, y = self.iren.GetEventPosition()
      
        cellPicker = vtk.vtkCellPicker() # Try vtkPropPicker() ? 
        cellPicker.SetTolerance(0.0001)
        cellPicker.Pick(x, y, 0, self.renderer)
        
        if (cellPicker.GetPickedPositions().GetNumberOfPoints() == 0):
          return
        else:
          point = cellPicker.GetPickedPositions().GetPoint(0)
        
        if (self.in1_collection.getMainActor() == cellPicker.GetActor()):
          idx = self.in1_collection.addPoint(point)
          self.renderer.AddActor(self.in1_collection.getPointActor(idx))
          self.activityString = "Adding point " + str(idx) + " to image 1.\n" + self.in1_collection.getPointAsString(idx)
          self.InvokeEvent("UpdateEvent")
        elif (self.in2_collection.getMainActor() == cellPicker.GetActor()):
          idx = self.in2_collection.addPoint(point)
          self.renderer.AddActor(self.in2_collection.getPointActor(idx))
          self.activityString = "Adding point " + str(idx) + " to image 2.\n" + self.in2_collection.getPointAsString(idx)
          self.InvokeEvent("UpdateEvent")
        else:
          print("WARNING in MyInteractorStyle: No actor picked.")
          return # do nothing
          
        # This is an ugly way to remove the outline actor that results from picking. Must be a better way??
        actorCollection = self.renderer.GetActors()
        actorCollection.InitTraversal()
        for i in range(actorCollection.GetNumberOfItems()):
          actor = actorCollection.GetNextActor()
          if (actor.GetProperty().GetColor() == (1.0,0.0,0.0)): # The outline actor is red
            self.renderer.RemoveActor(actor)
        
        self.iren.Render()
        
        return
        
      if key in 'd':
        x, y = self.iren.GetEventPosition()
      
        cellPicker = vtk.vtkCellPicker()
        cellPicker.SetTolerance(0.00001)
        cellPicker.Pick(x, y, 0, self.renderer)
        
        if (cellPicker.GetPickedPositions().GetNumberOfPoints() == 0):
          return
        else:
          point = cellPicker.GetPickedPositions().GetPoint(0)
          
        if (self.in1_collection.getMainActor() == cellPicker.GetActor()):
          idx = self.in1_collection.getIndexOfClosestPickedPoint(point)
          if (idx<0):
            return
          self.renderer.RemoveActor(self.in1_collection.getPointActor(idx))
          self.activityString = "Removing point " + str(idx) + " from image 1.\n" + self.in1_collection.getPointAsString(idx)
          self.InvokeEvent("UpdateEvent")
          self.in1_collection.removePoint(idx)
          self.iren.Render()
        elif (self.in2_collection.getMainActor() == cellPicker.GetActor()):
          idx = self.in2_collection.getIndexOfClosestPickedPoint(point)
          if (idx<0):
            return
          self.renderer.RemoveActor(self.in2_collection.getPointActor(idx))
          self.activityString = "Removing point " + str(idx) + " from image 2.\n" + self.in2_collection.getPointAsString(idx)
          self.InvokeEvent("UpdateEvent")
          self.in2_collection.removePoint(idx)
          self.iren.Render()
        else:
          print("WARNING in MyInteractorStyle: No actor picked.")
          return # do nothing

      return
        
