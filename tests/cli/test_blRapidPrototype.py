'''Test blRapidPrototype'''

import unittest
import subprocess
import shutil, tempfile, filecmp, difflib
import os
import numpy.testing as npt

from tests.config_cli import cfg
from bonelab.cli.RapidPrototype import create_cube
from bonelab.cli.RapidPrototype import create_cylinder
from bonelab.cli.RapidPrototype import create_sphere
from bonelab.cli.RapidPrototype import img2stl
from bonelab.cli.RapidPrototype import create_sign

# I should add tests that check boolean_stl and add_stl, but ran out
# of steam for now. June 7, 2020

class TestblRapidPrototype(unittest.TestCase):
    '''Test blRapidPrototype'''
    filenames = [
        'cube_expected.stl',
        'cylinder_expected.stl',
        'sphere_expected.stl',
        'test25a.aim',
        'test25a_expected.stl',
        'sign_expected.stl'
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

    def runner(self, args, expected_file, produced_file, type):
        # Run
        if type in "create_cube":
          create_cube(**args)
        elif type in "create_cylinder":
          create_cylinder(**args)
        elif type in "create_sphere":
          create_sphere(**args)
        elif type in "img2stl":
          img2stl(**args)
        elif type in "create_sign":
          create_sign(**args)
        else:
          raise ValueError('Invalid operation: ' + type)
        
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

    def test_blRapidPrototype_create_cube(self):
        '''`blRapidPrototype` creates a cube STL file'''
        stl_file_expected = os.path.join(self.test_dir, 'cube_expected.stl')
        stl_file_produced = os.path.join(self.test_dir, 'cube.stl')

        args = {
            'func':           create_cube,
            'output_file':    stl_file_produced,
            'transform_file': "None",
            'bounds':         [0,1,0,1,0,1],
            'rotate':         [0,0,0],
            'visualize':      False,
            'overwrite':      False
        }

        self.runner(args, stl_file_expected, stl_file_produced, "create_cube")

    def test_blRapidPrototype_create_cylinder(self):
        '''`blRapidPrototype` creates a cylinder STL file'''
        stl_file_expected = os.path.join(self.test_dir, 'cylinder_expected.stl')
        stl_file_produced = os.path.join(self.test_dir, 'cylinder.stl')

        args = {
            'func':           create_cylinder,
            'output_file':    stl_file_produced,
            'transform_file': "None",
            'radius':         0.5,
            'height':         1.0,
            'resolution':     6,
            'capping':        True,
            'center':         [0,0,0],
            'rotate':         [0,0,0],
            'visualize':      False,
            'overwrite':      False
        }

        self.runner(args, stl_file_expected, stl_file_produced, "create_cylinder")

    def test_blRapidPrototype_create_sphere(self):
        '''`blRapidPrototype` creates a sphere STL file'''
        stl_file_expected = os.path.join(self.test_dir, 'sphere_expected.stl')
        stl_file_produced = os.path.join(self.test_dir, 'sphere.stl')

        args = {
            'func':           create_sphere,
            'output_file':    stl_file_produced,
            'transform_file': "None",
            'radius':         0.5,
            'phi':            8,
            'theta':          8,
            'phi_start':      0,
            'phi_end':        180,
            'theta_start':    0,
            'theta_end':      360,
            'center':         [0,0,0],
            'visualize':      False,
            'overwrite':      False
        }

        self.runner(args, stl_file_expected, stl_file_produced, "create_sphere")

    def test_blRapidPrototype_create_sign(self):
        '''`blRapidPrototype` creates a sign STL file'''
        stl_file_expected = os.path.join(self.test_dir, 'sign_expected.stl')
        stl_file_produced = os.path.join(self.test_dir, 'sign.stl')

        args = {
            'func':           create_sign,
            'output_file':    stl_file_produced,
            'transform_file': "None",
            'text':           "Hello!",
            'width':          10.0,
            'height':         5.0,
            'depth':          0.5,
            'nobacking':      False,
            'visualize':      False,
            'overwrite':      False
        }

        self.runner(args, stl_file_expected, stl_file_produced, "create_sign")

    def test_blRapidPrototype_img2stl(self):
        '''`blRapidPrototype` creates an STL file from AIM'''
        aim = os.path.join(self.test_dir, 'test25a.aim')
        stl_file_expected = os.path.join(self.test_dir, 'test25a_expected.stl')
        stl_file_produced = os.path.join(self.test_dir, 'test25a.stl')
    
        args = {
            'func':           img2stl,
            'input_file':     aim,
            'output_file':    stl_file_produced,
            'transform_file': "None",
            'threshold':      False,
            'gaussian':       0.7,
            'radius':         1.0,
            'marching_cubes': 50.0,
            'decimation':     0.0,
            'visualize':      False,
            'overwrite':      False
        }
    
        self.runner(args, stl_file_expected, stl_file_produced, "img2stl")

    #def test_blRapidPrototype_stl2aim(self):
    #    '''`blRapidPrototype` creates an AIM file from STL'''
    #    stl = os.path.join(self.test_dir, 'globe.stl')
    #    aim_file_expected = os.path.join(self.test_dir, 'globe_expected.aim')
    #    aim_file_produced = os.path.join(self.test_dir, 'globe.aim')
    #
    #    args = {
    #        'func':           stl2aim,
    #        'input_file':     stl,
    #        'output_file':    aim_file_produced,
    #        'transform_file': "None",
    #        'el_size_mm':     [0.0607,0.0607,0.0607],
    #        'visualize':      False,
    #        'overwrite':      False
    #    }
    #
    #    self.runner(args, aim_file_expected, aim_file_produced, "stl2aim")

if __name__ == '__main__':
    unittest.main()
