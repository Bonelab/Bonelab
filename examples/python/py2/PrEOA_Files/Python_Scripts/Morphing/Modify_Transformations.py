import sys
import argparse
import vtk
import os
from vtk.util import numpy_support
from vtk.util.numpy_support import numpy_to_vtk, vtk_to_numpy
import numpy as np
import scipy.optimize as opt
import pylab as plt
import random as rand
from matplotlib.image import AxesImage
import scipy
from scipy import stats
from scipy import ndimage
import matplotlib.pyplot as plt
import fileinput

#Name files - just need transformation file created by elastix
dirname = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Morphed/PREOA_00"
dirname2 = "/Users/jbhatla/Documents/UofC/PrEOA/Analysis/Morphing/Thickness_Map_Morphed/PREOA_0"
file_C1 = "_L_FC_THICK_LAT_transformation.txt"
file_C2 = "_L_FC_THICK_MED_transformation.txt"
file_C3 = "_L_TC_THICK_LAT_transformation.txt"
file_C4 = "_L_TC_THICK_MED_transformation.txt"
file_C5 = "_R_FC_THICK_LAT_transformation.txt"
file_C6 = "_R_FC_THICK_MED_transformation.txt"
file_C7 = "_R_TC_THICK_LAT_transformation.txt"
file_C8 = "_R_TC_THICK_MED_transformation.txt"
file2_C1 = "_L_FC_THICK_LAT_bin.txt"
file2_C2 = "_L_FC_THICK_MED_bin.txt"
file2_C3 = "_L_TC_THICK_LAT_bin.txt"
file2_C4 = "_L_TC_THICK_MED_bin.txt"
file2_C5 = "_R_FC_THICK_LAT_bin.txt"
file2_C6 = "_R_FC_THICK_MED_bin.txt"
file2_C7 = "_R_TC_THICK_LAT_bin.txt"
file2_C8 = "_R_TC_THICK_MED_bin.txt"
sample_number = 5 #Start sample number
end = 32 #end sample number
roi_number = 1 #Roi number
while (sample_number <= end):

    while roi_number <9:
        if sample_number < 10: #Names files
            file_num_original = globals()['file_C%s' % roi_number]
            file_num_new = globals()['file2_C%s' % roi_number]
            filename = dirname + str(sample_number) + file_num_original
            filename2 = dirname + str(sample_number) + file_num_new
        else:
            file_num_original = globals()['file_C%s' % roi_number]
            file_num_new = globals()['file2_C%s' % roi_number]
            filename = dirname2 + str(sample_number) + file_num_original
            filename2 = dirname2 + str(sample_number) + file_num_new

        #Change Interpolation order (Use 1 for binary image, 3 for greyscale)
        print filename
        for i, line in enumerate(fileinput.input(filename, inplace=1)):
            sys.stdout.write(line.replace('(FinalBSplineInterpolationOrder 3)', '(FinalBSplineInterpolationOrder 1)'))  # replace intd write

        roi_number = roi_number + 1
        if roi_number ==9:
            sample_number = sample_number+1
            roi_number = 1
    print "end"
