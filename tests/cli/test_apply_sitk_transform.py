from __future__ import annotations

import unittest
from hypothesis import given, settings, strategies as st
import os
import shutil
import tempfile
import SimpleITK as sitk
import numpy as np

from bonelab.cli.apply_sitk_transform import apply_sitk_transform, create_parser, INTERPOLATORS

HYPOTHESIS_DEADLINE = 2000  # this is how many milliseconds each test has to finish in

IMAGE_SIZE_DICT = {
    "small": 20,
    "medium": 25,
    "big": 30
}

RIGID_TRANSFORM = "rigid.mat"
FIELD_TRANSFORM = "field.nii"
TEST_OUTPUT_LABEL = "test_output.nii"


class TestApplySitkTransform(unittest.TestCase):

    def setUp(self):
        # Create temporary directory to work in
        self.test_dir = tempfile.mkdtemp()
        # write some random images to file and save in a dictionary
        self.random_images = {}
        for image_key, image_size in IMAGE_SIZE_DICT.items():
            arr = np.random.rand(image_size, image_size, image_size)
            img = sitk.GetImageFromArray(arr)
            fn = os.path.join(self.test_dir, f"{image_key}.nii")
            sitk.WriteImage(img, fn)
            self.random_images[image_key] = fn
        # write a no-op rigid transform
        transform = sitk.Euler3DTransform()
        self.rigid_fn = os.path.join(self.test_dir, RIGID_TRANSFORM)
        sitk.WriteTransform(transform, self.rigid_fn)
        # write a no-op field transform
        arr = np.random.rand(5, 5, 5, 3)
        field = sitk.GetImageFromArray(arr)
        self.field_fn = os.path.join(self.test_dir, FIELD_TRANSFORM)
        sitk.WriteImage(field, self.field_fn)

    def tearDown(self):
        # Remove temporary directory and all files
        shutil.rmtree(self.test_dir)

    @settings(deadline=HYPOTHESIS_DEADLINE)
    @given(
        fixed_image=st.sampled_from(list(IMAGE_SIZE_DICT.keys())),
        moving_image=st.sampled_from([None] + list(IMAGE_SIZE_DICT.keys())),
        use_rigid=st.booleans(),
        invert=st.booleans(),
        interpolator=st.sampled_from(list(INTERPOLATORS.keys()))
    )
    def test_everything(self, fixed_image, moving_image, use_rigid, invert, interpolator):
        fixed_image = self.random_images[fixed_image]
        output = os.path.join(self.test_dir, TEST_OUTPUT_LABEL)
        transform = self.rigid_fn if use_rigid else self.field_fn
        args = [f"{fixed_image}", f"{transform}", f"{output}", "-s", "-ow"]
        if moving_image is not None:
            moving_image = self.random_images[moving_image]
            args += ["-fi", f"{moving_image}"]
        if invert:
            args += ["-it"]
        args += ["-int", f"{interpolator}"]
        apply_sitk_transform(create_parser().parse_args(args=args))


if __name__ == '__main__':
    unittest.main()
