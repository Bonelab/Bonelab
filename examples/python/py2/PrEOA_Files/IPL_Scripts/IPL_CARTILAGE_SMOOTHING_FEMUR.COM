$! ## ==============================================================================
$! ##    Smooth Segmented Cartilage
$! ## ==============================================================================
$! ## This script smooths the cartilage that has already been segmented from the MRI
$! ## and transforms it to the HR-pQCT space
$! ##
$! ## Author: Jenn Bhatla, 2016 Updated July 2, 2017
$! ## ------------------------------------------------------------------------------
$! ##    Input parameters and output
$! ## ------------------------------------------------------------------------------
$! ##
$! ## Input #1: Segmented Cartilage gobj
$! ## Input #2: Transformation matrix obtained during registraion
$! ##
$! ## Output #1: Smoothed cartilage gobj
$! ## Output #2: Smoothed cartilage aim
$! ## Output #3: Cartilage thickness map
$! ##
$! ## Note: for the PrE-OA Study this script was run after the IPL_SEGMENT_CARTILAGE_FEMUR.COM
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
$   CARTILAGE = DEV_READ + DIR_READ + FILENAME_MR + "_FC_SEG.GOBJ" !Input segmented cartilage gobj
$   CARTILAGE_SEG = DEV_WRITE + DIR_WRITE + FILENAME_REG + "_FC_SEG.AIM" !Output segmented cartilage gobj
$   THICKNESS = DEV_WRITE + DIR_WRITE + FILENAME_REG + "_FC_THICK_REG.AIM" !Thickness map of cartilage (not actually used in analysis, just for understanding)
$   REG_FILE = DEV_WRITE + DIR_WRITE + FILENAME_REG + "_F_REG3.DAT"
$
$   ipl_scanco_prog := $um:ipl_scanco_m.exe
$
$
$		SIGMA := 1.2
$		SUPPORT := 2
$		FEM_SEG = DEV + DIR + FILENAME+ "_SEG.AIM"
$
$   ipl_scanco_prog

/db_scanco_activate false

/gobj_to_aim "CARTILAGE cart

! Transform the MRI scan to HR-pQCT space
/transform
  -in                        cart
  -out                       cart_trans
  -Tmat_file_name            "REG_FILE
  -el_size_mm_out            0.1821 0.1821 0.1821

!Smooth cartilage
/set_value
   -input                     cart_trans
   -value_object              127
   -value_background          0

/seg_gauss
  -input                     cart_trans
  -output                    cartilage
  -sigma                     3.00000
  -support                   6
  -lower_in_perm_aut_al      700.00000
  -upper_in_perm_aut_al      10000.0
  -value_in_range            42
  -unit                      0


/write cartilage "CARTILAGE_SEG

! Create thickness maps of the cartilage
/dt_thickness
  -input                     cartilage
  -output                    thickness

/voxgobj_scanco_param
  -input                     cartilage

/write thickness "THICKNESS
..
$
$
$
$
$
$ EXIT
