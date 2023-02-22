from __future__ import annotations

import unittest
from hypothesis import given, strategies as st
import os
import shutil
import tempfile
import SimpleITK as sitk
import numpy as np
import pandas as pd

from bonelab.cli.compute_overlap import create_parser, compute_overlap

IMAGE_SIZE_DICT = {
    "small": 20,
    "medium": 25,
    "big": 30
}

MAX_VALUE = 10

TEST_OUTPUT_LABEL = "test_output.csv"


class TestComputeOverlap(unittest.TestCase):

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
        img1=st.sampled_from(list(IMAGE_SIZE_DICT.keys())),
        img2=st.sampled_from(list(IMAGE_SIZE_DICT.keys())),
        cl=st.lists(st.integers(min_value=1, max_value=MAX_VALUE), min_size=1, max_size=5)
    )
    def test_various_random_images_and_class_labels(self, img1, img2, cl):
        args = [self.random_images[img1], self.random_images[img2], TEST_OUTPUT_LABEL, "-cl", *[str(x) for x in cl]]
        compute_overlap(create_parser().parse_args(args=args))

    def test_full_overlap(self):
        output = "full_overlap.csv"
        mask = np.zeros((5, 5, 5))
        mask[2, 2, 2] = 1
        mask = sitk.GetImageFromArray(mask)
        fn = os.path.join(self.test_dir, "mask.nii")
        sitk.WriteImage(mask, fn)
        args = [fn, fn, output]
        compute_overlap(create_parser().parse_args(args=args))
        df = pd.read_csv(output)
        self.assertAlmostEqual(1.0, df["dice_1"].values[0])
        self.assertAlmostEqual(1.0, df["jaccard_1"].values[0])

    def test_no_overlap(self):
        output = "no_overlap.csv"
        mask = np.zeros((5, 5, 5))
        mask[2, 2, 2] = 1
        opp = 1-mask
        mask = sitk.GetImageFromArray(mask)
        opp = sitk.GetImageFromArray(opp)
        mask_fn = os.path.join(self.test_dir, "mask.nii")
        opp_fn = os.path.join(self.test_dir, "opp.nii")
        sitk.WriteImage(mask, mask_fn)
        sitk.WriteImage(opp, opp_fn)
        args = [mask_fn, opp_fn, output]
        compute_overlap(create_parser().parse_args(args=args))
        df = pd.read_csv(output)
        self.assertAlmostEqual(0.0, df["dice_1"].values[0])
        self.assertAlmostEqual(0.0, df["jaccard_1"].values[0])


if __name__ == '__main__':
    unittest.main()
