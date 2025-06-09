#---------------------------------------------------------------
# Copyright (C) 2021 Bone Imaging Laboratory
# All rights reserved.
# bonelab@ucalgary.ca
#---------------------------------------------------------------
# Created February 2, 2021
# Steven Boyd
#
# Updated June 6, 2025 - Added support for PySide6 and VTK 9.3
#---------------------------------------------------------------
# A Qt GUI-based tool demonstrating the basics of integrating 
# pyqt, vtk and python.
#
# Note: Uses PySide6, vtk8.2 and python3:
#     pyside6     6.8.3           py312h8c66da3_0         conda-forge
#     vtk         9.3.1           qt_py312he4b582b_216    conda-forge
#     python      3.12.1          h5c2c468_1              conda-forge
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

from PySide6.QtWidgets import QApplication

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
      prog="blQtBasic",
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
  
  app = QApplication(sys.argv)
  main_window = MainWindow(**vars(args))
  main_window.show()
  sys.exit(app.exec())

if __name__ == '__main__':
    main()
