'''Helper functions for VTK Input/Output'''

import SimpleITK as sitk
import numpy as np
import copy

# Dictionary of supported filetypes and preferred casting type.
sitk_supported_file_types = {
    'bmp':  {
        'supported_types':      [sitk.sitkUInt8],
        'sitk_cast_type':       sitk.sitkUInt8,
        'np_cast_type':         np.uint8
    },
    'tif': {
        'supported_types':      [sitk.sitkUInt8, sitk.sitkInt8, sitk.sitkUInt16, sitk.sitkInt16],
        'sitk_cast_type':       sitk.sitkFloat32,
        'np_cast_type':         np.float32
    },
    'jpg': {
        'supported_types':      [sitk.sitkUInt8, sitk.sitkUInt32],
        'sitk_cast_type':       sitk.sitkUInt32,
        'np_cast_type':         np.uint32
    },
    'png': {
        'supported_types':      [sitk.sitkUInt8, sitk.sitkUInt32],
        'sitk_cast_type':       sitk.sitkUInt32,
        'np_cast_type':         np.uint32
    }
}
sitk_supported_file_types['tiff'] = copy.copy(sitk_supported_file_types['tif'])
sitk_supported_file_types['jpeg'] = copy.copy(sitk_supported_file_types['jpg'])
