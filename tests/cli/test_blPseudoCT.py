'''Test blPseudoCT'''

import unittest
import subprocess
import shutil, tempfile
import os
import numpy.testing as npt

from .config_cli import cfg
from bonelab.cli.PseudoCT import PseudoCT


class TestblPseudoCT(unittest.TestCase):
    '''Test blPseudoCT'''
    filenames = [
        'COR_PD_3'
    ]

    def setUp(self):
        # Create temporary directory to work in
        self.test_dir = tempfile.mkdtemp()

        # Download testing data
        for filename in self.filenames:
            # Fetch the data
            download_location = cfg['DOWNLOAD_TESTING_DATA'](filename)
            self.assertNotEqual(download_location, '', 'Unable to download file ' + filename)

            # Copy to temporary directory
            if os.path.isdir(self.test_dir):
                shutil.copytree(download_location, os.path.join(self.test_dir, filename))
            else:
                shutil.copy(download_location, self.test_dir)
            self.assertTrue(os.path.isdir(os.path.join(self.test_dir, filename)))

        # Run
        self.args = {
            'input_directory':                  os.path.join(self.test_dir, 'COR_PD_3'),
            'output_directory':                 os.path.join(self.test_dir, 'COR_PD_3_ct'),
            'expression':                       '*',
            'overwrite':                        True,
            'verbose':                          False
        }
        PseudoCT(**self.args)

    def tearDown(self):
        # Remove temporary directory and all files
        shutil.rmtree(self.test_dir)

    def test_blPseudoCT(self):
        '''Can run `blPseudoCT`

        Note that this test takes a while.'''
        # Output exists
        self.assertTrue(os.path.isdir(self.args['output_directory']))

if __name__ == '__main__':
    unittest.main()
