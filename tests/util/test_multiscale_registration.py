from __future__ import annotations

import unittest
from hypothesis import given, strategies as st
from bonelab.util.multiscale_registration import (
    smooth_and_resample, multiscale_registration, multiscale_demons, DEMONS_FILTERS
)

import numpy as np
import SimpleITK as sitk

from typing import Tuple


def generate_sitk_image(shape: Tuple[int, int, int]) -> sitk.Image:
    return sitk.GetImageFromArray(np.random.rand(*shape))


class TestSmoothAndResample(unittest.TestCase):

    @given(d=st.integers(min_value=5, max_value=50))
    def test_no_shrink(self, d):
        shape = (d, d, d)
        img = generate_sitk_image(shape)
        resampled_img = smooth_and_resample(img, 1.0, 1.0)
        self.assertEqual(shape, resampled_img.GetSize())

    @given(d=st.integers(min_value=5, max_value=50), s=st.floats(min_value=1.0, max_value=3.0))
    def test_arbitrary_shrinkage(self, d, s):
        shape = (d, d, d)
        img = generate_sitk_image(shape)
        resampled_img = smooth_and_resample(img, s, 1.0)
        self.assertEqual(tuple([int(x / s + 0.5) for x in shape]), resampled_img.GetSize())


class TestMultiscaleRegistration(unittest.TestCase):

    def setUp(self):
        self.registration_filter = sitk.DemonsRegistrationFilter()
        self.registration_filter.SetNumberOfIterations(10)
        self.registration_filter.SetSmoothDisplacementField(True)
        self.registration_filter.SetStandardDeviations(1.0)
        self.registration_filter.SetSmoothUpdateField(True)
        self.registration_filter.SetUpdateFieldStandardDeviations(1.0)

    @given(d=st.integers(min_value=20, max_value=50))
    def test_normal_registration(self, d):
        shape = (d, d, d)
        fixed, moving = generate_sitk_image(shape), generate_sitk_image(shape)
        ddf = multiscale_registration(self.registration_filter, fixed, moving)
        self.assertEqual(ddf.GetSize(), fixed.GetSize())

    @given(d=st.integers(min_value=20, max_value=30), n=st.integers(min_value=1, max_value=3))
    def test_multiscale(self, d, n):
        shape = (d, d, d)
        multiscale_progression = tuple(zip(
            [float((x+1)**2) for x in range(n)], [float((x+1)**2) for x in range(n)]
        ))
        fixed, moving = generate_sitk_image(shape), generate_sitk_image(shape)
        ddf = multiscale_registration(
            self.registration_filter, fixed, moving, multiscale_progression=multiscale_progression
        )
        self.assertEqual(ddf.GetSize(), fixed.GetSize())


class TestMultiscaleDemons(unittest.TestCase):

    @given(
        demons_type=st.sampled_from(list(DEMONS_FILTERS.keys())),
        d=st.integers(min_value=20, max_value=30),
        n=st.integers(min_value=1, max_value=3),
        demons_iterations=st.integers(min_value=1, max_value=10)
    )
    def test_demons(self, demons_type, d, n, demons_iterations):
        shape = (d, d, d)
        multiscale_progression = tuple(zip(
            [float((x + 1) ** 2) for x in range(n)], [float((x + 1) ** 2) for x in range(n)]
        ))
        fixed, moving = generate_sitk_image(shape), generate_sitk_image(shape)
        ddf = multiscale_demons(
            fixed, moving, demons_type, demons_iterations,
            multiscale_progression=multiscale_progression
        )
        self.assertEqual(ddf.GetSize(), fixed.GetSize())


if __name__ == '__main__':
    unittest.main()
