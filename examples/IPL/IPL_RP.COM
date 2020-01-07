$! History:
$!  2016.05.30   babesler@ucalgary.ca     Created
$!  2017.01.10   babesler@ucalgary.ca     Updated to over threshold
$!
$! Description:
$!  Prepares a segmented image for rapid prototyping
$!
$! Inputs:
$!      P1  INPUT_IMAGE       A grey-scale image of bone
$! Outputs:
$!          OUTPUT_IMAGE      The output RP image
$!
$! Example Usage:
$!  @IPL_RP.COM DISK4:[BONELAB.PROJECTS.TBONE.RP]TBONE_002_P00_RR.AIM
$!
$! Notes:
$!      - None
$!
$   ON ERROR THEN EXIT
$!
$! Constants
$   SCRIPT_NAME := IPL_RP.COM
$   VERSION := 0.2
$   IPL_PROGRAM := $UM:IPL_SCANCO_M.EXE
$   SIGMA := 0.8
$   SUPPORT := 1
$   THRESHOLD := 300
$   EL_SIZE := 0.18
$   BOUNDARY := 10
$   TIME = F$CVTIME()
$!
$! Generate file names
$   INPUT_IMAGE   = P1
$   FILENAME      = F$PARSE(INPUT_IMAGE,,,"NAME")
$   DEV           = F$PARSE(INPUT_IMAGE,,,"DEVICE")
$   DIR           = F$PARSE(INPUT_IMAGE,,,"DIRECTORY")
$   OUTPUT_IMAGE  = DEV + DIR + FILENAME + "_RP.AIM"
$!
$! Write variables out to screen
$   WRITE SYS$OUTPUT "Variables:"
$   WRITE SYS$OUTPUT "    FILENAME = ''FILENAME'"
$   WRITE SYS$OUTPUT "    DEV = ''DEV'"
$   WRITE SYS$OUTPUT "    DIR = ''DIR'"
$   WRITE SYS$OUTPUT "    SIGMA = ''SIGMA'"
$   WRITE SYS$OUTPUT "    SUPPORT = ''SUPPORT'"
$   WRITE SYS$OUTPUT "    THRESHOLD = ''THRESHOLD'"
$   WRITE SYS$OUTPUT "    EL_SIZE = ''EL_SIZE'"
$   WRITE SYS$OUTPUT "    BOUNDARY = ''BOUNDARY'"
$   WRITE SYS$OUTPUT "    INPUT_IMAGE = ''INPUT_IMAGE'"
$   WRITE SYS$OUTPUT "    OUTPUT_IMAGE = ''OUTPUT_IMAGE'"
$!
$   IPL_PROGRAM

/read
  -name                      in
  -filename                  "INPUT_IMAGE

/seg_gauss
  -input                     in
  -output                    seg
  -sigma                     "SIGMA
  -support                   "SUPPORT
  -lower_in_perm_aut_al      "THRESHOLD
  -upper_in_perm_aut_al      100000.000000
  -value_in_range            127
  -unit                      2

/delete in

/sub_get
  -input                     seg
  -output                    sub
  -pos                       -1 -1 84
  -dim                       -1 -1 84
  -global_pos_flag           false

/bounding_box_cut
  -input                     sub
  -output                    bb
  -z_only                    false
  -border                    "BOUNDARY

/cl_ow_rank_extract
  -input_output              bb
  -first_rank                1
  -last_rank                 1
  -connect_boundary          false
  -value_in_range            127
  -topology                  6

/header_geo_set
  -input                     bb
  -el_size_mm_new            "EL_SIZE

/write_v020
  -name                      bb
  -filename                  "OUTPUT_IMAGE
  -compress_type             bin
  -version_020               true

..
$!
$  WRITE SYS$OUTPUT "Finished!"
$!
$   EXIT
