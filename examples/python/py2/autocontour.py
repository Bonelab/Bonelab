import ipl_module
import sys
import argparse
import vtk
import vtkn88
import os
import re
import time

#start = time.time()

input = ipl_module.input
border = ipl_module.border
first_rank = ipl_module.first_rank
last_rank = ipl_module.last_rank
lower_fract = ipl_module.lower_fract
upper_fract = ipl_module.upper_fract
value_in = ipl_module.value_in
boundary = ipl_module.boundary
dilate_distance = ipl_module.dilate_distance
erode_distance = ipl_module.erode_distance
lower = ipl_module.lower
upper = ipl_module.upper
value_in_range = ipl_module.value_in_range
peel_iter = ipl_module.peel_iter
open = ipl_module.open
value_object = ipl_module.value_object
value_background = ipl_module.value_background
sigma = ipl_module.sigma
support = ipl_module.support

#Filenames

ORIGAIM_FILENAME = os.path.basename(input)

temp = ORIGAIM_FILENAME.split(".")
ORIG_FILENAME = temp[0]

BONEMASK_FILENAME = ORIG_FILENAME + "_BONE_MASK_PY.AIM"
TRABMASK_FILENAME = ORIG_FILENAME + "_TRAB_MASK_PY.AIM"
CORTMASK_FILENAME = ORIG_FILENAME + "_CORT_MASK_PY.AIM"

INVTRAB_FILENAME = ORIG_FILENAME + "_TRAB_INV_PY.AIM"

help1 = ORIG_FILENAME + "_BONE_HELP1_PY.AIM"
help2 = ORIG_FILENAME + "_BONE_HELP2_PY.AIM"
help3 = ORIG_FILENAME + "_BONE_HELP3_PY.AIM"
help4 = ORIG_FILENAME + "_BONE_HELP4_PY.AIM"
help5 = ORIG_FILENAME + "_BONE_HELP5_PY.AIM"
help6 = ORIG_FILENAME + "_BONE_HELP6_PY.AIM"

print help1

image_in = ipl_module.ipl_read( input )

ipl_module.ipl_examine_geometry( image_in )

#===============================================
# STEP 1: Extract Periosteal Surface
#===============================================

# Bounding box cut
box = ipl_module.ipl_bounding_box_cut( image_in, [4,4,2])

# Offset mirror
mirror = ipl_module.ipl_add_offset_mirror( box, [0,0,2])

# Gauss filter
gauss1 = ipl_module.ipl_gauss_lp( mirror,  1.2, support )

# Global threshold
thres1 = ipl_module.ipl_threshold( gauss1, lower, upper, value_in_range )

# Component labeling
cl1 = ipl_module.ipl_cl_rank_extract( thres1,  first_rank, last_rank )
ipl_module.ipl_examine_geometry( cl1 )

ipl_module.ipl_write( cl1, help1)

# Dilation
dilate1 = ipl_module.ipl_dilation( cl1, dilate_distance, [0,0,1] )
ipl_module.ipl_examine_geometry( dilate1 )

ipl_module.ipl_write( dilate1, help2)

# Invert1
invert1 = ipl_module.ipl_set_value(dilate1, 0, 127)

# Connectivity
connect1 = ipl_module.ipl_cl_slicewise_extract(invert1, lower_fract, upper_fract, value_in) 

# Invert2
invert2 = ipl_module.ipl_set_value(connect1, 0, 127)

# Erosion
erode1 = ipl_module.ipl_erosion( invert2 , erode_distance)
ipl_module.ipl_examine_geometry( erode1 )

ipl_module.ipl_write( erode1, BONEMASK_FILENAME)

#===============================================
# STEP 2: Extract Endosteal Surface
#===============================================

# Gauss filter
gauss2 = ipl_module.ipl_gauss_lp( mirror,  1.2, support )

# Global threshold
thres2 = ipl_module.ipl_threshold( gauss2, lower, upper, value_in_range )

# Copy
step1 = thres2

# Blank
solid = ipl_module.ipl_set_value( step1 , 127, 127)

# Mask
mask1 = ipl_module.ipl_maskaimpeel( solid, erode1, 0 )

# Invert3
invert3 = ipl_module.ipl_set_value(mask1, 0, 127)

# Add aims
add = ipl_module.ipl_add_aims( invert3 , thres2 )

# Invert4
invert4 = ipl_module.ipl_set_value(add, 0, 127)
ipl_module.ipl_examine_geometry( invert4 )

ipl_module.ipl_write( invert4, help3)

# Open
open = ipl_module.ipl_open( invert4, 1 )

# Component labeling
cl2 = ipl_module.ipl_cl_rank_extract( open,  1, 2 )
ipl_module.ipl_examine_geometry( cl2 )

ipl_module.ipl_write( cl2, help4 )

# Dilation
dilate2 = ipl_module.ipl_dilation( cl2, 5, [0,0,1] )

# Invert5
invert5 = ipl_module.ipl_set_value( dilate2 , 0, 127)

# Connectivity
connect2 = ipl_module.ipl_cl_slicewise_extract(invert5, lower_fract, upper_fract, value_in) 

# Invert6
invert6 = ipl_module.ipl_set_value( connect2 , 0, 127)
ipl_module.ipl_examine_geometry( invert6 )

box2 = ipl_module.ipl_bounding_box_cut( invert6, [1,1,1])

ipl_module.ipl_write( box2 , help5 )

# Erosion
erode2 = ipl_module.ipl_erosion( box2 , 5)
ipl_module.ipl_examine_geometry( erode2 )

box3 = ipl_module.ipl_add_offset_mirror(erode2, [1,1,1])

ipl_module.ipl_write( box3, help6 )

# Median Filter
median = ipl_module.ipl_median_filter( box3, 1 )

ipl_module.ipl_write( median, TRABMASK_FILENAME)

#===============================================
# STEP 3: Generate Cortical Mask With Boundary
#===============================================

# Mask 2
mask2 = ipl_module.ipl_maskaimpeel( solid, median, 0 )

#Invert 7
invert7 = ipl_module.ipl_set_value(mask2, 0, 127)
ipl_module.ipl_examine_geometry( invert7 )

ipl_module.ipl_write( invert7, INVTRAB_FILENAME )

# Mask 3
mask3 = ipl_module.ipl_maskaimpeel( erode1, invert7, 0)

ipl_module.ipl_write( mask3, "mask.aim" )

box3 = ipl_module.ipl_bounding_box_cut( mask3, [-2.5,-5,0])

ipl_module.ipl_write( box3, CORTMASK_FILENAME )


quit()

#end = time.time()
#print end - start

quit()