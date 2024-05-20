from __future__ import annotations

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace
import SimpleITK as sitk
import numpy as np
from vtk import VTK_CHAR
from vtkbone import vtkboneAIMReader, vtkboneAIMWriter
from datetime import datetime
import os

from bonelab.util.echo_arguments import echo_arguments
from bonelab.util.time_stamp import message
from bonelab.util.registration_util import check_inputs_exist, check_for_output_overwrite
from bonelab.util.vtk_util import numpy_to_vtkImageData
from bonelab.io.vtk_helpers import handle_filetype_writing_special_cases


def convert_masks_to_aims(args: Namespace) -> None:
    print(echo_arguments("Convert Back To AIM", vars(args)))
    output_aims = [f"{args.output_base}_{cl}.AIM" for cl in args.class_labels]
    message("Checking inputs exist")
    check_inputs_exist([args.input_mask, args.reference_aim], False)
    message("Checking for output overwrite")
    check_for_output_overwrite(output_aims, args.overwrite, False)
    message(f"Reading input image from: {args.input_mask}")
    mask = sitk.ReadImage(args.input_mask)
    message("Converting input image to numpy array")
    mask = np.transpose(sitk.GetArrayFromImage(mask), (2, 1, 0))
    message(f"Reading reference AIM from {args.reference_aim}")
    reader = vtkboneAIMReader()
    reader.DataOnCellsOff()
    reader.SetFileName(args.reference_aim)
    reader.Update()
    message(f"Converting images back to AIMs")
    for cl, cv, output_aim in zip(args.class_labels, args.class_values, output_aims):
        message(f"Converting class {cl} ({cv}) to AIM")
        mask_cl = numpy_to_vtkImageData(
            127 * (mask == cv),
            spacing=reader.GetOutput().GetSpacing(),
            origin=reader.GetOutput().GetOrigin(),
            array_type=VTK_CHAR
        )
        message(f"Adding to processing log")
        processing_log = (
                reader.GetProcessingLog() + os.linesep +
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {args.log}."
        )
        message(f"Saving image to {output_aim}")
        writer = vtkboneAIMWriter()
        writer.SetInputData(mask_cl)
        handle_filetype_writing_special_cases(
            writer,
            processing_log=processing_log
        )
        writer.SetFileName(output_aim)
        writer.Update()


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Convert a mask image to the Scanco AIM format. You must provide a path to the mask image "
                    "you want to convert, a path to the reference AIM image, and a path to where you want the output "
                    "images saved to. The reference AIM is used to determine all of the metadata for the output image, "
                    "including the voxel spacing, origin, and dimensions. You can also provide a log message that will "
                    "be added to the processing log of the output AIM. This script is intended specifically for "
                    "converting masks that contain multiclass segmentations, so you also need to provide a list of "
                    "class values and class labels. These will be matched one-to-one - each class label will be "
                    "binarized and saved as a separate AIM file using the class label as a suffix to the output path.",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "input_mask", type=str, help="Path to the mask you want to convert back to AIM."
    )
    parser.add_argument(
        "reference_aim", type=str, help="Path to the reference AIM image."
    )
    parser.add_argument(
        "output_base", type=str,
        help="Path to where you want the output AIMs saved to. NOTE: this is a prefix and the class labels are going "
             "to be appended, followed by .AIM, so do not include the AIM extension here."
    )
    parser.add_argument(
        "--class-values", "-cv", type=int, nargs="+", help="List of class values.", required=True
    )
    parser.add_argument(
        "--class-labels", "-cl", type=str, nargs="+", help="List of class labels.", required=True
    )
    parser.add_argument(
        "--log", "-l", type=str, default="", help="Message to add to processing log."
    )
    parser.add_argument(
        "--overwrite", "-ow", action="store_true", help="Overwrite output without asking."
    )

    return parser


def main() -> None:
    args = create_parser().parse_args()
    convert_masks_to_aims(args)


if __name__ == "__main__":
    main()
