'''Test points IO'''

import unittest
import subprocess
import shutil, tempfile, filecmp
import os
import numpy as np

from bonelab.io.points import write_points, read_points

class TestPointsIO(unittest.TestCase):
    '''Test points IO'''

    def setUp(self):
        # Create temporary directory to work in
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove temporary directory and all files
        shutil.rmtree(self.test_dir)

    def test_write_points(self):
        '''write_points correctly writes points'''
        filename = os.path.join(self.test_dir, 'points.txt')
        points = [
            [10, 11, 12],
            [10.1, 12.2, 13.3],
            [-10.1, -0.0, 11]
        ]
        write_points(points, filename, precision=2)

        self.assertTrue(os.path.isfile(filename))
        
        expected_filename = os.path.join(self.test_dir, 'points_expected.txt')
        with open(expected_filename, 'w') as f:
            f.write('10.00,11.00,12.00' + os.linesep)
            f.write('10.10,12.20,13.30' + os.linesep)
            f.write('-10.10,-0.00,11.00' + os.linesep)

        with open(filename, 'r') as f:
            print(f.read())
        with open(expected_filename, 'r') as f:
            print(f.read())
        
        self.assertTrue(filecmp.cmp(filename, expected_filename), 'Files are not the same')

    def test_read_points(self):
        '''read_points correctly writes points'''
        filename = os.path.join(self.test_dir, 'points_expected.txt')
        with open(filename, 'w') as f:
            f.write('10.00,11.00,12.00' + os.linesep)
            f.write('10.10,12.20,13.30' + os.linesep)
            f.write('-10.10,-0.00,11.00' + os.linesep)

        points = read_points(filename)
        self.assertEqual(len(points), 3)

        expected_points = [
            [10, 11, 12],
            [10.1, 12.2, 13.3],
            [-10.1, -0.0, 11]
        ]
        self.assertTrue(np.allclose(points, expected_points))

    def test_delimiter(self):
        '''works with different delimiter'''
        delimiter = ';'
        points = [
            [0,0,0],
            [-10, 11, 12],
            [0.8, 9.1234, 12341234.12341234]
        ]
        filename = os.path.join(self.test_dir, 'points.txt')

        write_points(points, filename, precision=20, delimiter=delimiter)
        self.assertTrue(os.path.isfile(filename))

        new_points = read_points(filename, delimiter=delimiter)
        self.assertEqual(len(points), 3)

        self.assertTrue(np.allclose(points, new_points))


if __name__ == '__main__':
    unittest.main()
