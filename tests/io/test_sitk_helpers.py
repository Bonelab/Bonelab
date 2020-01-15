'''Test sitk_helpers'''

import unittest
import shutil, tempfile
from bonelab.io.sitk_helpers import sitk_supported_file_types


class TestSITKHelpers(unittest.TestCase):
    '''Test sitk_helpers'''

    def runner(self, extension):
        self.assertTrue(extension in sitk_supported_file_types)
        self.assertTrue('supported_types' in sitk_supported_file_types[extension])
        self.assertTrue(len(sitk_supported_file_types[extension]['supported_types'])>0)
        self.assertTrue('sitk_cast_type' in sitk_supported_file_types[extension])
        self.assertTrue('np_cast_type' in sitk_supported_file_types[extension])

    def test_sitk_supported_file_types_bmp(self):
        '''bmp defined in sitk_supported_file_types'''
        self.runner('bmp')

    def test_sitk_supported_file_types_tif(self):
        '''tif defined in sitk_supported_file_types'''
        self.runner('tif')

    def test_sitk_supported_file_types_tiff(self):
        '''tiff defined in sitk_supported_file_types'''
        self.runner('tiff')

    def test_sitk_supported_file_types_jpg(self):
        '''jpg defined in sitk_supported_file_types'''
        self.runner('jpg')

    def test_sitk_supported_file_types_jpeg(self):
        '''jpeg defined in sitk_supported_file_types'''
        self.runner('jpeg')

    def test_sitk_supported_file_types_png(self):
        '''png defined in sitk_supported_file_types'''
        self.runner('png')


if __name__ == '__main__':
    unittest.main()
