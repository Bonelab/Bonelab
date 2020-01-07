$! ## ==============================================================================
$! ##    Segment cartilage from MRI scan
$! ## ==============================================================================
$! ## This script segments cartilage from the MRI scan using the HR-pQCT mask to
$! ## define the bone-cartilage interface
$! ##
$! ## Author: Jenn Bhatla, 2016 Updated July 2, 2017
$! ## ------------------------------------------------------------------------------
$! ##    Input parameters and output
$! ## ------------------------------------------------------------------------------
$! ##
$! ## Input #1: MRI Scan (Can use MRI scan that has realigned slices)
$! ## Input #2: HR-pQCT bone gobj
$! ## Input #3: MRI Cartilage gobj (without outside contoured but bone-cartilage interface overestimated)
$! ## Input #4: Transformation matrix obtained during registraion
$! ##
$! ## Output #1: Segmented cartilage gobj
$! ##
$! ## Note: for the PrE-OA Study this script was run after the IPL_REGISTER_MRI_XCT_TIBIA.COM
$! ## ------------------------------------------------------------------------------
$! ##    START OF CODE
$! ## ------------------------------------------------------------------------------
$!
$! SUBMIT/QUEUE=SYS$FAST/NOPRINT/NONOTIFY/PRIORITY=100/LOG=SYS$SCRATCH: DISK4:[BONELAB.PROJECTS.PREOA.COM]IPL_CARTILAGE_ANALYSIS.COM
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
$   AIM_FILE = DEV_READ + DIR_READ + FILENAME_MR + "_REG.AIM"   !MRI Scan with realigned slices (or not realigned if this isn't an issue)
$   IPL_GOBJ_CT = DEV_READ + DIR_READ + FILENAME_CT + "_T.GOBJ"  !Bone gobj from HR-pQCT
$   CARTILAGE = DEV_READ + DIR_READ + FILENAME_MR + "_TC_reg.GOBJ" !input cartilage gobj
$   REG_FILE = DEV_WRITE + DIR_WRITE + FILENAME_REG + "_T_REG3.DAT" ! input transformation matrix obtained from registration
$   CARTILAGE_SEG = DEV_READ + DIR_READ + FILENAME_MR + "_TC_SEG.GOBJ" !output segmented cartilage gobj
$!
$   ipl_scanco_prog := $um:ipl_scanco_m.exe
$
$! Parameters for gaussian segmentation
$		SIGMA := 1.2
$		SUPPORT := 2
$		FEM_SEG = DEV + DIR + FILENAME+ "_SEG.AIM"
$
$   ipl_scanco_prog

/db_scanco_activate false

/gobj_to_aim "IPL_GOBJ_CT  bone_gobj
/gobj_to_aim "CARTILAGE  cart_gobj

! Transform HR-pQCT gobj to MRI

/transform
  -in                        bone_gobj
  -out                       bone_gobj_trans
  -Tmat_file_name            "REG_FILE
  -el_size_mm_out            0.2734  0.2734  1.4000
  -Tmat_invert               true

! Set bone and cartilage to different values

/set_value
   -input                     cart_gobj
   -value_object              42
   -value_background          0

/set_value
   -input                     bone_gobj_trans
   -value_object              82
   -value_background          0

! Add HR-pQCT bone mask and MRI cartilage mask together and threshold to subtract bone from the cartilage mask

/add_aims
  -input1                    cart_gobj
  -input2                    bone_gobj_trans
  -output                    out

/absolute_threshold
  -input                     out
  -output                    cartilage
  -lower_in_abs              42
  -upper_in_abs              42
  -grayscale_or_scaledvalues true
  -value_in_range            127

/togobj_from_aim cartilage "CARTILAGE_SEG

..
$
$
$
$
$
$ EXIT
