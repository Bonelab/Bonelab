'''Test aim calibration header'''

import unittest
import os

from bonelab.util.aim_calibration_header import \
    get_aim_hu_equation, \
    get_aim_density_equation, \
    get_aim_calibration_constants_from_processing_log


class TestAIMCalibrationHeader(unittest.TestCase):
    '''Test aim calibration header'''

    def setUp(self):
        # Note the following for this dataset
        #    !% D3p_sup_threshold: Setting input unit 0 to 6: Permille 1/1000.
        #    !% If orig aim: Thresholds correspond to Lin.Att.: 1.2000 4.000 [1/cm]
        #    !% If orig aim: Thresholds correspond to Dens: 1532.9355 6022.671 [mg HA/ccm]
        #    !% If orig aim: Thresholds correspond to HU: 3981.1174 15603.894 [HU]
        #    !% Thresholds correspond to native numbers:   9830 32767

        self.processing_log = '''!
! Processing Log
!
!-------------------------------------------------------------------------------
Created by                    ISQ_TO_AIM (IPL)                                  
Time                           7-JAN-2020 11:50:11.17                           
Original file                 dk0:[xtremect2.data.00002360.00011786]d0010131.isq;
Original Creation-Date        20-MAR-2019 13:04:39.09                           
Orig-ISQ-Dim-p                                    768        768         55
Orig-ISQ-Dim-um                                139929     139929      10021
!-------------------------------------------------------------------------------
Patient Name                  DBQ_161                                           
Index Patient                                    2360
Index Measurement                               11786
!-------------------------------------------------------------------------------
Site                                                4
Scanner ID                                       3401
Scanner type                                        9
Position Slice 1 [um]                           11975
No. samples                                       768
No. projections per 180                           900
Scan Distance [um]                             139929
Integration time [us]                           43000
Reference line [um]                             11975
Reconstruction-Alg.                                 3
Energy [V]                                      68000
Intensity [uA]                                   1470
Angle-Offset [mdeg]                                 0
Default-Eval                                        4
!-------------------------------------------------------------------------------
Mu_Scaling                                       8192
Calibration Data              68 kVp, BH: 200 mg HA/ccm, Scaling 8192, 0.2 CU   
Calib. default unit type      2 (Density)                                       
Density: unit                 mg HA/ccm                                         
Density: slope                         1.60351904e+03
Density: intercept                    -3.91209015e+02
HU: mu water                                  0.24090
!-------------------------------------------------------------------------------
Parameter name                Linear Attenuation                                
Parameter units               [1/cm]                                            
Minimum value                                -0.10791
Maximum value                                 1.07495
Average value                                 0.16743
Standard deviation                            0.16057
Scaled by factor                                 8192
Minimum data value                         -884.00000
Maximum data value                         8806.00000
Average data value                         1371.61597
Standard data deviation                    1315.35596
!-------------------------------------------------------------------------------'''

    def test_get_aim_calibration_constants_from_processing_log_mu_scaling(self):
        mu_scaling, hu_mu_water, hu_mu_air, density_slope, density_intercept = get_aim_calibration_constants_from_processing_log(self.processing_log)

        self.assertAlmostEqual(mu_scaling, 8192.0)

    def test_get_aim_calibration_constants_from_processing_log_hu_mu_water(self):
        mu_scaling, hu_mu_water, hu_mu_air, density_slope, density_intercept = get_aim_calibration_constants_from_processing_log(self.processing_log)

        self.assertAlmostEqual(hu_mu_water, 0.24090)

    def test_get_aim_calibration_constants_from_processing_log_hu_mu_air(self):
        mu_scaling, hu_mu_water, hu_mu_air, density_slope, density_intercept = get_aim_calibration_constants_from_processing_log(self.processing_log)

        self.assertAlmostEqual(hu_mu_air, 0.0)

    def test_get_aim_calibration_constants_from_processing_log_density_slope(self):
        mu_scaling, hu_mu_water, hu_mu_air, density_slope, density_intercept = get_aim_calibration_constants_from_processing_log(self.processing_log)

        self.assertAlmostEqual(density_slope, 1.60351904e+03)

    def test_get_aim_calibration_constants_from_processing_log_density_intercept(self):
        mu_scaling, hu_mu_water, hu_mu_air, density_slope, density_intercept = get_aim_calibration_constants_from_processing_log(self.processing_log)

        self.assertAlmostEqual(density_intercept, -3.91209015e+02)

    def test_get_aim_hu_equation_m(self):
        m,b = get_aim_hu_equation(self.processing_log)

        self.assertAlmostEqual(m, 0.5067260792860108)

    def test_get_aim_hu_equation_b(self):
        m,b = get_aim_hu_equation(self.processing_log)

        self.assertAlmostEqual(b, -1000.0)

    def test_get_aim_density_equation_m(self):
        m,b = get_aim_density_equation(self.processing_log)

        self.assertAlmostEqual(m, 0.1957420703125)

    def test_get_aim_density_equation_b(self):
        m,b = get_aim_density_equation(self.processing_log)

        self.assertAlmostEqual(b, -3.91209015e+02)


if __name__ == '__main__':
    unittest.main()
