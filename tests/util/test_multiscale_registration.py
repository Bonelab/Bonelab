from __future__ import annotations

import unittest
from bonelab.util.multiscale_registration import smooth_and_resample, multiscale_registration

import numpy as np
import SimpleITK as sitk

from typing import Tuple


def generate_sitk_image(shape: Tuple[int, int, int]) -> sitk.Image:
    return sitk.GetImageFromArray(np.random.rand(*shape))


class TestSmoothAndResample(unittest.TestCase):

    def test_no_shrink(self):
        shape = (10, 10, 10)
        img = generate_sitk_image(shape)
        resampled_img = smooth_and_resample(img, 1.0, 1.0)
        self.assertEqual(shape, resampled_img.GetSize())

    def test_shrink_by_two(self):
        shape = (10, 10, 10)
        img = generate_sitk_image(shape)
        resampled_img = smooth_and_resample(img, 2.0, 1.0)
        self.assertEqual( (5, 5, 5), resampled_img.GetSize())


class TestMultiscaleRegistration(unittest.TestCase):

    def setUp(self):
        self.registration_filter = sitk.DemonsRegistrationFilter()
        self.registration_filter.SetNumberOfIterations(10)
        self.registration_filter.SetSmoothDisplacementField(True)
        self.registration_filter.SetStandardDeviations(1.0)
        self.registration_filter.SetSmoothUpdateField(True)
        self.registration_filter.SetUpdateFieldStandardDeviations(1.0)

    def test_normal_registration(self):
        shape = (50, 50, 50)
        fixed, moving = generate_sitk_image(shape), generate_sitk_image(shape)
        multiscale_registration(self.registration_filter, fixed, moving)

    def test_one_multiscale_level(self):
        shape = (50, 50, 50)
        multiscale_progression = ((2.0, 1.0),)
        fixed, moving = generate_sitk_image(shape), generate_sitk_image(shape)
        multiscale_registration(
            self.registration_filter, fixed, moving, multiscale_progression=multiscale_progression
        )

    def test_three_multiscale_levels(self):
        shape = (50, 50, 50)
        multiscale_progression = ((2.0, 1.0), (4.0, 2.0), (8.0, 4.0))
        fixed, moving = generate_sitk_image(shape), generate_sitk_image(shape)
        multiscale_registration(
            self.registration_filter, fixed, moving, multiscale_progression=multiscale_progression
        )


class TestMultiscaleDemons(unittest.TestCase):

    def test_demons(self):
        pass

    def test_diffeomorphic(self):
        pass

    def test_symmetric(self):
        pass

    def test_fast_symmetric(self):
        pass


if __name__ == '__main__':
    unittest.main()
