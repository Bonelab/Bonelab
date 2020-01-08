'''Get calibration data from AIM header'''

import re

def get_aim_hu_equation(processing_log):
    '''Get the calibration equation for Hounsfield Units

    First convert Native -> mu (linear attenuation)
        mu = Native / mu_scaling
    Second convert mu -> HU
        HU = 1000 * (mu - mu_water) / (mu_water - mu_air)
    Therefore, the final equation is
        m = 1000.0 / (mu_scaling * (hu_mu_water - hu_mu_air))
        b = - 1000.0 * hu_mu_water / (hu_mu_water - hu_mu_air)
    '''
    # Get constants
    mu_scaling, hu_mu_water, hu_mu_air, density_slope, density_intercept = get_aim_calibration_constants_from_processing_log(processing_log)

    # Compute conversion
    m = 1000.0 / (mu_scaling * (hu_mu_water - hu_mu_air))
    b = -1000.0 * hu_mu_water / (hu_mu_water - hu_mu_air)

    return m, b

def get_aim_density_equation(processing_log):
    '''Get the calibration equation for density

    First convert Native -> mu (linear attenuation)
        mu = Native / mu_scaling
    Second convert mu -> density
        density = density_slope * mu + density_intercept
    Therefore, the final equation is
        density = density_slope * Native / mu_scaling + density_intercept
    '''
    # Get constants
    mu_scaling, hu_mu_water, hu_mu_air, density_slope, density_intercept = get_aim_calibration_constants_from_processing_log(processing_log)

    # Compute conversion
    m = density_slope / mu_scaling
    b = density_intercept

    return m, b

def get_aim_calibration_constants_from_processing_log(processing_log):
    '''Get the calibration constants from a AIM processing log'''
    mu_scaling_match = re.search(r'Mu_Scaling\s+(\d+)', processing_log)
    hu_mu_water_match = re.search(r'HU: mu water\s+(\d+.\d+)', processing_log)
    density_slope_match = re.search(r'Density: slope\s+([-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)', processing_log)
    density_intercept_match = re.search(r'Density: intercept\s+([-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)', processing_log)

    mu_scaling = int(mu_scaling_match.group(1))
    hu_mu_water = float(hu_mu_water_match.group(1))
    hu_mu_air = 0
    density_slope = float(density_slope_match.group(1))
    density_intercept = float(density_intercept_match.group(1))

    return mu_scaling, hu_mu_water, hu_mu_air, density_slope, density_intercept
