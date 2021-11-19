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
        'bpaq_output.csv',
        'bpaq_individual.txt',
        'bpaq_individual_output.csv',
        'bpaq_template_out.txt'
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
        
    def tearDown(self):
        # Remove temporary directory and all files
        shutil.rmtree(self.test_dir)

    def runner(self, args, expected_file, produced_file):
        # Run
        BPAQ(**args)

        # Test file exists
        self.assertTrue(os.path.isfile(produced_file), 'Can find ' + produced_file)

        # Assert content equal
        with open(expected_file, 'r') as f:
            expected_contents = f.read()

        with open(produced_file, 'r') as f:
            produced_contents = f.read()

        self.assertTrue(
            filecmp.cmp(expected_file, produced_file, shallow=False),
            '{o}Expected{o}"{}"{o}Received{o}"{}"{o}'.format(
                expected_contents, produced_contents, o=os.linesep
        ))

    def test_blBPAQ_excel(self):
        '''`blBPAQ` runs with Excel file'''
        excel_file = os.path.join(self.test_dir, 'bpaq_data.xlsx')
        csv_file_expected = os.path.join(self.test_dir, 'bpaq_output.csv')
        csv_file_produced = os.path.join(self.test_dir, 'bpaq_output_produced.csv')

        args = {
            'ifile':          excel_file,
            'ofile':          csv_file_produced,
            'show_table':     False,
            'show_redcap':    False,
            'print_template': False
        }

        self.runner(args, csv_file_expected, csv_file_produced)

    def test_blBPAQ_individual(self):
        '''`blBPAQ` runs with individual'''
        excel_file = os.path.join(self.test_dir, 'bpaq_individual.txt')
        csv_file_expected = os.path.join(self.test_dir, 'bpaq_individual_output.csv')
        csv_file_produced = os.path.join(self.test_dir, 'bpaq_individual_output_produced.csv')

        args = {
            'ifile':          excel_file,
            'ofile':          csv_file_produced,
            'show_table':     False,
            'show_redcap':    False,
            'print_template': False
        }

        self.runner(args, csv_file_expected, csv_file_produced)

    def test_blBPAQ_template(self):
        '''`blBPAQ` runs with template'''
        template = os.path.join(self.test_dir, 'bpaq_template.txt')
        template_expected = os.path.join(self.test_dir, 'bpaq_template_out.txt')
        template_produced = os.path.join(self.test_dir, 'bpaq_template.txt')


        args = {
            'ifile':          template,
            'show_table':     False,
            'show_redcap':    False,
            'print_template': True
        }

        self.runner(args, template_expected, template_produced)


if __name__ == '__main__':
    unittest.main()
