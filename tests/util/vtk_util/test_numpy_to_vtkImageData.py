'''Test numpy_to_vtkImageData'''

import unittest
import os
import numpy as np
import numpy.testing as npt

from bonelab.util.vtk_util import numpy_to_vtkImageData


class TestNumpyTovtkImageData(unittest.TestCase):
    '''Test numpy_to_vtkImageData'''

    def test_3d_array(self):
        '''Correctly convert 3D array'''
        array = np.arange(2*3*4).reshape(2,3,4)
        image = numpy_to_vtkImageData(array)

        npt.assert_array_almost_equal(image.GetDimensions(), array.shape)

        for index, x in np.ndenumerate(array):
            self.assertAlmostEqual(array[index], image.GetScalarComponentAsDouble(*index, 0))

    def test_3d_array_spacing(self):
        '''Correctly set spacing'''
        array = np.arange(2*3*4).reshape(2,3,4)
        image = numpy_to_vtkImageData(array, spacing=[2.0, 3.0, 4.0])
        npt.assert_array_almost_equal(image.GetSpacing(), [2.0, 3.0, 4.0])

    def test_3d_array_origin(self):
        '''Correctly set origin'''
        array = np.arange(2*3*4).reshape(2,3,4)
        image = numpy_to_vtkImageData(array, origin=[-12.0, 33.0, 104.0])
        npt.assert_array_almost_equal(image.GetOrigin(), [-12.0, 33.0, 104.0])


if __name__ == '__main__':
    unittest.main()
