from __future__ import annotations

import unittest
from hypothesis import given, strategies as st
import shutil
import tempfile
import SimpleITK as sitk
import numpy as np

from bonelab.cli.demons_registration import create_parser, demons_registration


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