# History:
#   2017.03.16  babesler@ucalgary.ca    Created
#
# Description:
#   Function to convert an AIM to another image format and scale it to HU from
#       SCANCO native units.
#
# Notes:
#   - None
#
# Usage: python native_to_hu.py input.aim output.nii

# Imports
import vtk
import re
import os

# Below are tests taken from /threshold in IPL.
# Numbers come from /threshold in IPL
hu = [300.1572, 15905.655, -0.1172, 4999.812]
native = [2520, 32767, 1938, 11629]

# Determine TF
m = (hu[1] - hu[0]) / (native[1] - native[0])
b = hu[1] - m*native[1]

print "IPL Eq: {} x + {}".format(m,b)

formatter="{:>20}"*3
print formatter.format("Native", "Hu predicted", "HU actual");
for h, n in zip(hu, native):
    pred = m*n+b;
    print formatter.format(n, pred, h)

#proclog = reader.GetProcessingLog()
proclog="""!
! Processing Log
!
!-------------------------------------------------------------------------------
Created by                    ISQ_TO_AIM (IPL)                                  
Time                          12-DEC-2016 13:14:15.91                           
Original file                 uct_measurement_data:[00000815.00004261]d0004254.isq
Original Creation-Date         2-FEB-2016 09:28:19.15                           
Orig-ISQ-Dim-p                                   2304       2304        504
Orig-ISQ-Dim-um                                139852     139852      30592
!-------------------------------------------------------------------------------
Patient Name                  BHS_090                                           
Index Patient                                     815
Index Measurement                                4261
!-------------------------------------------------------------------------------
Site                                                4
Scanner ID                                       3401
Scanner type                                        9
Position Slice 1 [um]                          157955
No. samples                                      2304
No. projections per 180                           900
Scan Distance [um]                             139852
Integration time [us]                           43000
Reference line [um]                            160955
Reconstruction-Alg.                                 3
Energy [V]                                      68000
Intensity [uA]                                   1470
Angle-Offset [mdeg]                                 0
Default-Eval                                       10
!-------------------------------------------------------------------------------
Mu_Scaling                                       8192
Calibration Data              68 kVp, BH: 200 mg HA/ccm, Scaling 8192, 0.2 CU   
Calib. default unit type      2 (Density)                                       
Density: unit                 mg HA/ccm                                         
Density: slope                         1.65292004e+03
Density: intercept                    -3.96799988e+02
HU: mu water                                  0.23660
!-------------------------------------------------------------------------------
Parameter (before) name       Linear Attenuation                                
Parameter units               [1/cm]                                            
Minimum value                                -0.31860
Maximum value                                 1.44788
Average value                                 0.04581
Standard deviation                            0.10969
Scaled by factor                                 8192
Minimum data value                        -2610.00000
Maximum data value                        11861.00000
Average data value                          375.30457
Standard data deviation                     898.56189
!-------------------------------------------------------------------------------
Procedure:                    D3P_GobjOrAimMaskAimPeel_OW()                     
Gobj File:                    uct_measurement_data:[00000815.00004261]d0004254_2.gobj
Cutborder                     False                                             
Peel Iterations                                     0
Gobj: Rel. Vol. of set AIM              0.01450334220
Gobj: of Set Vol(dim-2*off) of AIM               2304       2304        504
! 
Parameter (before) name       Linear Attenuation                                
Parameter units               [1/cm]                                            
Minimum value                                -0.23059
Maximum value                                 1.44788
Average value                                 0.29551
Standard deviation                            0.16394
Scaled by factor                           8192.00000
Minimum data value                        -1889.00000
Maximum data value                        11861.00000
Average data value                         2420.80396
Standard data deviation                    1343.02991
!-------------------------------------------------------------------------------
Procedure:                    D3P_BoundingBoxCut()                              
z only (False: also xy)       False                                             
Null Border                                         0          0          0
! 
Parameter name                Linear Attenuation                                
Parameter units               [1/cm]                                            
Minimum value                                -0.23059
Maximum value                                 1.44788
Average value (approx.)                       9.54046
Standard deviation (approx.)                  0.00000
Scaled by factor                           8192.00000
Minimum data value                        -1889.00000
Maximum data value                        11861.00000
Average data value (approx.)              78155.46875
Standard data deviation (approx.)             0.00000
!-------------------------------------------------------------------------------"""

mu_scaling_match = re.search(r'Mu_Scaling\s+(\d+)', proclog)
hu_mu_water_match = re.search(r'HU: mu water\s+(\d+.\d+)', proclog)

mu_scaling = int(mu_scaling_match.group(1))
hu_mu_water = float(hu_mu_water_match.group(1))
hu_mu_air = 0
print('Found the following calibration data in the header:')
print('\tmu_scaling: {}'.format(mu_scaling))
print('\thu_mu_water: {}'.format(hu_mu_water))

# First convert Native -> mu (linear attenuation)
#   mu = Native / mu_scaling
# Second convert mu -> HU
#   HU = 1000 * (mu - mu_water) / (mu_water - mu_air)

m = 1000.0 / mu_scaling / (hu_mu_water - hu_mu_air)
b = -1000.0 * hu_mu_water / (hu_mu_water - hu_mu_air)

print "Proc. log eq: {} x + {}".format(m,b)

