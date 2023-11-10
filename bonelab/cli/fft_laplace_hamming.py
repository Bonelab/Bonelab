from __future__ import annotations

# external imports
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace
import SimpleITK as sitk
from vtkbone import vtkboneAIMReader, vtkboneAIMWriter
from vtk import VTK_CHAR
import os
import numpy as np
from datetime import datetime
from skimage.morphology import remove_small_objects

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
    message_s("Construct mesh grids for spatial and frequency domains...", silent)
    x, y, z = np.meshgrid(
        *[np.arange(s) / s for s in image.shape],
        indexing="ij"
    )
    vx, vy, vz = np.meshgrid(
        *[np.fft.fftshift(np.fft.fftfreq(s, d=voxel_spacing)) for s in image.shape],
        indexing="ij"
    )
    message_s("Construct the hamming window function...", silent)
    hamming = (
            (hamming_a0 - (1 - hamming_a0) * np.cos(2 * np.pi * x))
            * (hamming_a0 - (1 - hamming_a0) * np.cos(2 * np.pi * y))
            * (hamming_a0 - (1 - hamming_a0) * np.cos(2 * np.pi * z))
    )
    message_s("Compute the FFT Laplace-Hamming filter...", silent)
    laplace_hamming = laplace_epsilon * np.real(np.fft.ifftn(np.fft.ifftshift(
        hamming * (vx ** 2 + vy ** 2 + vz ** 2) * np.fft.fftshift(np.fft.fftn(image))
    ))) + (1 - laplace_epsilon) * image
    message_s("Segment and remove small objects from segmentation...", silent)
    return remove_small_objects(laplace_hamming > threshold, min_size=min_size)


def fft_laplace_hamming(args: Namespace) -> None:
    print(echo_arguments("FFT Laplace-Hamming", vars(args)))
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
    segmentation = compute_fft_laplace_hamming_segmentation(
        image,
        args.laplace_epsilon,
        args.hamming_a0,
        args.voxel_spacing,
        args.threshold,
        args.min_size,
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
                echo_arguments("Bone segmentation created by FFT Laplace Hamming", vars(args))
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
        segmentation_sitk = sitk.GetImageFromArray(segmentation)
        segmentation_sitk.CopyInformation(image_sitk)
        sitk.WriteImage(segmentation_sitk, args.output)


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Perform Laplace-Hamming filtering on an AIM to segment bone. You provide an input image, the "
                    "Laplace epsilon, the Hamming window a0, the voxel spacing, the threshold, and the minimum size "
                    "for structures in the segmentation, and a segmentation will be created. This is intended to "
                    "replicate the Laplace Hamming filter available in IPL, and is necessary because the IPL LH "
                    "filter cannot currently be ran on large images (e.g. from knees). Because IPL is closed-source, "
                    "we cannot be sure that this implementation is identical. We have just matched the processing "
                    "steps described in the IPL documentation as best we can.",
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
        "--laplace-epsilon", "-le",
        type=float,
        default=0.5,
        help="The epsilon value to use to combine the original image and the laplace image."
    )
    parser.add_argument(
        "--hamming-a0", "-ha0",
        type=float,
        default=25/46,
        help="The a0 value to use for the hamming window."
    )
    parser.add_argument(
        "--voxel-spacing", "-vs",
        type=float,
        default=1,
        help="The voxel spacing of the image. This parameter will be used to scale the spatial wavemodes when the "
             "image is transformed to the frequency domain, and the wavemodes are then squared, summed, and multiplied "
             "by the image in the frequency domain - to perform the FFT Laplacian filter. "
             "NOTE: We have found that when this is left at 1, the magnitude "
             "of the outputs of the FFT Laplace-Hamming filter are on the same order as the original image and so we "
             "currently recommend this not be modified. If you do modify this, you will need to modify the threshold "
             "accordingly, and the effect of the `laplace-epsilon` parameter will likely become negligible."
    )
    parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=150,
        help="The threshold to use for the segmentation. NOTE: Do not assume this is in the same units as the input "
             "image. The  `laplace-epsilon`, `hamming-a0`, and `voxel_spacing` parameters will influence the magnitude "
             "of the output of the FFT Laplace-Hamming filter, and so the threshold will need to be adjusted "
             "accordingly."
    )
    parser.add_argument(
        "--min-size", "-ms",
        type=int,
        default=64,
        help="The minimum size of the objects to keep."
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


def main() -> None:
    args = create_parser().parse_args()
    fft_laplace_hamming(args)


if __name__ == "__main__":
    main()
