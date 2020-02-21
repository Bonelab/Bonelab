'''Test n88_util grab_field'''

import unittest
import subprocess
import shutil, tempfile
import os
from netCDF4 import Dataset

from tests.config_cli import cfg
from bonelab.util.n88_util import grab_field


class TestGrabField(unittest.TestCase):
    '''Test n88_util grab_field'''
    filenames = [
        'test25a_uniaxial_solved.n88model'
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

    def test_bad_field_name(self):
        '''Throw error on bad field name'''
        def instantiate():
            root = Dataset(os.path.join(self.test_dir, 'test25a_uniaxial_solved.n88model'), "r")
            solution = root.groups["Solutions"].groups[root.ActiveSolution]
            grab_field(solution, 'fake_field_name')
        self.assertRaises(IndexError, instantiate)

    def runner(self, field_name):
        root = Dataset(os.path.join(self.test_dir, 'test25a_uniaxial_solved.n88model'), "r")
        solution = root.groups["Solutions"].groups[root.ActiveSolution]
        field = grab_field(solution, field_name)

        self.assertEqual(len(field), 7087)

    def test_strain_energy_density(self):
        '''Can extract SED'''
        self.runner('StrainEnergyDensity')

    def test_von_mises_stress(self):
        '''Can extract SED'''
        self.runner('VonMisesStress')

    def test_stress_xx(self):
        '''Can extract StressXX'''
        self.runner('StressXX')

    def test_stress_yy(self):
        '''Can extract StressYY'''
        self.runner('StressYY')

    def test_stress_zz(self):
        '''Can extract StressZZ'''
        self.runner('StressZZ')

    def test_stress_xy(self):
        '''Can extract StressXY'''
        self.runner('StressXY')

    def test_stress_yz(self):
        '''Can extract StressYZ'''
        self.runner('StressYZ')

    def test_stress_xz(self):
        '''Can extract StressXZ'''
        self.runner('StressXZ')

    def test_strain_xx(self):
        '''Can extract StainXX'''
        self.runner('StrainXX')

    def test_strain_yy(self):
        '''Can extract StrainYY'''
        self.runner('StrainYY')

    def test_strain_zz(self):
        '''Can extract StrainZZ'''
        self.runner('StrainZZ')

    def test_strain_xy(self):
        '''Can extract StainXY'''
        self.runner('StrainXY')

    def test_strain_yz(self):
        '''Can extract StrainYZ'''
        self.runner('StrainYZ')

    def test_strain_xz(self):
        '''Can extract StrainXZ'''
        self.runner('StrainXZ')


if __name__ == '__main__':
    unittest.main()
