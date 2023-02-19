from __future__ import annotations

import unittest
from hypothesis import given, strategies as st
import os
import shutil
import tempfile
import SimpleITK as sitk
import numpy as np

from bonelab.cli.registration import create_parser, registration


IMAGE_SIZE_DICT = {
    "small": 10,
    "medium": 15,
    "big": 20
}


class TestRegistration(unittest.TestCase):

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

    @given(
        fixed_image=st.sampled_from(list(IMAGE_SIZE_DICT.keys())),
        moving_image=st.sampled_from(list(IMAGE_SIZE_DICT.keys()))
    )
    def test_default(self, fixed_image, moving_image):
        output = os.path.join(self.test_dir, "test_output")
        args = [self.random_images[fixed_image], self.random_images[moving_image], output]
        registration(create_parser().parse_args(args=args))


if __name__ == '__main__':
    unittest.main()
