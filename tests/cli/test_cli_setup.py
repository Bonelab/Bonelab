'''Test command line interface setup'''

import unittest
import subprocess

from .config_cli import cfg

class TestCommandLineInterfeceSetup(unittest.TestCase):
    '''Test command line interface setup
    
    The help section of all expected command line tools are ran here
    to guarantee they were exported by setup.cfg using pbr
    '''

    def runner(self, entry_point):
        command = [entry_point, '-h']
        self.assertTrue(
            cfg['RUN_CALL'](command),
            'Could not run command \"{}\"'.format(' '.join(command))
        )

    def test_aimod(self):
        '''Can run `aimod`'''
        self.runner('aimod')

    def test_aix(self):
        '''Can run `aix`'''
        self.runner('aix')

    def test_blImageConvert(self):
        '''Can run `blImageConvert`'''
        self.runner('blImageConvert')

    def test_blDownloadData(self):
        '''Can run `blDownloadData`'''
        self.runner('blDownloadData')

    def test_blSliceViewer(self):
        '''Can run `blSliceViewer`'''
        self.runner('blSliceViewer')


if __name__ == '__main__':
    unittest.main()
