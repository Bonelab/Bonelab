from __future__ import annotations

import unittest
from hypothesis import given, strategies as st
import os
import shutil
import tempfile
import SimpleITK as sitk
import numpy as np

from bonelab.cli.demons_registration import create_parser, demons_registration


IMAGE_SIZE_DICT = {
    "small": 20,
    "medium": 25,
    "big": 30
}

TEST_OUTPUT_LABEL = "test_output"

# set this low so that testing goes quickly
DEFAULT_ITERATIONS = 10

"""
We probably want to do something like this here to test that we can load a transform
    @given(
        fixed_image=st.sampled_from(list(IMAGE_SIZE_DICT.keys())),
        moving_image=st.sampled_from(list(IMAGE_SIZE_DICT.keys()))
    )
    def test_default_then_load_transform(self, fixed_image, moving_image):
        args = self._construct_default_args(fixed_image, moving_image)
        registration(create_parser().parse_args(args=args))
        args += ["-it", os.path.join(self.test_dir, f"{TEST_OUTPUT_LABEL}.mat")]
        registration(create_parser().parse_args(args=args))
"""


class TestDemonsRegistration(unittest.TestCase):

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

    def tearDown(self):
        # Remove temporary directory and all files
        shutil.rmtree(self.test_dir)

    def _construct_default_args(self, fixed_image: str, moving_image: str) -> List[str]:
        output = os.path.join(self.test_dir, TEST_OUTPUT_LABEL)
        return [
            self.random_images[fixed_image], self.random_images[moving_image], output,
            "-mi", f"{DEFAULT_ITERATIONS}"
        ]

    @given(
        fixed_image=st.sampled_from(list(IMAGE_SIZE_DICT.keys())),
        moving_image=st.sampled_from(list(IMAGE_SIZE_DICT.keys()))
    )
    def test_default(self, fixed_image, moving_image):
        args = self._construct_default_args(fixed_image, moving_image)
        demons_registration(create_parser().parse_args(args=args))


if __name__ == '__main__':
    unittest.main()
