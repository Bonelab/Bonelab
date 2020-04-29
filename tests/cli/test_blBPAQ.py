'''Test blBPAQ'''

import unittest
import subprocess
import shutil, tempfile, filecmp, difflib
import os
import numpy.testing as npt

from tests.config_cli import cfg
from bonelab.cli.BPAQ import BPAQ


class TestblBPAQ(unittest.TestCase):
    '''Test blBPAQ'''
    filenames = [
        'bpaq_data.xlsx',
        'bpaq_output.csv'
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

        # Setup output files
        self.excel_file = os.path.join(self.test_dir, 'bpaq_data.xlsx')
        self.csv_file_expected = os.path.join(self.test_dir, 'bpaq_output.csv')
        self.csv_file_produced = os.path.join(self.test_dir, 'bpaq_output_produced.csv')

        # Run
        self.args = {
            'ifile':        self.excel_file,
            'ofile':        self.csv_file_produced,
            'show_table':   False,
            'show_redcap':  False
        }
        BPAQ(**self.args)

    def tearDown(self):
        # Remove temporary directory and all files
        shutil.rmtree(self.test_dir)

    def test_blBPAQ(self):
        '''`blBPAQ` produces correct output'''
        # All outputs exist
        for filename in [self.excel_file, self.csv_file_expected, self.csv_file_produced]:
            self.assertTrue(os.path.isfile(filename), 'Can find ' + filename)

        with open(self.csv_file_expected, 'r') as f:
            expected_contents = f.read()

        with open(self.csv_file_produced, 'r') as f:
            produced_contents = f.read()

        # Check output is as expected
        filecmp.clear_cache()
        self.assertTrue(
            filecmp.cmp(self.csv_file_expected, self.csv_file_produced, shallow=False),
            '{o}Expected{o}"{}"{o}Received{o}"{}"{o}'.format(
                expected_contents, produced_contents, o=os.linesep
        ))

if __name__ == '__main__':
    unittest.main()
