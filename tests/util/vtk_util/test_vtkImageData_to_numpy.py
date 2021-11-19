'''Test vtkImageData_to_numpy'''

import unittest
import os
import numpy as np
import numpy.testing as npt
import shutil, tempfile

from tests.config_cli import cfg
from bonelab.util.vtk_util import vtkImageData_to_numpy, numpy_to_vtkImageData
from bonelab.io.vtk_helpers import get_vtk_reader


class TestvtkImageDataToNumpy(unittest.TestCase):
    '''Test vtkImageData_to_numpy'''
    filenames = [
        'test25a.aim'
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

    def test_numpy_consistent(self):
        '''Conversion is consistent with numpy'''
        array = np.arange(2*3*4).reshape(2,3,4)
        image = numpy_to_vtkImageData(array)
        array2 = vtkImageData_to_numpy(image)

        npt.assert_array_almost_equal(image.GetDimensions(), array.shape)
        npt.assert_array_almost_equal(array2.shape, array.shape)

        for index, x in np.ndenumerate(array):
            self.assertAlmostEqual(array[index], image.GetScalarComponentAsDouble(*index, 0))
            self.assertAlmostEqual(array[index], array2[index])

    def test_image_data(self):
        '''Correctly works on image data'''
        filename = os.path.join(self.test_dir, 'test25a.aim')
        r = get_vtk_reader(filename)
        r.SetFileName(filename)
        r.Update()

        array = vtkImageData_to_numpy(r.GetOutput())

        npt.assert_array_almost_equal(array.shape, [25, 25, 25])

        test_points = [
            [   (0, 0, 0),    127  ],
            [   (0, 0, 24),   0    ],
            [   (20, 21, 23), 0    ]
        ]

        for index, value in test_points:
            self.assertAlmostEqual(array[index], value)


if __name__ == '__main__':
    unittest.main()
