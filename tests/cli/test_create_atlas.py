from __future__ import annotations

import unittest
from hypothesis import given, strategies as st
import os
import shutil
import tempfile
import SimpleITK as sitk
import numpy as np
import pandas as pd

from bonelab.cli.create_atlas import create_parser, create_atlas


class TestCreateAtlas(unittest.TestCase):
    pass


if __name__ == '__main__':
    unittest.main()
