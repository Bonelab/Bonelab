#---------------------------------------------------------------
# Copyright (C) 2020 Bone Imaging Laboratory
# All rights reserved.
# bonelab@ucalgary.ca
#---------------------------------------------------------------
# Created December 4, 2020
# Steven Boyd
#---------------------------------------------------------------
# A simple class to store some commonly used colours. There is
# probably a better way to do this, but it works.
#---------------------------------------------------------------

import os
import sys
import math
import vtk

class ColourPalette():

  def __init__(self,parent=None):
    
    self.colour_dictionary = {'bone':        (0.900, 0.760, 0.600), 
                              'bone1':       (0.890, 0.855, 0.788),
                              'bone2':       (0.855, 0.890, 0.388),
                              'red':         (0.900, 0.000, 0.000),
                              'green':       (0.000, 1.000, 0.000),
                              'blue':        (0.000, 0.000, 1.000),
                              'bluegreen':   (0.000, 1.000, 1.000),
                              'scanco':      (0.000, 0.000, 204.0/255.0),
                              'background2': (0.400, 0.500, 0.700)}

  def getColour(self,name):
    if name not in self.colour_dictionary:
       print("ERROR in ColourPalette(): Invalid color name.")
       exit(0)
    return self.colour_dictionary.get(name)

    
