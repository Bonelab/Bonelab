#---------------------------------------------------------------
# Copyright (C) 2021 Bone Imaging Laboratory
# All rights reserved.
# bonelab@ucalgary.ca
#---------------------------------------------------------------
# Created February 2, 2021
# Steven Boyd
#---------------------------------------------------------------
# A Qt GUI-based tool demonstrating the basics of integrating 
# pyqt, vtk and python.
#
# Note: Uses PyQt5, vtk8.2 and python3:
#     pyqt        5.12.3           py38hf180056_3    conda-forge
#     vtk         8.2.0          py38h19d254c_206    conda-forge
#     python      3.8.1                h5c2c468_1    conda-forge
#
# Create an environment like this:
# conda create --name bonelab --channel conda-forge python=3.8 pyqt=5.12 vtk=8
#
# Usage:
#   blQtBasic -h
#---------------------------------------------------------------

from bonelab.gui.qtbasic.mainwindow import MainWindow

import sys
import math
import vtk

from PyQt5 import QtWidgets as qtw

#-------------------------------------------------------------------------------
def argManager():
  import argparse
  description='''
An application to demonstrate PyQt5 and VTK for 3D image viewing.
'''
  epilog='''
Example calls could be:
$ blQtBasic
$ blQtBasic --input_file myfile
$ blQtBasic --window_size 1536 1024
'''
  # Setup argument parsing
  parser = argparse.ArgumentParser(
      formatter_class=argparse.RawTextHelpFormatter,
      prog="blQtViewer",
      description=description,
      epilog=epilog
  )
  parser.add_argument('--input_file', help='Input file {.nii, .dcm}')
  parser.add_argument('--gaussian', type=float, default=1.2, metavar='GAUSS', help='Gaussian standard deviation (default: %(default)s)')
  parser.add_argument('--radius', type=int, default=2, metavar='RADIUS', help='Gaussian radius support (default: %(default)s)')
  parser.add_argument('--isosurface', type=int, default=80, metavar='MC', help='Marching cubes isosurface (default: %(default)s)')
  
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
