$! ## ==============================================================================
$! ##    Create ROIs for Cartilage and Subchondral Compact Bone
$! ## ==============================================================================
$! ## This script created the weight bearing ROIs for the cartilage and subchondral
$! ## compact bone (after the actual ROI has been created in blSurfaceViewer)
$! ##
$! ## Author: Jenn Bhatla, 2016 Updated July 2, 2017
$! ## ------------------------------------------------------------------------------
$! ##    Input parameters and output
$! ## ------------------------------------------------------------------------------
$! ##
$! ## Input #1: Segmented Cartilage gobj
$! ## Input #2: Segmented Subchondral Compact Bone
$! ## Input #3: Lateral ROI
$! ## Input #4: Medial ROI
$! ##
$! ## Output #1: Lateral Subchondral Compact bone ROI
$! ## Output #2: Lateral cartilage ROI
$! ## Output #3: Medial Subchondral Compact bone ROI
$! ## Output #4: Medial cartilage ROI
$! ##
$! ## Note: for the PrE-OA Study this script was run after the IPL_CARTILAGE_SMOOTHING_FEMUR.COM and after ROIs have been generated
$! ## ------------------------------------------------------------------------------
$! ##    START OF CODE
$! ## ------------------------------------------------------------------------------
$!
$! SUBMIT/QUEUE=SYS$FAST/NOPRINT/NONOTIFY/PRIORITY=100/LOG=SYS$SCRATCH: DISK4:[BONELAB.PROJECTS.PREOA.COM]IPL_CARTILAGE_ROIS.COM
$!
$    MRI_IMAGE = P1
$    XCT_IMAGE = P2
$    REGISTERED = P3
$
$   FILENAME_MR = F$PARSE("''MRI_IMAGE'",,,"NAME")
$   FILENAME_CT = F$PARSE("''XCT_IMAGE'",,,"NAME")
$   FILENAME_REG = F$PARSE("''REGISTERED'",,,"NAME")
$
$   DEV_READ = F$PARSE("''MRI_IMAGE'",,,"DEVICE")
$   DIR_READ = F$PARSE("''MRI_IMAGE'",,,"DIRECTORY")
$   DEV_WRITE = F$PARSE("''REGISTERED'",,,"DEVICE")
$   DIR_WRITE = F$PARSE("''REGISTERED'",,,"DIRECTORY")
$
$   CARTILAGE_SEG = DEV_WRITE + DIR_WRITE + FILENAME_REG + "_FC_SEG.AIM" !Input segmented cartilage
$   BONE_SEG = DEV_WRITE + DIR_READ + FILENAME_CT + "_F_CORT.AIM" !Input segmented subchondral compact bone

$   THICKNESS_lat_Cart = DEV_WRITE + DIR_WRITE + FILENAME_REG + "_FC_THICK_LAT_REG.AIM"  !Output cartilage and bone ROIs for each region
$   THICKNESS_lat_bone = DEV_WRITE + DIR_WRITE + FILENAME_REG + "_F_THICK_LAT_REG.AIM"
$   THICKNESS_med_Cart = DEV_WRITE + DIR_WRITE + FILENAME_REG + "_FC_THICK_MED_REG.AIM"
$   THICKNESS_med_bone = DEV_WRITE + DIR_WRITE + FILENAME_REG + "_F_THICK_MED_REG.AIM"
$   ROI_LAT = DEV_READ + DIR_READ + FILENAME_REG + "_XCT_F_LAT.AIM" !Input medial and lateral ROIs
$   ROI_MED = DEV_READ + DIR_READ + FILENAME_REG + "_XCT_F_MED.AIM"
$
$   ipl_scanco_prog := $um:ipl_scanco_m.exe
$
$
$
$   ipl_scanco_prog

!CREATE Femur Lateral
/db_scanco_activate false

/read cart "CARTILAGE_SEG

/set_value
   -input                     cart
   -value_object              82
   -value_background          0

/read roi_lat "ROI_LAT

/scale_elsize
  -input                     roi_lat
  -output                    roi_lat_sca
  -down_scale                3 3 3
  -integrate                 true

/set_value
   -input                     roi_lat_sca
   -value_object              42
   -value_background          0

/add_aims
  -input1                    cart
  -input2                    roi_lat_sca
  -output                    out

/absolute_threshold
  -input                     out
  -output                    roi_cart_lat
  -lower_in_abs              124
  -upper_in_abs              124
  -grayscale_or_scaledvalues true
  -value_in_range            127

!/add_aims
!  -input1                    cart
!  -input2                    roi_lat_sca
!  -output                    out

/cl_ow_rank_extract
  -input_output              roi_cart_lat
  -first_rank                1
  -last_rank                 1
  -connect_boundary          false
  -value_in_range            127
  -topology                  6

/add_aims
  -input1                    roi_cart_lat
  -input2                    roi_lat_sca
  -output                    roi_concat

/bounding_box_cut
  -input                     roi_concat
  -output                    roi_concat_cut

/subtract_aims
  -input1                    roi_concat_cut
  -input2                    roi_lat_sca
  -output                    roi_cart_lat_bounded

/dt_thickness
  -input                     roi_cart_lat_bounded
  -output                    thickness_lat_Cart

/write thickness_lat_Cart "THICKNESS_lat_Cart


!!! Now for Bone
/read bone "BONE_SEG

/scale_elsize
  -input                     bone
  -output                    bone_sca
  -down_scale                3 3 3
  -integrate                 true

/set_value
   -input                     bone_sca
   -value_object              82
   -value_background          0

/read roi_lat "ROI_LAT

/scale_elsize
  -input                     roi_lat
  -output                    roi_lat_sca
  -down_scale                3 3 3
  -integrate                 true

/set_value
   -input                     roi_lat_sca
   -value_object              42
   -value_background          0

/add_aims
  -input1                    bone_sca
  -input2                    roi_lat_sca
  -output                    out

/absolute_threshold
  -input                     out
  -output                    roi_bone_lat
  -lower_in_abs              124
  -upper_in_abs              124
  -grayscale_or_scaledvalues true
  -value_in_range            127


/cl_ow_rank_extract
  -input_output              roi_bone_lat
  -first_rank                1
  -last_rank                 1
  -connect_boundary          false
  -value_in_range            127
  -topology                  6

/add_aims
  -input1                    roi_bone_lat
  -input2                    roi_lat_sca
  -output                    roi_concat

/bounding_box_cut
  -input                     roi_concat
  -output                    roi_concat_cut

/subtract_aims
  -input1                    roi_concat_cut
  -input2                    roi_lat_sca
  -output                    roi_bone_lat_bounded

/dt_thickness
  -input                     roi_bone_lat_bounded
  -output                    thickness_lat_bone

/write thickness_lat_bone "THICKNESS_lat_bone
!CREATE Femur Medial
/db_scanco_activate false

/read cart "CARTILAGE_SEG

/set_value
   -input                     cart
   -value_object              82
   -value_background          0

/read roi_med "ROI_med

/scale_elsize
  -input                     roi_med
  -output                    roi_med_sca
  -down_scale                3 3 3
  -integrate                 true

/set_value
   -input                     roi_med_sca
   -value_object              42
   -value_background          0

/add_aims
  -input1                    cart
  -input2                    roi_med_sca
  -output                    out

/absolute_threshold
  -input                     out
  -output                    roi_cart_med
  -lower_in_abs              124
  -upper_in_abs              124
  -grayscale_or_scaledvalues true
  -value_in_range            127

/cl_ow_rank_extract
  -input_output              roi_cart_med
  -first_rank                1
  -last_rank                 1
  -connect_boundary          false
  -value_in_range            127
  -topology                  6

/add_aims
  -input1                    roi_cart_med
  -input2                    roi_med_sca
  -output                    roi_concat

/bounding_box_cut
  -input                     roi_concat
  -output                    roi_concat_cut

/subtract_aims
  -input1                    roi_concat_cut
  -input2                    roi_med_sca
  -output                    roi_cart_med_bounded

/dt_thickness
  -input                     roi_cart_med_bounded
  -output                    thickness_med_Cart

/write thickness_med_Cart "THICKNESS_med_Cart
..
$   ipl_scanco_prog
!!! Now for Bone
/read bone "BONE_SEG

/scale_elsize
  -input                     bone
  -output                    bone_sca
  -down_scale                3 3 3
  -integrate                 true

/set_value
   -input                     bone_sca
   -value_object              82
   -value_background          0

/read roi_med "ROI_med

/scale_elsize
  -input                     roi_med
  -output                    roi_med_sca
  -down_scale                3 3 3
  -integrate                 true

/set_value
   -input                     roi_med_sca
   -value_object              42
   -value_background          0

/add_aims
  -input1                    bone_sca
  -input2                    roi_med_sca
  -output                    out

/absolute_threshold
  -input                     out
  -output                    roi_bone_med
  -lower_in_abs              124
  -upper_in_abs              124
  -grayscale_or_scaledvalues true
  -value_in_range            127


/cl_ow_rank_extract
  -input_output              roi_bone_med
  -first_rank                1
  -last_rank                 1
  -connect_boundary          false
  -value_in_range            127
  -topology                  6


/add_aims
  -input1                    roi_bone_med
  -input2                    roi_med_sca
  -output                    roi_concat

/bounding_box_cut
  -input                     roi_concat
  -output                    roi_concat_cut

/subtract_aims
  -input1                    roi_concat_cut
  -input2                    roi_med_sca
  -output                    roi_bone_med_bounded

/dt_thickness
  -input                     roi_bone_med_bounded
  -output                    thickness_med_bone

/write thickness_med_bone "THICKNESS_med_bone
..

$
$
$
$
$
$ EXIT
