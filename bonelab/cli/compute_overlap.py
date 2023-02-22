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
        description="blComputeOverlap: SimpleITK Overlap Computing Tool.",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    return parser


def compute_overlap(args: Namespace):
    pass


def main():
    compute_overlap(create_parser().parse_args())


if __name__ == "__main__":
    main()
