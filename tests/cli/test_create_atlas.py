from __future__ import annotations

import unittest
from hypothesis import given, strategies as st
import os
import shutil
import tempfile
import numpy as np
import SimpleITK as sitk
from scipy.interpolate import Rbf

from bonelab.cli.create_atlas import create_parser, create_atlas

HYPOTHESIS_DEADLINE = 2000  # this is how many milliseconds each test has to finish in

TEST_OUTPUT_ATLAS = "average.nii"
TEST_OUTPUT_MASK = "mask.nii.gz"

# set this low so that testing goes quickly
DEFAULT_ITERATIONS = 10


def generate_random_deformation_field(field_shape: Tuple[int], scale: float, num_grid_points: int) -> np.ndarray:
    dim = len(field_shape)
    if (dim < 2) or (dim > 3):
        raise ValueError(f"length of `field_shape` should be 2 or 3, got {dim}")
    low_res_points = np.meshgrid(*[np.linspace(0, s-1, num_grid_points) for s in field_shape])
    # low_res_field = np.random.normal(loc=0, scale=scale, size=(*tuple(reversed(low_res_points[0].shape)), dim))
    low_res_points = [lrp.flatten() for lrp in low_res_points]
    low_res_field = np.random.normal(loc=0, scale=scale, size=(low_res_points[0].shape[0], dim))

    interpolator = Rbf(*low_res_points, low_res_field, mode="N-D")

    field_points = np.meshgrid(*[np.arange(0, s) for s in field_shape])
    return interpolator(*field_points)


class TestCreateAtlas(unittest.TestCase):
    def setUp(self):
        # Create temporary directory to work in
        self.test_dir = tempfile.mkdtemp()

        # test image set parameters
        obj_shape = (15, 15, 15)
        obj_intercept = 100.0
        obj_coeffs = (50.0, 50.0, 50.0)

        pad_amount = 6

        noise_magnitude = 100.0

        num_images = 5

        deformation_scale = 2
        deformation_grid_points = 3

        xyz = np.meshgrid(*[np.arange(s) for s in obj_shape])
        obj_arr = obj_intercept
        for (x, coeff) in zip(xyz, obj_coeffs):
            obj_arr += coeff * x

        self.img_list = []
        self.mask_list = []

        for i in range(num_images):
            img = np.pad(obj_arr, pad_amount, "constant")
            mask = (img >= obj_intercept).astype(float)
            img += noise_magnitude * np.random.rand(*img.shape)
            img, mask = sitk.GetImageFromArray(img), sitk.GetImageFromArray(mask)
            transform = sitk.DisplacementFieldTransform(sitk.GetImageFromArray(
                generate_random_deformation_field(img.GetSize(), deformation_scale, deformation_grid_points)
            ))
            if i > 0:
                img = sitk.Resample(img, transform, sitk.sitkLinear)
                mask = sitk.Resample(mask, transform, sitk.sitkNearestNeighbor)
            self.img_list.append(os.path.join(self.test_dir, f"image_{i}.nii"))
            self.mask_list.append(os.path.join(self.test_dir, f"mask_{i}.nii.gz"))
            sitk.WriteImage(img, os.path.join(self.test_dir, f"image_{i}.nii"))
            sitk.WriteImage(mask, os.path.join(self.test_dir, f"mask_{i}.nii.gz"))

    def tearDown(self):
        # Remove temporary directory and all files
        shutil.rmtree(self.test_dir)

    def test_can_run(self):
        output_atlas = os.path.join(self.test_dir, TEST_OUTPUT_ATLAS)
        output_mask = os.path.join(self.test_dir, TEST_OUTPUT_MASK)
        args = [
            output_atlas, output_mask,
            "-img", *self.img_list,
            "-seg", *self.mask_list,
            "-ow", "-s", "-opt", "Powell",
            "-ai", "10", "-mai", "10", "-mdi", "10"
        ]
        create_atlas(create_parser().parse_args(args=args))


if __name__ == '__main__':
    unittest.main()
