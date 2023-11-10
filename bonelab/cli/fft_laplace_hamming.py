from __future__ import annotations

# external imports
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace
import SimpleITK as sitk
from vtkbone import vtkboneAIMReader, vtkboneAIMWriter
from vtk import VTK_CHAR
import os
import numpy as np
from datetime import datetime

# internal imports
from bonelab.util.registration_util import message_s
from bonelab.util.echo_arguments import echo_arguments
from bonelab.util.registration_util import create_file_extension_checker
from bonelab.util.vtk_util import vtkImageData_to_numpy, numpy_to_vtkImageData
from bonelab.util.aim_calibration_header import get_aim_density_equation
from bonelab.io.vtk_helpers import handle_filetype_writing_special_cases


def compute_fft_laplace_hamming_segmentation(
        image: np.ndarray,
        laplace_epsilon: float,
        hamming_a0: float,
        voxel_spacing: float,
        threshold: float,
        min_size: int,
        silent: bool
) -> np.ndarray:
    """
    Compute the FFT Laplace Hamming segmentation of an image.

    Parameters
    ----------
    image : np.ndarray
        The image to segment.

    laplace_epsilon : float
        The epsilon value to use to combine the original image and the laplace image.

    hamming_a0 : float
        The a0 value to use for the hamming window.

    voxel_spacing : float
        The voxel spacing of the image.

    threshold : float
        The threshold to use for the segmentation.

    min_size : int
        The minimum size of the objects to keep.

    silent : bool
        Whether or not to print messages.

    Returns
    -------
    np.ndarray
        The segmented image.
    """
    x, y, z = np.meshgrid(
        *[np.arange(s) / s for s in image.shape],
        indexing="ij"
    )
    vx, vy, vz = np.meshgrid(
        *[np.fft.fftshift(np.fft.fftfreq(s, d=voxel_spacing)) for s in image.shape],
        indexing="ij"
    )
    hamming = (
            (hamming_a0 - (1 - hamming_a0) * np.cos(2 * np.pi * x))
            * (hamming_a0 - (1 - hamming_a0) * np.cos(2 * np.pi * y))
            * (hamming_a0 - (1 - hamming_a0) * np.cos(2 * np.pi * z))
    )
    laplace_hamming = laplace_epsilon * np.real(np.fft.ifftn(np.fft.ifftshift(
        hamming * (vx ** 2 + vy ** 2 + vz ** 2) * np.fft.fftshift(np.fft.fftn(image))
    ))) + (1 - laplace_epsilon) * image
    return remove_small_objects(laplace_hamming > threshold, min_size=min_size)


def fft_laplace_hamming(args: Namespace) -> None:
    pass


def create_parser() -> ArgumentParser:
    pass


def main() -> None:
    args = create_parser().parse_args()
    fft_laplace_hamming(args)


if __name__ == "__main__":
    main()
