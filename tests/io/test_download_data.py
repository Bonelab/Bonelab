'''Test get_vtk_reader'''

import unittest
import vtk
import vtkbone
import shutil, tempfile
import os


class TestDownloadData(unittest.TestCase):
    '''Test download data
    
    Simply tests that all variables are defined
    '''

    def test_BL_DATA_DEFAULT_URL_defined(self):
        '''BL_DATA_DEFAULT_URL is defined'''
        from bonelab.io.download_data import BL_DATA_DEFAULT_URL

    def test_BL_DATA_DIRECTORY_ENVIRONMENT_VARIABLE_defined(self):
        '''BL_DATA_DIRECTORY_ENVIRONMENT_VARIABLE is defined'''
        from bonelab.io.download_data import BL_DATA_DIRECTORY_ENVIRONMENT_VARIABLE

    def test_BL_DATA_DIRECTORY_DEFAULT_defined(self):
        '''BL_DATA_DIRECTORY_DEFAULT is defined'''
        from bonelab.io.download_data import BL_DATA_DIRECTORY_DEFAULT


if __name__ == '__main__':
    unittest.main()
