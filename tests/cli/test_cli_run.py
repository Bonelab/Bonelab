'''Test command line interface run'''

import unittest
import subprocess
import shutil, tempfile
import os

from .config_cli import cfg


class TestCommandLineInterfeceRun(unittest.TestCase):
    '''Test command line interface run
    
    For non-visualization scripts, test that each command line functionality
    can be ran
    '''
    filenames = [
        'test25a.aim'
    ]

    def runner(self, command):
        self.assertTrue(
            cfg['RUN_CALL'](command),
            'Could not run command \"{}\"'.format(' '.join(command))
        )

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

    def test_blDownloadData(self):
        '''Can run `blDownloadData`'''
        directory = os.path.join(self.test_dir, 'bldata')
        command = ['blDownloadData', '-n', '--output_directory', directory]
        self.runner(command)

        # Test that the expected files exist
        self.assertTrue(os.path.isdir(directory))
        for filename in self.filenames:
            self.assertTrue(os.path.isfile(os.path.join(directory, filename)))

    def test_aix(self):
        '''Can run `aix`'''
        command = ['aix', os.path.join(self.test_dir, 'test25a.aim')]
        self.runner(command)

    def test_blImageConvert(self):
        '''Can run `blImageConvert`'''
        command = ['blImageConvert', os.path.join(self.test_dir, 'test25a.aim'), os.path.join(self.test_dir, 'test.aim')]
        self.runner(command)
        self.assertTrue(os.path.join(self.test_dir, 'test.aim'))


if __name__ == '__main__':
    unittest.main()
