from __future__ import annotations

import unittest
from hypothesis import given, strategies as st
import shutil
import tempfile
import SimpleITK as sitk
import numpy as np

from bonelab.cli.demons_registration import create_parser, demons_registration

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

    def tearDown(self):
        # Remove temporary directory and all files
        shutil.rmtree(self.test_dir)

    def test_default(self):
        pass


if __name__ == '__main__':
    unittest.main()