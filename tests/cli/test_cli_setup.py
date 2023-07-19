'''Test command line interface setup'''

import unittest
import subprocess

from tests.config_cli import cfg


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

    def test_blDownloadData(self):
        '''Can run `blDownloadData`'''
        self.runner('blDownloadData')

    def test_blExtractFields(self):
        '''Can run `blExtractFields`'''
        self.runner('blExtractFields')

    def test_blImage2ImageSeries(self):
        '''Can run `blImage2ImageSeries`'''
        self.runner('blImage2ImageSeries')

    def test_blImageConvert(self):
        '''Can run `blImageConvert`'''
        self.runner('blImageConvert')

    def test_blImageSeries2Image(self):
        '''Can run `blImageSeries2Image`'''
        self.runner('blImageSeries2Image')

    def test_blMuscle(self):
        '''Can run `blMuscle`'''
        self.runner('blMuscle')

    def test_blSliceViewer(self):
        '''Can run `blSliceViewer`'''
        self.runner('blSliceViewer')

    def test_blVisualizeSegmentation(self):
        '''Can run `blVisualizeSegmentation`'''
        self.runner('blVisualizeSegmentation')

    def test_blRapidPrototype(self):
        '''Can run `blRapidPrototype`'''
        self.runner('blRapidPrototype')

    def test_scrub_vms_extension(self):
        '''Can run `scrub_vms_extension`'''
        self.runner('scrub_vms_extension')

    @unittest.skip('`gdcm` dependency problem')
    def test_blPseudoCT(self):
        '''Can run `blPseudoCT`'''
        self.runner('blPseudoCT')

    def test_blBPAQ(self):
        '''Can run `blBPAQ`'''
        self.runner('blBPAQ')

    def test_blRegBCn88modelgenerator(self):
        '''Can run `blRegBCn88modelgenerator`'''
        self.runner('blRegBCn88modelgenerator')

    def test_blRegBCtransformresults(self):
        '''Can run `blRegBCtransformresults`'''
        self.runner('blRegBCtransformresults')

    def test_blAutocontour(self):
        ''' Can run `blAutocontour` '''
        self.runner('blAutocontour')

    def test_blRegistration(self):
        ''' Can run `blRegistration` '''
        self.runner('blRegistration')

    def test_blRegistrationDemons(self):
        ''' Can run `blRegistrationDemons` '''
        self.runner('blRegistrationDemons')

    def test_blITKSnapAnnotParser(self):
        ''' Can run `blITKSnapAnnotParser` '''
        self.runner('blITKSnapAnnotParser')

    def test_blImageFilter(self):
        ''' Can run `blImageFilter` '''
        self.runner('blImageFilter')

    def test_blPanningVideo(self):
        ''' Can run `blPanningVideo` '''
        self.runner('blPanningVideo')

    def test_blRegistrationApplyTransform(self):
        ''' Can run `blRegistrationApplyTransform` '''
        self.runner('blRegistrationApplyTransform')

    def test_blComputeOverlap(self):
        ''' Can run `blImageComputeOverlap` '''
        self.runner('blImageComputeOverlap')


if __name__ == '__main__':
    unittest.main()
