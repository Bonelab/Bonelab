$! ## ==============================================================================
$! ##   IPL Peeled aims for REG
$! ## ==============================================================================
$! ## This script creates aims to be used in blSurfaceViewer to find initial guess for registration.
$! ##
$! ## Author: Jenn Bhatla, 2016 Updated July 2, 2017
$! ## ------------------------------------------------------------------------------
$! ##    Input parameters and output
$! ## ------------------------------------------------------------------------------
$! ##
$! ## Input #1: HR-pQCT Scan
$! ## Input #2: HR-pQCT Bone gobj
$! ## Input #3: MRI Scan
$! ## Input #4: MRI Bone gobj
$! ##
$! ## Output #1: HR-pQCT peeled and downscaled image
$! ## Output #2: MRI peeled and downscaled image
$! ##
$! ## Note: The bone (femur vs. tibia is hardcoded into the script and needs to be adjusted)
$! ## ------------------------------------------------------------------------------
$! ##    START OF CODE
$! ## ------------------------------------------------------------------------------
$!
$!  IPL Batch Scanco
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
$   BONE = DEV_WRITE + DIR_READ + FILENAME_CT + ".AIM" !HR-pQCT greyscale
$   CART = DEV_WRITE + DIR_READ + FILENAME_MR + ".AIM"  !MRI greyscale
$   BONE_GOBJ = DEV_WRITE + DIR_READ + FILENAME_CT + "_F.GOBJ" !HR-pQCT bone gobj
$   CART_GOBJ = DEV_WRITE + DIR_READ + FILENAME_MR + "_F.GOBJ" !MRI bone gobj
$   BONE_PEEL = DEV_WRITE + DIR_WRITE + FILENAME_CT + "_PEEL_F.AIM" !HR-pQCT peeled image
$   CART_PEEL = DEV_WRITE + DIR_WRITE + FILENAME_MR + "_PEEL_F.AIM" !MRI peeled image
$
$   ipl_scanco_prog := $um:ipl_scanco_m.exe
$
$
$
$   ipl_scanco_prog

/db_scanco_activate false

/read cart "CART

/read bone "BONE

/gobj_maskaimpeel_ow
  -input_output              cart
  -gobj_filename             "CART_GOBJ
  -peel_iter                 0

/gobj_maskaimpeel_ow
  -input_output              bone
  -gobj_filename             "BONE_GOBJ

/scale_elsize
  -input                     bone
  -output                    bone_sca
  -down_scale                3 3 3
  -integrate                 true

/write bone_sca "BONE_PEEL
/write cart "CART_PEEL
..

$
$
$
$
$
$ EXIT
