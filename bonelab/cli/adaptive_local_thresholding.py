from __future__ import annotations

# external imports
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace
import SimpleITK as sitk
from vtkbone import vtkboneAIMReader, vtkboneAIMWriter
from vtk import VTK_CHAR
import os
import numpy as np
from scipy import ndimage
from skimage.filters import gaussian
from skimage.morphology import ball, cube, remove_small_objects
from datetime import datetime

# internal imports
from bonelab.util.registration_util import message_s
from bonelab.util.echo_arguments import echo_arguments
from bonelab.util.registration_util import create_file_extension_checker
from bonelab.util.vtk_util import vtkImageData_to_numpy, numpy_to_vtkImageData
from bonelab.util.aim_calibration_header import get_aim_density_equation
from bonelab.io.vtk_helpers import handle_filetype_writing_special_cases


def compute_minmax_threshold_image(density: np.ndarray, footprint: np.ndarray, silent: bool) -> np.ndarray:
    """
    Calculate the minmax threshold image.

    Parameters
    ----------
    density : np.ndarray
        The density image to be thresholded.

    footprint : np.ndarray
        The footprint to use for identifying local thresholds.

    silent : bool
        Whether to suppress terminal output.

    Returns
    -------
    np.ndarray
        The minmax threshold image.
    """
    message_s("Calculating max image...", silent)
    max_image = ndimage.filters.maximum_filter(density, footprint=footprint)
    message_s("Calculating min image...", silent)
    min_image = ndimage.filters.maximum_filter(density, footprint=footprint)
    message_s("Calculating minmax threshold image...", silent)
    return (min_image + max_image) / 2


def compute_mean_threshold_image(density: np.ndarray, footprint: np.ndarray, silent: bool) -> np.ndarray:
    """
    Calculate the mean threshold image.

    Parameters
    ----------
    density : np.ndarray
        The density image to be thresholded.

    footprint : np.ndarray
        The footprint to use for identifying local thresholds.

    silent : bool
        Whether to suppress terminal output.

    Returns
    -------
    np.ndarray
        The mean threshold image.
    """
    message_s("Calculating mean image...", silent)
    return ndimage.filters.convolve(density, footprint / footprint.sum())


def compute_adaptive_local_threshold_segmentation(
        density: np.ndarray,
        low_threshold: float,
        high_threshold: float,
        footprint: np.ndarray,
        mode: str,
        sigma: float,
        min_size: int,
        silent: bool
) -> np.ndarray:
    """
    Perform local adaptive thresholding on a density image.

    Parameters
    ----------
    density : np.ndarray
        The density image to be thresholded.

    low_threshold : float
        The lower threshold for the density image.

    high_threshold : float
        The upper threshold for the density image.

    footprint : np.ndarray
        The footprint to use for identifying local thresholds.

    mode : str
        The mode to use for identifying local thresholds. Can be `mean`, `minmax`, or `both`.

    sigma : float
        The sigma to use for the gaussian filter.

    min_size : int
        The minimum size of structures to keep in the segmentation.

    silent : bool
        Whether to suppress terminal output.

    Returns
    -------
    np.ndarray
        The thresholded image.
    """
    message_s(f"Calculating threshold image using mode: {mode}", silent)
    if mode == "mean":
        threshold_image = compute_mean_threshold_image(density, footprint, silent)
    elif mode == "minmax":
        threshold_image = compute_minmax_threshold_image(density, footprint, silent)
    elif mode == "both":
        threshold_image = np.minimum(
            compute_mean_threshold_image(density, footprint, silent),
            compute_minmax_threshold_image(density, footprint, silent)
        )
    else:
        raise ValueError(f"`mode` must be one of `mean`, `minmax`, or `both`, received {mode}.")
    density = gaussian(density, sigma=sigma)
    return remove_small_objects(
        ((density > low_threshold) & (density > threshold_image)) | (density > high_threshold),
        min_size=min_size
    )


def adaptive_local_thresholding(args: Namespace):
    print(echo_arguments("Adaptive Local Thresholding", vars(args)))
    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Input file {args.input} does not exist.")
    if os.path.exists(args.output) and not args.overwrite:
        raise FileExistsError(f"Output file {args.output} already exists. Use the --overwrite flag to overwrite.")
    message_s(f"Reading input image from {args.input}", args.silent)
    if args.aims:
        reader = vtkboneAIMReader()
        reader.DataOnCellsOff()
        reader.SetFileName(args.input)
        reader.Update()
        image = vtkImageData_to_numpy(reader.GetOutput())
        if args.convert_to_density:
            m, b = get_aim_density_equation(reader.GetProcessingLog())
            image = m * image + b
    else:
        image_sitk = sitk.ReadImage(args.input)
        image = sitk.GetArrayFromImage(image_sitk)
    message_s("Generating bone segmentation", args.silent)
    if args.structuring_element_shape == "ball":
        footprint = ball(args.structuring_element_size)
    elif args.structuring_element_shape == "cube":
        footprint = cube(args.structuring_element_size)
    else:
        raise ValueError("Invalid structuring element shape.")
    segmentation = compute_adaptive_local_threshold_segmentation(
        image,
        args.lower_threshold,
        args.upper_threshold,
        footprint,
        args.local_threshold_method,
        args.sigma,
        args.minimum_structure_size,
        args.silent
    )
    message_s(f"Writing bone segmentation to {args.output}", args.silent)
    if args.aims:
        segmentation_vtk = numpy_to_vtkImageData(
            127 * (segmentation > 0),
            spacing=reader.GetOutput().GetSpacing(),
            origin=reader.GetOutput().GetOrigin(),
            array_type=VTK_CHAR
        )
        processing_log = (
            reader.GetProcessingLog() + os.linesep +
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]" +
            echo_arguments("Bone segmentation created by Adaptive Local Thresholding", vars(args))
        )
        writer = vtkboneAIMWriter()
        writer.SetInputData(segmentation_vtk)
        handle_filetype_writing_special_cases(
            writer,
            processing_log=processing_log
        )
        writer.SetFileName(args.output)
        writer.Update()
    else:
        segmentation_sitk = sitk.GetImageFromArray(segmentation.astype(int))
        segmentation_sitk.CopyInformation(image_sitk)
        sitk.WriteImage(segmentation_sitk, args.output)


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Perform adaptive local thresholding on an image to segment bone. You provide an input image "
                    "and lower and upper thresholds and a bone segmentation will be created. Optionally you can "
                    "specify the size and shape of the structuring element used for identifying the local thresholds, "
                    "as well as the minimum structure size to keep in the segmentation. Finally, you can also specify "
                    "whether to base the local thresholds on the mean of local voxels, the average of the min and max "
                    "of local voxels, or the minimum of each of these methods. This method is based on the following "
                    "article: https://doi.org/10.1016/j.bone.2021.116225. ",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "input",
        type=str,
        help="Input image filename to be segmented."
    )
    parser.add_argument(
        "output",
        type=str,
        help="Output filename for the segmentation."
    )
    parser.add_argument(
        "--aims",
        default=False,
        action="store_true",
        help="Enable this flag to indicate that the input and output are .aim files."
    )
    parser.add_argument(
        "--lower-threshold", "-lt",
        type=float,
        default=190,
        help="Lower threshold for bone segmentation."
    )
    parser.add_argument(
        "--upper-threshold", "-ut",
        type=float,
        default=450,
        help="Upper threshold for bone segmentation."
    )
    parser.add_argument(
        "--structuring-element-size", "-sz",
        type=int,
        default=6,
        help="Size of the structuring element used for identifying local thresholds."
             "If the footprint shape is a ball, this is the radius. If the footprint shape is a cube, "
             "this is the width."
    )
    parser.add_argument(
        "--structuring-element-shape", "-sh",
        type=str,
        default="ball",
        choices=["ball", "cube"],
        help="Shape of the structuring element used for identifying local thresholds."
    )
    parser.add_argument(
        "--sigma", "-sg",
        type=float,
        default=1,
        help="Sigma for the gaussian filter."
    )
    parser.add_argument(
        "--minimum-structure-size", "-ms",
        type=int,
        default=64,
        help="Minimum size of structures to keep in the segmentation."
    )
    parser.add_argument(
        "--local-threshold-method", "-ltm",
        type=str,
        default="mean",
        choices=["mean", "minmax", "both"],
        help="Method for determining local thresholds. `mean` uses the mean of local voxels. `minmax` uses the "
             "average of the min and max of local voxels. `both` uses the minimum of both methods."
    )
    parser.add_argument(
        "--convert-to-density", "-cd",
        default=False,
        action="store_true",
        help="Enable this flag to convert the input aim image to density units. Only valid if the input is an .aim "
    )
    parser.add_argument(
        "--silent", "-s",
        default=False,
        action="store_true",
        help="Enable this flag to suppress terminal output about how the program is proceeding."
    )
    parser.add_argument(
        "--overwrite", "-ow",
        default=False,
        action="store_true",
        help="Enable this flag to overwrite existing files, if they exist at output targets."
    )

    return parser


def main():
    args = create_parser().parse_args()
    adaptive_local_thresholding(args)


if __name__ == "__main__":
    main()
