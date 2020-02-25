'''Test command line interface run'''

import unittest
import subprocess
import shutil, tempfile
import os

from tests.config_cli import cfg


class TestCommandLineInterfaceRun(unittest.TestCase):
    '''Test command line interface run
    
    For non-visualization scripts, test that each command line functionality
    can be ran
    '''
    filenames = [
        'test25a.aim',
        'test25a.nii',
        'dicom',
        'test25a_uniaxial_solved.n88model'
    ]

    def runner(self, command, stdin=None):
        self.assertTrue(
            cfg['RUN_CALL'](command, stdin=stdin),
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
            if os.path.isfile(download_location):
                shutil.copy(download_location, self.test_dir)
                self.assertTrue(os.path.isfile(os.path.join(self.test_dir, filename)))
            else:
                shutil.copytree(download_location, os.path.join(self.test_dir, filename))
                self.assertTrue(os.path.isdir(os.path.join(self.test_dir, filename)))

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
            this_filename = os.path.join(directory, filename)
            self.assertTrue(os.path.exists(this_filename), 'Cannot find file ' + this_filename)

    def test_aix(self):
        '''Can run `aix`'''
        command = ['aix', os.path.join(self.test_dir, 'test25a.aim')]
        self.runner(command)

    def test_blExtractFields(self):
        '''Can run `blExtractFields`'''
        n88 = os.path.join(self.test_dir, 'test25a_uniaxial_solved.n88model')
        aim = os.path.join(self.test_dir, 'output.aim')
        command = ['blExtractFields', n88, aim]
        self.runner(command)
        self.assertTrue(os.path.isfile(aim), 'Cannot find file ' + aim)

    def test_blImage2ImageSeries(self):
        '''Can run `blImage2ImageSeries`'''
        name = os.path.join(self.test_dir, 'test25a')
        command = ['blImage2ImageSeries', os.path.join(self.test_dir, 'test25a.nii'), name, '-n', '4']
        self.runner(command)
        formatter = '{}_%04d.bmp'.format(name)
        for i in range(25):
            filename = formatter % i
            self.assertTrue(os.path.isfile(filename), 'Cannot find file ' + filename)

    def test_blImageSeries2Image(self):
        '''Can run `blImageSeries2Image`'''
        name = os.path.join(self.test_dir, 'dicom.nii')
        command = ['blImageSeries2Image', os.path.join(self.test_dir, 'dicom'), name, '-o']
        self.runner(command)
        self.assertTrue(os.path.isfile(name), 'Cannot find file ' + name)

    def test_blImageConvert(self):
        '''Can run `blImageConvert`'''
        command = ['blImageConvert', os.path.join(self.test_dir, 'test25a.aim'), os.path.join(self.test_dir, 'test.aim')]
        self.runner(command)
        self.assertTrue(os.path.join(self.test_dir, 'test.aim'))


if __name__ == '__main__':
    unittest.main()
