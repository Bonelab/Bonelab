import os
import sys
import math
import vtk

from bonelab.gui.qtviewer.colourpalette import ColourPalette

class PickerCollection():
  """Manages point tuples and vtkActors in a list in addition to main vtkActor"""

  def __init__(self,parent=None):
    
    self.mainActor = None
    self.pickedPoints = []
    self.pickedPointsActors = []
    self.collectionName = "none"
    self.shrinkFactor = 0.005 # size of pointActor relative to diagonal of mainActor
    self.pointActorColour = ColourPalette().getColour("green")
    
    # Format controls
    self.precision = 4
    self.delimiter=", "
    self.formatter = "{{:8.{}f}}".format(self.precision)
    
  def setCollectionName(self, _name):
    self.collectionName = _name
    return
    
  def getCollectionName(self):
    return self.collectionName
  
  # Adds the tuple as well as the point actor
  def addPoint(self, _pt):
    self.pickedPoints.append(_pt)
    self.pickedPointsActors.append(self._createPointActor(_pt))
    return (self.getNumberOfPoints()-1)
  
  # Returns the tuple
  def getPoint(self, _index):
    if (not self._inRange(_index)):
      print("ERROR in getPoint: Index {:d} is out of range.".format(_index))
      exit(0)
    return self.pickedPoints[_index]
  
  # Returns the point actor
  def getPointActor(self, _index):
    if (not self._inRange(_index)):
      print("ERROR in getPointActor: Index out of range.")
      exit(0)
    return self.pickedPointsActors[_index]
  
  # Removes the tuple as well as the point actor
  def removePoint(self, _index):
    if (not self._inRange(_index)):
      print("ERROR in removePoint: Index out of range.")
      exit(0)
    self.pickedPoints.pop(_index)
    self.pickedPointsActors.pop(_index)
    return
    
  def getNumberOfPoints(self):
    return len(self.pickedPoints)
  
  # Clears the tuples and the point actors
  def clearPoints(self):
    self.pickedPoints.clear()
    self.pickedPointsActors.clear()
    return
  
  def setPointsVisibility(self, _visibility):
    for actor in self.pickedPointsActors:
      actor.SetVisibility(_visibility)
    return
    
  def getPointAsString(self, _index):
    point = self.getPoint(_index)
    s = ""
    s += "!-- Point " + str(_index) + ": "
    s += self.delimiter.join([self.formatter.format(float(x)) for x in point])
    s += os.linesep
    return s

  def getAllPointsAsString(self):
    if (self.getNumberOfPoints() == 0):
      return ""
    s = ""
    s += "!-- Points " + \
         self.collectionName + \
         "------------------------------------------\n"
    for point in self.pickedPoints:
      entry = self.delimiter.join([self.formatter.format(float(x)) for x in point])
      s += entry
      s += os.linesep
    return s
  
  def setMainActor(self, _actor):
    self.mainActor = _actor
    return

  def getMainActor(self):
    return self.mainActor
  
  def setPointActorColour(self, _colour):
    self.pointActorColour = _colour
    return
  
  def getPointActorColour(self):
    return self.pointActorColour
  
  def getIndexOfClosestPickedPoint(self, _pt):
    index = -1
    min_distance_to_point = 1e99
    
    for idx, point in enumerate(self.pickedPoints):
      distance_to_point = self._calculateDiagonal((_pt[0],point[0],_pt[1],point[1],_pt[2],point[2],))
      #print(str(idx) + ", " + str(distance_to_point))
      if (distance_to_point < min_distance_to_point):
        min_distance_to_point = distance_to_point
        index = idx
    return index
    
  def _inRange(self, _index):
    if (_index > (self.getNumberOfPoints()-1) or _index < 0):
      return False
    else:
      return True
      
  def _calculateDiagonal(self, b):
    diag =  math.pow((b[1]-b[0]),2)
    diag += math.pow((b[3]-b[2]),2)
    diag += math.pow((b[5]-b[4]),2)
    diag = math.sqrt(diag)
    return diag
    
  def _createPointActor(self, _pt):
    bounds = self.mainActor.GetBounds()
    sphere_size = self._calculateDiagonal(bounds) * self.shrinkFactor

    sphere = vtk.vtkSphereSource()
    sphere.SetRadius(sphere_size)
    sphere.SetThetaResolution(20)
    sphere.SetPhiResolution(20)
    sphere.SetCenter(_pt)
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(sphere.GetOutputPort())
    pointActor = vtk.vtkActor()
    pointActor.PickableOff()
    pointActor.GetProperty().SetColor(self.pointActorColour)
    pointActor.SetMapper(mapper)

    return pointActor

# # Start of main test program --------------------------------------------------
# 
# main_actor = vtk.vtkActor()
# 
# p1 = (0.900, 0.760, 0.600)
# p2 = (0.890, 0.855, 0.788)
# p3 = (0.855, 0.890, 0.388)
# p4 = (1.000, 0.000, 0.000)
# p5 = (0.000, 1.000, 0.000)
# p6 = (0.000, 0.000, 1.000)
# p7 = (0.000, 1.000, 1.000)
# p8 = (0.000, 0.000, 204.0/255.0)
# p9 = (0.400, 0.500, 0.700)
# 
# print(p1)
# 
# point_list = PickerCollection()
# point_list.setMainActor(main_actor)
# point_list.setCollectionName("In1")
# point_list.setPointActorColour(ColourPalette().getColour("red"))
# point_list.addPoint(p1)
# point_list.addPoint(p2)
# point_list.addPoint(p3)
# point_list.addPoint(p4)
# point_list.addPoint(p5)
# point_list.addPoint(p6)
# point_list.addPoint(p7)
# point_list.addPoint(p8)
# point_list.addPoint(p9)
# 
# print("Point actor colour: " + str(point_list.getPointActorColour()[0]) + ", " \
#                              + str(point_list.getPointActorColour()[1]) + ", " \
#                              + str(point_list.getPointActorColour()[2]))
# print("List of points -----\n")
# print(point_list.getAllPointsAsString())
# print("Number of points is " + str(point_list.getNumberOfPoints()))
# point_list.setPointsVisibility(1)
# print("Visibility is " + str(point_list.getPointActor(3).GetVisibility()))
# #print(point_list.getPointAsString(4))
# #point_list.removePoint(2)
# #print("Number of points is " + str(point_list.getNumberOfPoints()))
# #point_list.clearPoints()
# #print("Number of points is " + str(point_list.getNumberOfPoints()))
# #print(point_list.getAllPointsAsString())
# pt = (.9,.1,.1)
# inx = point_list.getIndexOfClosestPickedPoint(pt)
# print("Closest point to [" + str(pt[0]) + ", " + str(pt[1]) + ", " + str(pt[2]) + "] is index " + str(inx))
# print(point_list.getPointAsString(inx))