$! ## ==============================================================================
$! ##   IPL Morphing Inputs
$! ## ==============================================================================
$! ## This script creates inputs for morphing the ROIs by downscaling HR-pQCT ROIs
$! ##
$! ## Author: Jenn Bhatla, 2016 Updated July 2, 2017
$! ## ------------------------------------------------------------------------------
$! ##    Input parameters and output
$! ## ------------------------------------------------------------------------------
$! ##
$! ## Inputs: Bone weight bearing ROIs for the medial and lateral femur and tibia
$! ##
$! ## Outputs: Downscaled weight bearing ROIs
$! ##
$! ## Note: The bone (femur vs. tibia is hardcoded into the script and needs to be adjusted if used for a bone other than these)
$! ## ------------------------------------------------------------------------------
$! ##    START OF CODE
$! ## ------------------------------------------------------------------------------
$!  IPL Batch Scanco
$!
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
$! Input and outputs ROIs for each medial and lateral region for the femur and tibia
$   ROI_LAT_T = DEV_READ + DIR_READ + FILENAME_REG + "_XCT_T_LAT.AIM"
$   ROI_LAT_SCA_T = DEV_WRITE + DIR_WRITE + FILENAME_REG + "_XCT_T_LAT_R03.AIM"
$   ROI_MED_T = DEV_READ + DIR_READ + FILENAME_REG + "_XCT_T_MED.AIM"
$   ROI_MED_SCA_T = DEV_WRITE + DIR_WRITE + FILENAME_REG + "_XCT_T_MED_R03.AIM"
$   ROI_LAT_F = DEV_READ + DIR_READ + FILENAME_REG + "_XCT_F_LAT.AIM"
$   ROI_LAT_SCA_F = DEV_WRITE + DIR_WRITE + FILENAME_REG + "_XCT_F_LAT_R03.AIM"
$   ROI_MED_F = DEV_READ + DIR_READ + FILENAME_REG + "_XCT_F_MED.AIM"
$   ROI_MED_SCA_F = DEV_WRITE + DIR_WRITE + FILENAME_REG + "_XCT_F_MED_R03.AIM"
$
$   ipl_scanco_prog := $um:ipl_scanco_m.exe
$
$
$
$   ipl_scanco_prog

/db_scanco_activate false

!!!!!!!!Create Tibia regions
/read roi_lat "ROI_LAT_T

/scale_elsize
  -input                     roi_lat
  -output                    roi_lat_sca
  -down_scale                3 3 3
  -integrate                 true

/write roi_lat_sca "ROI_LAT_SCA_T

/read roi_med "ROI_MED_T

/scale_elsize
  -input                     roi_med
  -output                    roi_med_sca
  -down_scale                3 3 3
  -integrate                 true

/write roi_med_sca "ROI_MED_SCA_T

!!!!!!!!Create Femur regions
/read roi_lat "ROI_LAT_F

/scale_elsize
  -input                     roi_lat
  -output                    roi_lat_sca
  -down_scale                3 3 3
  -integrate                 true

/write roi_lat_sca "ROI_LAT_SCA_F

/read roi_med "ROI_MED_F

/scale_elsize
  -input                     roi_med
  -output                    roi_med_sca
  -down_scale                3 3 3
  -integrate                 true

/write roi_med_sca "ROI_MED_SCA_F
..

$
$
$
$
$
$ EXIT
