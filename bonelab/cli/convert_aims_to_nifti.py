from __future__ import annotations

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace, ArgumentTypeError
import SimpleITK as sitk
import numpy as np
import vtkbone
import os

from bonelab.util.echo_arguments import echo_arguments
from bonelab.util.time_stamp import message
from bonelab.util.vtk_util import vtkImageData_to_numpy
from bonelab.util.aim_calibration_header import get_aim_density_equation
from bonelab.cli.registration import check_inputs_exist, check_for_output_overwrite


def create_parser() -> ArgumentParser:
    """
    Create the parser for the command line tool.

    Returns
    -------
    ArgumentParser
        The parser for the command line tool.
    """
    parser = ArgumentParser(
        description="This tool allows you to convert an AIM image and optionally, its masks, to NIfTI image(s).",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "image", type=str, help="The image AIM file to convert."
    )
    parser.add_argument(
        "output_dir", type=str, help="The output directory."
    )
    parser.add_argument(
        "--masks", "-m", default=None, type=str, nargs="+", help="The mask AIM files to convert."
    )
    parser.add_argument(
        "--overwrite", "-ow", action="store_true", help="Overwrite output files if they exist."
    )
    parser.add_argument(
        "--silent", "-s", action="store_true", help="Silence all terminal output."
    )
    return parser


def message_s(m: str, s: bool):
    """
    Print a message if silent is False.

    Parameters
    ----------
    m : str
        The message to print.
    s : bool
        Whether or not to print the message.

    Returns
    -------
    None
    """
    if not s:
        message(m)


def convert_aim_to_nifti(args: Namespace):
    """
    Convert an AIM file to a NIfTI file.

    Parameters
    ----------
    args : Namespace
        The command line arguments.

    Returns
    -------
    None
    """
    print(echo_arguments("Convert AIM to NIfTI", vars(args)))
    # check inputs
    check_inputs_exist([args.image] + (args.masks if args.masks is not None else []), args.silent)
    # create output paths
    image_output_path = os.path.join(args.output_dir, os.path.basename(args.image).lower().replace(".aim", ".nii.gz"))
    if args.masks is not None:
        mask_output_paths = [
            os.path.join(args.output_dir, os.path.basename(mask).lower().replace(".aim", ".nii.gz"))
            for mask in args.masks
        ]
    else:
        mask_output_paths = None
    # check if outputs exist
    check_for_output_overwrite(
        [image_output_path] + (mask_output_paths if mask_output_paths is not None else []),
        args.overwrite, args.silent
    )
    # read image
    message_s(f"Reading image AIM file {args.image}", args.silent)
    reader = vtkbone.vtkboneAIMReader()
    reader.DataOnCellsOff()
    reader.SetFileName(args.image)
    reader.Update()
    processing_log = reader.GetProcessingLog()
    density_slope, density_intercept = get_aim_density_equation(processing_log)
    arr = density_slope * vtkImageData_to_numpy(reader.GetOutput()) + density_intercept
    # convert to SimpleITK image
    message_s("Converting image to SimpleITK image", args.silent)
    img = sitk.GetImageFromArray(np.moveaxis(arr, [0, 1, 2], [2, 1, 0]))
    img.SetSpacing(reader.GetOutput().GetSpacing())
    img.SetOrigin(reader.GetOutput().GetOrigin())
    # write image
    message_s(f"Writing NIfTI file {image_output_path}", args.silent)
    sitk.WriteImage(img, image_output_path)
    image_position = reader.GetPosition()
    image_shape = img.GetSize()
    image_spacing = img.GetSpacing()
    image_origin = img.GetOrigin()
    message_s(f"IMAGE | Shape: {image_shape}, Position: {image_position}", args.silent)
    if mask_output_paths is not None:
        message_s(f"Reading {len(args.masks)} mask AIM files", args.silent)
        for (mask_path, mask_output_path) in zip(args.masks, mask_output_paths):
            message_s(f"Reading mask AIM file {mask_path}", args.silent)
            reader.SetFileName(mask_path)
            reader.Update()
            arr = vtkImageData_to_numpy(reader.GetOutput())
            mask_position = reader.GetPosition()
            #print(pad_lower)
            #print(pad_upper)
            message_s("Converting mask to SimpleITK image", args.silent)
            mask = sitk.GetImageFromArray(np.moveaxis(arr, [0, 1, 2], [2, 1, 0]))
            mask.SetSpacing(image_spacing)
            mask.SetOrigin(image_origin)
            mask_shape = mask.GetSize()
            message_s(f"MASK (before cropping and padding) | Shape: {mask_shape}, Position: {mask_position}", args.silent)
            message_s("Cropping and Padding mask to match up to image", args.silent)
            pad_lower = [max(mp - ip, 0) for (mp, ip) in zip(mask_position, image_position)]
            crop_lower = [min(mp - ip, 0) for (mp, ip) in zip(mask_position, image_position)]
            message_s(f"After comparing positions, need to crop lower by {crop_lower} and pad lower by {pad_lower}", args.silent)
            for i, cl in enumerate(crop_lower):
                if cl < 0:
                    crop = [0, 0, 0]
                    crop[i] = abs(cl)
                    mask = sitk.Crop(mask, crop, [0, 0, 0])
            pad_upper = [max(ims - (ms + pl + cl), 0) for (pl, cl, ims, ms) in zip(pad_lower, crop_lower, image_shape, mask_shape)]
            crop_upper = [min(ims - (ms + pl + cl), 0) for (pl, cl, ims, ms) in zip(pad_lower, crop_lower, image_shape, mask_shape)]
            message_s(f"After comparing shapes, need to crop upper by {crop_upper} and pad upper by {pad_upper}", args.silent)
            for i, cu in enumerate(crop_upper):
                if cu < 0:
                    crop = [0, 0, 0]
                    crop[i] = abs(cu)
                    mask = sitk.Crop(mask, [0, 0, 0], crop)
            mask = sitk.ConstantPad(mask, pad_lower, pad_upper, 0)
            message_s(f"MASK (after cropping and padding) | Shape: {mask.GetSize()}", args.silent)
            message_s(f"Writing NIfTI file to {mask_output_path}", args.silent)
            sitk.WriteImage(mask, mask_output_path)
    else:
        message_s("No masks given, finished.", args.silent)


def main():
    parser = create_parser()
    args = parser.parse_args()
    convert_aim_to_nifti(args)


if __name__ == "__main__":
    main()
