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
    "small": 20,
    "medium": 25,
    "big": 30
}

TEST_OUTPUT_LABEL = "test_output"

# set this low so that testing goes quickly
DEFAULT_ITERATIONS = 10


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
        registration(create_parser().parse_args(args=args))

    @given(
        fixed_image=st.sampled_from(list(IMAGE_SIZE_DICT.keys())),
        moving_image=st.sampled_from(list(IMAGE_SIZE_DICT.keys())),
        output_format=st.sampled_from(["transform", "image", "compressed-image"])
    )
    def test_output_formats(self, fixed_image, moving_image, output_format):
        args = self._construct_default_args(fixed_image, moving_image) + ["-of", output_format]
        registration(create_parser().parse_args(args=args))

    @given(
        fixed_image=st.sampled_from(list(IMAGE_SIZE_DICT.keys())),
        moving_image=st.sampled_from(list(IMAGE_SIZE_DICT.keys())),
        downsampling=st.integers(min_value=2, max_value=4)
    )
    def test_downsampling(self, fixed_image, moving_image, downsampling):
        args = (
            self._construct_default_args(fixed_image, moving_image)
            + ["-dsf", f"{downsampling}", "-dss", f"{downsampling}"]
        )
        registration(create_parser().parse_args(args=args))

    @given(
        fixed_image=st.sampled_from(list(IMAGE_SIZE_DICT.keys())),
        moving_image=st.sampled_from(list(IMAGE_SIZE_DICT.keys())),
        n=st.integers(min_value=2, max_value=4)
    )
    def test_multiscale(self, fixed_image, moving_image, n):
        shrink_factors = [int(2 ** (x + 1)) for x in range(n)]
        smoothing_sigmas = [float(2 ** (x + 1)) for x in range(n)]
        args = (
                self._construct_default_args(fixed_image, moving_image)
                + ["-sf"] + [f"{sf}" for sf in shrink_factors]
                + ["-ss"] + [f"{ss}" for ss in smoothing_sigmas]
        )
        # we want this to either succeed, or to fail because we correctly caught that the user gave a combination
        # of a small image and a big shrink factor. any other error is not OK though
        try:
            registration(create_parser().parse_args(args=args))
        except RuntimeError as err:
            if "image sizes and shrink factors" not in str(err):
                raise err

    @given(
        fixed_image=st.sampled_from(list(IMAGE_SIZE_DICT.keys())),
        moving_image=st.sampled_from(list(IMAGE_SIZE_DICT.keys())),
        gdlr=st.floats(min_value=1e-6, max_value=1e-2),
        gdcmv=st.floats(min_value=1e-6, max_value=1e-2),
        gdcws=st.integers(min_value=3, max_value=20)
    )
    def test_gradient_descent(self, fixed_image, moving_image, gdlr, gdcmv, gdcws):
        args = (
            self._construct_default_args(fixed_image, moving_image)
            + ["-opt", "GradientDescent"]
            + ["-gdlr", f"{gdlr}", "-gdcmv", f"{gdcmv}", "-gdcws", f"{gdcws}"]
        )
        registration(create_parser().parse_args(args=args))

    @given(
        fixed_image=st.sampled_from(list(IMAGE_SIZE_DICT.keys())),
        moving_image=st.sampled_from(list(IMAGE_SIZE_DICT.keys())),
        pmli=st.integers(min_value=10, max_value=20),
        psl=st.floats(min_value=0.1, max_value=10.0),
        pst=st.floats(min_value=1e-8, max_value=1e-4),
        pvt=st.floats(min_value=1e-8, max_value=1e-4),
    )
    def test_powell(self, fixed_image, moving_image, pmli, psl, pst, pvt):
        args = (
            self._construct_default_args(fixed_image, moving_image)
            + ["-opt", "Powell", "-dsf", "2", "-dss", f"2.0"]
            + ["-pmli", f"{pmli}", "-psl", f"{psl}", "-pst", f"{pst}", "-pvt", f"{pvt}"]
        )
        registration(create_parser().parse_args(args=args))

    @given(
        fixed_image=st.sampled_from(list(IMAGE_SIZE_DICT.keys())),
        moving_image=st.sampled_from(list(IMAGE_SIZE_DICT.keys())),
        sm=st.sampled_from(
            ["MeanSquares", "Correlation", "JointHistogramMutualInformation", "MattesMutualInformation"]
        ),
        smss=st.sampled_from(["None", "Regular", "Random"]),
        smsr=st.floats(min_value=0.01, max_value=1.0),
        smssd=st.integers(min_value=1, max_value=255),
        minhb=st.integers(min_value=10, max_value=20),
        jmijsv=st.floats(min_value=0.5, max_value=2.0)
    )
    def test_similarity_metrics(self, fixed_image, moving_image, sm, smss, smsr, smssd, minhb, jmijsv):
        args = (
            self._construct_default_args(fixed_image, moving_image)
            + ["-sm", f"{sm}", "-dsf", "2", "-dss", f"2.0"]
            + ["-smss", f"{smss}", "-smsr", f"{smsr}", "-smssd", f"{smssd}"]
            + ["-minhb", f"{minhb}", "-jmijsv", f"{jmijsv}"]
        )
        registration(create_parser().parse_args(args=args))

    @given(
        fixed_image=st.sampled_from(list(IMAGE_SIZE_DICT.keys())),
        moving_image=st.sampled_from(list(IMAGE_SIZE_DICT.keys())),
        interpolator=st.sampled_from(["Linear", "NearestNeighbour", "BSpline"])
    )
    def test_interpolator(self, fixed_image, moving_image, interpolator):
        args = self._construct_default_args(fixed_image, moving_image) + ["-int", f"{interpolator}"]
        registration(create_parser().parse_args(args=args))

    @given(
        fixed_image=st.sampled_from(list(IMAGE_SIZE_DICT.keys())),
        moving_image=st.sampled_from(list(IMAGE_SIZE_DICT.keys())),
        initialization=st.sampled_from(["Geometry", "Moments"])
    )
    def test_initialization(self, fixed_image, moving_image, initialization):
        args = self._construct_default_args(fixed_image, moving_image) + ["-ci", f"{initialization}"]
        registration(create_parser().parse_args(args=args))


if __name__ == '__main__':
    unittest.main()
