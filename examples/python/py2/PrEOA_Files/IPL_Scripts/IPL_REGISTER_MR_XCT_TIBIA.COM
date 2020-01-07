$! ## ==============================================================================
$! ##    Register MRI and HR-pQCT scans
$! ## ==============================================================================
$! ## This script registers and MRI and HR-pQCT Image
$! ##
$! ## Author: Jenn Bhatla, 2016 Updated July 2, 2017
$! ## ------------------------------------------------------------------------------
$! ##    Input parameters and output
$! ## ------------------------------------------------------------------------------
$! ##
$! ## Input #1: MRI Scan
$! ## Input #2: HR-pQCT Scan
$! ## Input #3: Bone Gobj for the MRI scan
$! ## Input #4: Bone Gobj for the HR-pQCT scan
$! ## Input #5: Text file of x, y, z rotations and x, y, z translations that provide an
$! ## initial guess for registration that approximatly aligns the MRI and HR-pQCT images,
$! ## this can be obtained from blSurfaceViewer
$! ##
$! ## Output #1: Concatenated image of the HR-pQCT and MRI masks
$! ## Output #2: Text file containing transformation matrix for the transformation of
$! ## the MRI scan to the HR-pQCT scan
$! ##
$! ## Note that the bone (Femur vs. Tibia) is hardcoded into the script. Ideally this
$! ## should be updated to be more robust such that any bone could be used.
$! ## ------------------------------------------------------------------------------
$! ##    START OF CODE
$! ## ------------------------------------------------------------------------------
$!
$ ipl_scanco_prog := $um:ipl_scanco_M.exe !$um:ipl_scanco_regis_V107.exe   !$ ipl_scanco_prog := $um:ipl_scanco_fe.exe
$!
$!
$ MRI = DEV_READ + DIR_READ + FILENAME_MR + "_reg.AIM" !Greyscale MRI Image
$ MR_GOBJ_T = DEV_READ + DIR_READ + FILENAME_MR + "_T.GOBJ"  ! MRI bone gobj
$!
$ XCT = DEV_READ + DIR_READ + FILENAME_CT + ".AIM" !Greyscale XCT Image
$ CT_GOBJ_T = DEV_READ + DIR_READ + FILENAME_CT + "_T.GOBJ"  !Greyscale gobj
$!
$ CONCAT_T = DEV_WRITE + DIR_WRITE + FILENAME_REG + "_T_CONCAT2.aim" !concatenated image
$ REG_FILE_T = DEV_WRITE + DIR_WRITE + FILENAME_REG + "_T_reg3.dat"  !transfromation matrix from MRI to HR-pQCT space
$ REG_PARAM = DEV_WRITE + DIR_WRITE + FILENAME_MR + "_F_reg.txt"     !Initial guess for registration in text file (this gets read in during registration). Note that the same initial guess works for the tibia as for the femur in most cases.
$!
$! Read in initial guess of rotations and translations from text file
$!
$ PIPE SEARCH 'reg_param "Rotations:" | (READ SYS$PIPE LINE ; DEFINE/JOB/NOLOG LINE_LOG &LINE)
$ rotation1 = F$ELEMENT(1, " ", F$TRNLNM("LINE_LOG"))
$ rotation2 = F$ELEMENT(2, " ", F$TRNLNM("LINE_LOG"))
$ rotation3 = F$ELEMENT(3, " ", F$TRNLNM("LINE_LOG"))
$ PIPE SEARCH 'reg_param "Translations:" | (READ SYS$PIPE LINE ; DEFINE/JOB/NOLOG LINE_LOG &LINE)
$ trans1 = F$ELEMENT(1, " ", F$TRNLNM("LINE_LOG"))
$ trans2 = F$ELEMENT(2, " ", F$TRNLNM("LINE_LOG"))
$ trans3 = F$ELEMENT(3, " ", F$TRNLNM("LINE_LOG"))
$ ipl_scanco_prog

/read
  -name                      mr
  -filename                  "MRI

/read
  -name                      xct
  -filename                  "XCT

/register
  -in1                       xct
  -gobj_filename_in1         "CT_GOBJ_T
  -in2                       mr
!  -gobj_filename_in2         "MR_GOBJ_T
  -Tmat_file_name            "REG_FILE_T
  -orientation_search        0 !Use no orientation search as we are providing an initial guess to approximatly line ip the images already
  -initial_rotation          "rotation1 "rotation2 "rotation3 !These are from the initial guess
  -initial_translation       "trans1 "trans2 "trans3  !These are from the initial guess
  -delta_rotation            0.00100 0.00100 0.00500
  -delta_translation         0.00100 0.00100 0.00500
  -resolution_scaling        10 0 0
  -delta_scaling             1.000 0.100 0.100
  -weight_gobj_overlap       0.200 0.000 0.000
  -tolerance                 0.00000010
  -min_corr_coef             -0.000005000
  -min_method                1
  -object_func               2 !Mutual Information for multimodal registration
  -max_nr_iter               10000
  -output_option             2

  ! Create aim files from gobjs to concatenate to visualize registration

/gobj_to_aim
    -gobj_filename             "CT_GOBJ_T
    -output                    ct_gobj
    -peel_iter                 0

/gobj_to_aim
    -gobj_filename             "MR_GOBJ_T
    -output                    mr_gobj
    -peel_iter                 0

!Transform MRI to HR-pQCT space

/transform
   -in                        mr_gobj
   -out                       mr_trans
   -Tmat_file_name            "REG_FILE_T
   -img_interpol_option       0

! Scale images to be the same size

   /scale_elsize
     -input                     mr_trans
     -output                    mr_sca
     -down_scale                1 1 1
     -up_scale                  1.5000 1.5000 7.688
     -integrate                 true

   /scale_elsize
     -input                     ct_gobj
     -output                    ct_sca
     -down_scale                3.000 3.000 3.000
     -up_scale                  1.000 1.000 1.000
     -integrate                 true

! Set HR-pQCT and MRI masks to different colours

   /set_value
     -input                     mr_sca
     -value_object              42
     -value_background          0

   /set_value
     -input                     ct_sca
     -value_object              82
     -value_background          0

! Concatenate MRI and HR-pQCT images

   /concat
     -input1                    mr_sca
     -input2                    ct_sca
     -output                    concat
     -common_region_only        false
     -add_not_overlay           true
     -make_edge                 false
     -shift_ofin2               0 0 0
     -turnangle                 0.000000
     -turnpoint_global          -1 -1

/write concat "CONCAT_T
..
$ EXIT
