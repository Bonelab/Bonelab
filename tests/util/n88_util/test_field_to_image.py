'''Test n88_util field_to_image'''

import unittest
import subprocess
import shutil, tempfile
import os
from netCDF4 import Dataset
import numpy.testing as npt

from tests.config_cli import cfg
from bonelab.util.n88_util import field_to_image


class TestFieldToImage(unittest.TestCase):
    '''Test n88_util field_to_image'''
    filenames = [
        'test25a_uniaxial.n88model',
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

    def test_throw_error_on_unsolved_model(self):
        '''Throw error on unsolved model'''
        def instantiate():
            field_to_image(os.path.join(self.test_dir, 'test25a_uniaxial.n88model'), 'StrainEnergyDensity')
        self.assertRaises(IndexError, instantiate)

    def test_throw_error_on_bad_field_name(self):
        '''Throw error on bad field name'''
        def instantiate():
            field_to_image(os.path.join(self.test_dir, 'test25a_uniaxial_solved.n88model'), 'fake_field_name')
        self.assertRaises(IndexError, instantiate)

    def test_extract_strain_energy_density(self):
        '''Correctly extract SED'''
        field_name = 'StrainEnergyDensity'
        image, spacing, origin, n_elements = field_to_image(os.path.join(self.test_dir, 'test25a_uniaxial_solved.n88model'), field_name)
        
        npt.assert_array_equal(image.shape, [25, 25, 25])
        npt.assert_array_almost_equal(spacing, [0.03399992, 0.03399992, 0.03400004])
        npt.assert_array_almost_equal(origin, [6.64700055, 7.22500014, 1.71700007])
        self.assertEqual(n_elements, 7087)

        test_points = [
            [   (0, 0, 0),    0.2371111661195755  ],
            [   (0, 0, 24),   0    ],
            [   (20, 21, 23), 0    ],
            [   (6, 18, 23),  1.401611566543579   ],
            [   (15, 9, 24),  0.0   ],
            [   (5, 6, 17),   1.262300968170166   ]
        ]

        for index, value in test_points:
            self.assertAlmostEqual(image[index], value)

    def test_extract_strain_energy_density_outside_value(self):
        '''Correctly extract SED with outside value'''
        field_name = 'StrainEnergyDensity'
        image, spacing, origin, n_elements = field_to_image(os.path.join(self.test_dir, 'test25a_uniaxial_solved.n88model'), field_name, outside_value=-10.0)
        
        npt.assert_array_equal(image.shape, [25, 25, 25])
        npt.assert_array_almost_equal(spacing, [0.03399992, 0.03399992, 0.03400004])
        npt.assert_array_almost_equal(origin, [6.64700055, 7.22500014, 1.71700007])
        self.assertEqual(n_elements, 7087)

        test_points = [
            [   (0, 0, 0),    0.2371111661195755  ],
            [   (0, 0, 24),   -10.0    ],
            [   (20, 21, 23), -10.0    ],
            [   (6, 18, 23),  1.401611566543579   ],
            [   (15, 9, 24),  -10.0   ],
            [   (5, 6, 17),   1.262300968170166   ]
        ]

        for index, value in test_points:
            self.assertAlmostEqual(image[index], value)

    def test_extract_von_mises_stress(self):
        '''Correctly extract VonMisesStress'''
        field_name = 'VonMisesStress'
        image, spacing, origin, n_elements = field_to_image(os.path.join(self.test_dir, 'test25a_uniaxial_solved.n88model'), field_name)
        
        npt.assert_array_equal(image.shape, [25, 25, 25])
        npt.assert_array_almost_equal(spacing, [0.03399992, 0.03399992, 0.03400004])
        npt.assert_array_almost_equal(origin, [6.64700055, 7.22500014, 1.71700007])
        self.assertEqual(n_elements, 7087)

        test_points = [
            [   (0, 0, 0),    57.127845764160156  ],
            [   (0, 0, 24),   0    ],
            [   (20, 21, 23), 0    ],
            [   (6, 18, 23),  131.52987670898438  ],
            [   (15, 9, 24),  0.0   ],
            [   (5, 6, 17),   124.15428161621094  ]
        ]

        for index, value in test_points:
            self.assertAlmostEqual(image[index], value)

    def test_extract_stress_xx(self):
        '''Correctly extract StressXX'''
        field_name = 'StressXX'
        image, spacing, origin, n_elements = field_to_image(os.path.join(self.test_dir, 'test25a_uniaxial_solved.n88model'), field_name)
        
        npt.assert_array_equal(image.shape, [25, 25, 25])
        npt.assert_array_almost_equal(spacing, [0.03399992, 0.03399992, 0.03400004])
        npt.assert_array_almost_equal(origin, [6.64700055, 7.22500014, 1.71700007])
        self.assertEqual(n_elements, 7087)

        test_points = [
            [   (0, 0, 0),    0.3343238830566406  ],
            [   (0, 0, 24),   0    ],
            [   (20, 21, 23), 0    ],
            [   (6, 18, 23),  -8.079221725463867  ],
            [   (15, 9, 24),  0.0   ],
            [   (5, 6, 17),   -16.37940216064453  ]
        ]

        for index, value in test_points:
            self.assertAlmostEqual(image[index], value)

    def test_extract_stress_yy(self):
        '''Correctly extract StressYY'''
        field_name = 'StressYY'
        image, spacing, origin, n_elements = field_to_image(os.path.join(self.test_dir, 'test25a_uniaxial_solved.n88model'), field_name)
        
        npt.assert_array_equal(image.shape, [25, 25, 25])
        npt.assert_array_almost_equal(spacing, [0.03399992, 0.03399992, 0.03400004])
        npt.assert_array_almost_equal(origin, [6.64700055, 7.22500014, 1.71700007])
        self.assertEqual(n_elements, 7087)

        test_points = [
            [   (0, 0, 0),    0.7583122253417969  ],
            [   (0, 0, 24),   0    ],
            [   (20, 21, 23), 0    ],
            [   (6, 18, 23),  -27.049179077148438 ],
            [   (15, 9, 24),  0.0   ],
            [   (5, 6, 17),   -24.753982543945312 ]
        ]

        for index, value in test_points:
            self.assertAlmostEqual(image[index], value)

    def test_extract_stress_zz(self):
        '''Correctly extract StressZZ'''
        field_name = 'StressZZ'
        image, spacing, origin, n_elements = field_to_image(os.path.join(self.test_dir, 'test25a_uniaxial_solved.n88model'), field_name)
        
        npt.assert_array_equal(image.shape, [25, 25, 25])
        npt.assert_array_almost_equal(spacing, [0.03399992, 0.03399992, 0.03400004])
        npt.assert_array_almost_equal(origin, [6.64700055, 7.22500014, 1.71700007])
        self.assertEqual(n_elements, 7087)

        test_points = [
            [   (0, 0, 0),    -56.54663848876953  ],
            [   (0, 0, 24),   0    ],
            [   (20, 21, 23), 0    ],
            [   (6, 18, 23),  -141.2898406982422  ],
            [   (15, 9, 24),  0.0   ],
            [   (5, 6, 17),   -129.48597717285156 ]
        ]

        for index, value in test_points:
            self.assertAlmostEqual(image[index], value)

    def test_extract_stress_xy(self):
        '''Correctly extract StressXY'''
        field_name = 'StressXY'
        image, spacing, origin, n_elements = field_to_image(os.path.join(self.test_dir, 'test25a_uniaxial_solved.n88model'), field_name)
        
        npt.assert_array_equal(image.shape, [25, 25, 25])
        npt.assert_array_almost_equal(spacing, [0.03399992, 0.03399992, 0.03400004])
        npt.assert_array_almost_equal(origin, [6.64700055, 7.22500014, 1.71700007])
        self.assertEqual(n_elements, 7087)

        test_points = [
            [   (0, 0, 0),    0.20011991262435913 ],
            [   (0, 0, 24),   0    ],
            [   (20, 21, 23), 0    ],
            [   (6, 18, 23),  21.707307815551758  ],
            [   (15, 9, 24),  0.0   ],
            [   (5, 6, 17),   -31.890914916992188 ]
        ]

        for index, value in test_points:
            self.assertAlmostEqual(image[index], value)

    def test_extract_stress_yz(self):
        '''Correctly extract StressYZ'''
        field_name = 'StressYZ'
        image, spacing, origin, n_elements = field_to_image(os.path.join(self.test_dir, 'test25a_uniaxial_solved.n88model'), field_name)
        
        npt.assert_array_equal(image.shape, [25, 25, 25])
        npt.assert_array_almost_equal(spacing, [0.03399992, 0.03399992, 0.03400004])
        npt.assert_array_almost_equal(origin, [6.64700055, 7.22500014, 1.71700007])
        self.assertEqual(n_elements, 7087)

        test_points = [
            [   (0, 0, 0),    0.6589500308036804 ],
            [   (0, 0, 24),   0    ],
            [   (20, 21, 23), 0    ],
            [   (6, 18, 23),  10.11087703704834  ],
            [   (15, 9, 24),  0.0   ],
            [   (5, 6, 17),   -11.253583908081055 ]
        ]

        for index, value in test_points:
            self.assertAlmostEqual(image[index], value)

    def test_extract_stress_xz(self):
        '''Correctly extract StressXZ'''
        field_name = 'StressXZ'
        image, spacing, origin, n_elements = field_to_image(os.path.join(self.test_dir, 'test25a_uniaxial_solved.n88model'), field_name)
        
        npt.assert_array_equal(image.shape, [25, 25, 25])
        npt.assert_array_almost_equal(spacing, [0.03399992, 0.03399992, 0.03400004])
        npt.assert_array_almost_equal(origin, [6.64700055, 7.22500014, 1.71700007])
        self.assertEqual(n_elements, 7087)

        test_points = [
            [   (0, 0, 0),    -0.899536669254303 ],
            [   (0, 0, 24),   0    ],
            [   (20, 21, 23), 0    ],
            [   (6, 18, 23),  0.7890536785125732 ],
            [   (15, 9, 24),  0.0   ],
            [   (5, 6, 17),   -4.734708309173584 ]
        ]

        for index, value in test_points:
            self.assertAlmostEqual(image[index], value)

    def test_extract_strain_xx(self):
        '''Correctly extract StrainXX'''
        field_name = 'StrainXX'
        image, spacing, origin, n_elements = field_to_image(os.path.join(self.test_dir, 'test25a_uniaxial_solved.n88model'), field_name)
        
        npt.assert_array_equal(image.shape, [25, 25, 25])
        npt.assert_array_almost_equal(spacing, [0.03399992, 0.03399992, 0.03400004])
        npt.assert_array_almost_equal(origin, [6.64700055, 7.22500014, 1.71700007])
        self.assertEqual(n_elements, 7087)

        test_points = [
            [   (0, 0, 0),    0.0024997536092996597 ],
            [   (0, 0, 24),   0    ],
            [   (20, 21, 23), 0    ],
            [   (6, 18, 23),  0.006212107837200165  ],
            [   (15, 9, 24),  0.0   ],
            [   (5, 6, 17),   0.004377299919724464  ]
        ]

        for index, value in test_points:
            self.assertAlmostEqual(image[index], value)

    def test_extract_strain_yy(self):
        '''Correctly extract StrainYY'''
        field_name = 'StrainYY'
        image, spacing, origin, n_elements = field_to_image(os.path.join(self.test_dir, 'test25a_uniaxial_solved.n88model'), field_name)
        
        npt.assert_array_equal(image.shape, [25, 25, 25])
        npt.assert_array_almost_equal(spacing, [0.03399992, 0.03399992, 0.03400004])
        npt.assert_array_almost_equal(origin, [6.64700055, 7.22500014, 1.71700007])
        self.assertEqual(n_elements, 7087)

        test_points = [
            [   (0, 0, 0),    0.002580466214567423  ],
            [   (0, 0, 24),   0    ],
            [   (20, 21, 23), 0    ],
            [   (6, 18, 23),  0.0026008994318544865 ],
            [   (15, 9, 24),  0.0   ],
            [   (5, 6, 17),   0.0027830759063363075 ]
        ]

        for index, value in test_points:
            self.assertAlmostEqual(image[index], value)

    def test_extract_strain_zz(self):
        '''Correctly extract StrainZZ'''
        field_name = 'StrainZZ'
        image, spacing, origin, n_elements = field_to_image(os.path.join(self.test_dir, 'test25a_uniaxial_solved.n88model'), field_name)
        
        npt.assert_array_equal(image.shape, [25, 25, 25])
        npt.assert_array_almost_equal(spacing, [0.03399992, 0.03399992, 0.03400004])
        npt.assert_array_almost_equal(origin, [6.64700055, 7.22500014, 1.71700007])
        self.assertEqual(n_elements, 7087)

        test_points = [
            [   (0, 0, 0),    -0.00832836702466011  ],
            [   (0, 0, 24),   0    ],
            [   (20, 21, 23), 0    ],
            [   (6, 18, 23),  -0.019146479666233063  ],
            [   (15, 9, 24),  0.0   ],
            [   (5, 6, 17),   -0.017154186964035034 ]
        ]

        for index, value in test_points:
            self.assertAlmostEqual(image[index], value)

    def test_extract_strain_xy(self):
        '''Correctly extract StrainXY'''
        field_name = 'StrainXY'
        image, spacing, origin, n_elements = field_to_image(os.path.join(self.test_dir, 'test25a_uniaxial_solved.n88model'), field_name)
        
        npt.assert_array_equal(image.shape, [25, 25, 25])
        npt.assert_array_almost_equal(spacing, [0.03399992, 0.03399992, 0.03400004])
        npt.assert_array_almost_equal(origin, [6.64700055, 7.22500014, 1.71700007])
        self.assertEqual(n_elements, 7087)

        test_points = [
            [   (0, 0, 0),    7.61914998292923e-05 ],
            [   (0, 0, 24),   0    ],
            [   (20, 21, 23), 0    ],
            [   (6, 18, 23),  0.008264606818556786  ],
            [   (15, 9, 24),  0.0   ],
            [   (5, 6, 17),   -0.012141803279519081 ]
        ]

        for index, value in test_points:
            self.assertAlmostEqual(image[index], value)

    def test_extract_strain_yz(self):
        '''Correctly extract StrainYZ'''
        field_name = 'StrainYZ'
        image, spacing, origin, n_elements = field_to_image(os.path.join(self.test_dir, 'test25a_uniaxial_solved.n88model'), field_name)
        
        npt.assert_array_equal(image.shape, [25, 25, 25])
        npt.assert_array_almost_equal(spacing, [0.03399992, 0.03399992, 0.03400004])
        npt.assert_array_almost_equal(origin, [6.64700055, 7.22500014, 1.71700007])
        self.assertEqual(n_elements, 7087)

        test_points = [
            [   (0, 0, 0),    0.00025088153779506683 ],
            [   (0, 0, 24),   0    ],
            [   (20, 21, 23), 0    ],
            [   (6, 18, 23),  0.003849506378173828  ],
            [   (15, 9, 24),  0.0   ],
            [   (5, 6, 17),   -0.004284568130970001 ]
        ]

        for index, value in test_points:
            self.assertAlmostEqual(image[index], value)

    def test_extract_strain_xz(self):
        '''Correctly extract StrainXZ'''
        field_name = 'StrainXZ'
        image, spacing, origin, n_elements = field_to_image(os.path.join(self.test_dir, 'test25a_uniaxial_solved.n88model'), field_name)
        
        npt.assert_array_equal(image.shape, [25, 25, 25])
        npt.assert_array_almost_equal(spacing, [0.03399992, 0.03399992, 0.03400004])
        npt.assert_array_almost_equal(origin, [6.64700055, 7.22500014, 1.71700007])
        self.assertEqual(n_elements, 7087)

        test_points = [
            [   (0, 0, 0),    -0.000342479906976223 ],
            [   (0, 0, 24),   0    ],
            [   (20, 21, 23), 0    ],
            [   (6, 18, 23),  0.0003004157915711403 ],
            [   (15, 9, 24),  0.0   ],
            [   (5, 6, 17),   -0.001802641898393631 ]
        ]

        for index, value in test_points:
            self.assertAlmostEqual(image[index], value)


if __name__ == '__main__':
    unittest.main()
