from __future__ import annotations

import unittest
from hypothesis import given, strategies as st
import os
import shutil
import tempfile
import SimpleITK as sitk
import numpy as np

from bonelab.cli.mirror_image import create_parser, mirror_image

IMAGE_SIZE_DICT = {
    "small": 20,
    "medium": 25,
    "big": 30
}

MAX_VALUE = 10

MIN_AXIS = 0
MAX_AXIS = 2

TEST_OUTPUT_LABEL = "test_output.nii"


class TestMirrorImage(unittest.TestCase):

    def setUp(self):
        # Create temporary directory to work in
        self.test_dir = tempfile.mkdtemp()
        # write some random images to file and save in a dictionary
        self.random_images = {}
        for image_key, image_size in IMAGE_SIZE_DICT.items():
            arr = (MAX_VALUE * np.random.rand(image_size, image_size, image_size)).astype(int)
            img = sitk.GetImageFromArray(arr)
            fn = os.path.join(self.test_dir, f"{image_key}.nii")
            sitk.WriteImage(img, fn)
            self.random_images[image_key] = fn

    def tearDown(self):
        # Remove temporary directory and all files
        shutil.rmtree(self.test_dir)

    @given(
        img=st.sampled_from(list(IMAGE_SIZE_DICT.keys())),
        axis=st.integers(min_value=MIN_AXIS, max_value=MAX_AXIS)
    )
    def test_axes(self, img, axis):
        output = os.path.join(self.test_dir, TEST_OUTPUT_LABEL)
        args = [self.random_images[img], str(axis), output, "-s", "-ow"]
        mirror_image(create_parser().parse_args(args=args))


if __name__ == '__main__':
    unittest.main()
