#---------------------------------------------------------------
# Copyright (C) 2020 Bone Imaging Laboratory
# All rights reserved.
# bonelab@ucalgary.ca
#---------------------------------------------------------------
# Created December 4, 2020
# Steven Boyd
#---------------------------------------------------------------
# A Qt GUI-based 3D rendering tool. Used for viewing, point 
# picking and estimating 3D registration transforms.
#
# Note: Uses PyQt5, vtk8.2 and python3:
#     pyqt        5.12.3           py38hf180056_3    conda-forge
#     vtk         8.2.0          py38h19d254c_206    conda-forge
#     python      3.8.1                h5c2c468_1    conda-forge
#     n88tools    8.3.0                py38_np118    numerics88
#
# Create an environment like this:
# conda create --name bonelab --channel numerics88 \
#              --channel conda-forge python=3.8 \
#              n88tools pyqt=5.12 vtk=8
#
# Usage:
#   blQtViewer -h
#---------------------------------------------------------------
# TODO: 
# 1. Figure out how to show the bonelab logo in the About window.
# 2. Commit to GIT.
#
# KNOWN BUGS
# 1. Save:Points, Save:Transform, etc, has a problem where it
#    seems that at random times the QFileDialog is set to
#    not be enabled. Frustrating!
# 2. The part of the GUI that shows the number of picked points
#    for in1 and in2 is not reset to 0 after a transform is 
#    applied.
# 3. The following error occurs whenever I try and pick points.
#    I read that it might go away when I upgrade my version of
#    vtk8.2 to vtk9.0.
# >>> ERROR: In ../Rendering/Core/vtkHardwareSelector.cxx, line 288
# >>> vtkOpenGLHardwareSelector (0x7fbe9904a280): Color buffer depth 
# >>> must be at least 8 bit. Currently: 0, 8, 8
#
# WISH LIST
# 1. Add a new Pipeline that does 3d volume renderering
# 2. Can we make the FileMenu work in MacOS?
#---------------------------------------------------------------

from bonelab.gui.qtviewer.mainwindow import MainWindow

import sys
import math
import vtk
import vtkbone

from PyQt5 import QtWidgets as qtw

#-------------------------------------------------------------------------------
def argManager():
  import argparse
  description='''
An application for 3D image viewing, point picking and transforms.
'''
  epilog='''
Example calls could be:
$ blQtViewer
$ blQtViewer --input_file myfile
$ blQtViewer --window_size 1536 1024
'''
  # Setup argument parsing
  parser = argparse.ArgumentParser(
      formatter_class=argparse.RawTextHelpFormatter,
      prog="blQtViewer",
      description=description,
      epilog=epilog
  )
  parser.add_argument('--input_file', help='Input file {.aim, .nii, .dcm, .stl}')
  parser.add_argument('--gaussian', type=float, default=1.2, metavar='GAUSS', help='Gaussian standard deviation (default: %(default)s)')
  parser.add_argument('--radius', type=int, default=2, metavar='RADIUS', help='Gaussian radius support (default: %(default)s)')
  parser.add_argument('--isosurface', type=int, default=1, metavar='MC', help='Marching cubes isosurface (default: %(default)s)')
  
  parser.add_argument('--window_size', default=[1536,1024], nargs=2, type=int, metavar='DIM', 
                      help='Specify minimum main window size (default: %(default)s)')
  return parser.parse_args()

#-------------------------------------------------------------------------------
def main(): 
  args = argManager()
  
  app = qtw.QApplication([])
  main_window = MainWindow(**vars(args))
  sys.exit(app.exec())

if __name__ == '__main__':
    main()
