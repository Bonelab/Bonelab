from __future__ import annotations

# external imports
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace, ArgumentTypeError
import SimpleITK as sitk
from matplotlib import pyplot as plt
import csv
import yaml
from typing import List, Callable

# internal imports
from bonelab.util.vtk_util import vtkImageData_to_numpy
from bonelab.io.vtk_helpers import get_vtk_reader
from bonelab.util.multiscale_registration import smooth_and_resample, create_metric_tracking_callback


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="blApplyTransform: SimpleITK Transformation Tool.",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "fixed_image", type=str, metavar="FIXED",
        help="path to the fixed image (don't use DICOMs; AIM  or NIfTI should work)"
    )
    parser.add_argument(
        "transform", type=str, metavar="TRANSFORM",
        help="path to the transform, should either be *.mat, *.nii, or *.nii.gz"
    )
    parser.add_argument(
        "output", type=str, metavar="OUTPUT",
        help="path to where you want the transformed image saved, should have a file extension that is either *.aim, "
             "*.AIM, or compatible with sitk.WriteImage"
    )
    parser.add_argument(
        "--moving-image", "-mi", type=str, default=None, metavar="STR",
        help="if given, the fixed image will be resampled onto the moving image using the transform. If you do not "
             "give a moving image then the fixed image will be resampled onto itself using the transform, which could "
             "possibly result in the data going out of the bounds of the image - recommended to provide this since "
             "there should usually be a moving image that you used to get the transform in the first place anyways"
    )
    parser.add_argument(
        "--invert", "-i", default=False, action="store_true",
        help="enable this flag to invert the transform before applying it. you would want to do this if you registered "
             "image A (fixed) to image B (moving) but now you want to transform something from the coordindate system "
             "of image B to image A"
    )
    return parser


def apply_sitk_transform(args: Namespace):
    pass


def main():
    apply_sitk_transform(create_parser().parse_args())


if __name__ == "__main__":
    main()