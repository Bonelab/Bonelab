'''Test blMuscle'''

import unittest
import subprocess
import shutil, tempfile
import os
import numpy.testing as npt

from .config_cli import cfg
from bonelab.cli.Muscle import Muscle


class TestblMuscle(unittest.TestCase):
    '''Test blMuscle'''
    filenames = [
        'D0010131.AIM'
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
            shutil.copy(download_location, self.test_dir)
            self.assertTrue(os.path.isfile(os.path.join(self.test_dir, filename)))

        # Run
        self.args = {
            'input_filename':                   os.path.join(self.test_dir, 'D0010131.AIM'),
            'converted_filename':               os.path.join(self.test_dir, 'D0010131.nii'),
            'csv_filename':                     os.path.join(self.test_dir, 'muscle.csv'),
            'tiff_filename':                    os.path.join(self.test_dir, 'D0010131.tif'),
            'segmentation_filename':            os.path.join(self.test_dir, 'D0010131_SEG.nii'),
            'bone_threshold':                   800.0,
            'smoothing_iterations':             10,
            'segmentation_iterations':          2,
            'segmentation_multiplier':          2.0,
            'initial_neighborhood_radius':      1.0,
            'closing_radius':                   0.5
        }
        Muscle(**self.args)

    def tearDown(self):
        # Remove temporary directory and all files
        shutil.rmtree(self.test_dir)

    def test_blMuscle(self):
        '''Can run `blMuscle`

        Note that this test takes about 65 seconds, so we should only run it once.
        In order to save time, all tests are compressed here.'''
        # All outputs exist
        self.assertTrue(os.path.isfile(self.args['converted_filename']))
        self.assertTrue(os.path.isfile(self.args['csv_filename']))
        self.assertTrue(os.path.isfile(self.args['tiff_filename']))
        self.assertTrue(os.path.isfile(self.args['segmentation_filename']))

        # CSV file written correctly
        entry = []
        header = []
        with open(self.args['csv_filename'], 'r') as fp:
            for cnt, line in enumerate(fp):
                if len(header)==0:
                    header = [x.replace(os.linesep, '') for x in line.split(',')]
                else:
                    this_entry = [x.replace(os.linesep, '') for x in line.split(',')]
                    entry.append(this_entry)

        expected_header= [
            'Filename', 'Spacing.X [mm]', 'Spacing.Y [mm]', 'Spacing.Z [mm]',
            'density_slope', 'density_intercept',
            'muscle density [native]', 'A.Cross [vox^2]'
        ]
        self.assertEqual(len(entry), 1)
        self.assertEqual(header, expected_header)
        self.assertEqual(entry[0][0], self.args['input_filename'])
        npt.assert_almost_equal(float(entry[0][1]), 0.18219922482967377, decimal=4)
        npt.assert_almost_equal(float(entry[0][2]), 0.18219922482967377, decimal=4)
        npt.assert_almost_equal(float(entry[0][3]), 0.18219922482967377, decimal=4)
        npt.assert_almost_equal(float(entry[0][4]), 0.1957420703125, decimal=4)
        npt.assert_almost_equal(float(entry[0][5]), -391.209015, decimal=4)
        npt.assert_almost_equal(float(entry[0][6]), 2093.1338525656342, decimal=4)
        npt.assert_almost_equal(float(entry[0][7]), 118632.01818181819, decimal=4)


if __name__ == '__main__':
    unittest.main()
