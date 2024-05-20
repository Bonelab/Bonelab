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


def convert_back_to_aim(args: Namespace) -> None:
    print(echo_arguments("Convert Back To AIM", vars(args)))
    message("Checking inputs exist")
    check_inputs_exist([args.input_mask, args.reference_aim], False)
    message("Checking for output overwrite")
    check_for_output_overwrite(args.output_aim, args.overwrite, False)
    message(f"Reading input image from: {args.input_mask}")
    mask = sitk.ReadImage(args.input_mask)
    message("Converting input image to numpy array")
    mask = np.transpose(sitk.GetArrayFromImage(mask), (2, 1, 0))
    message(f"Reading reference AIM from {args.reference_aim}")
    reader = vtkboneAIMReader()
    reader.DataOnCellsOff()
    reader.SetFileName(args.reference_aim)
    reader.Update()
    message(f"Converting image back to AIM")
    mask = numpy_to_vtkImageData(
        127 * (mask > 0),
        spacing=reader.GetOutput().GetSpacing(),
        origin=reader.GetOutput().GetOrigin(),
        array_type=VTK_CHAR
    )
    message(f"Adding to processing log")
    processing_log = (
        reader.GetProcessingLog() + os.linesep +
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {args.log}."
    )
    message(f"Saving image to {args.output_aim}")
    writer = vtkboneAIMWriter()
    writer.SetInputData(mask)
    handle_filetype_writing_special_cases(
        writer,
        processing_log=processing_log
    )
    writer.SetFileName(args.output_aim)
    writer.Update()


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Convert from any image type back to the Scanco AIM format. You must provide a path to the image "
                    "you want to convert, a path to the reference AIM image, and a path to where you want the output "
                    "image saved to. The reference AIM is used to determine all of the metadata for the output image, "
                    "including the processing log (an additional entry will be added to the processing log to indicate "
                    "how the image was converted). The actual image data will be taken from the input image.",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input_mask", type=str, help="Path to the mask you want to convert back to AIM."
    )
    parser.add_argument(
        "reference_aim", type=str, help="Path to the reference AIM image."
    )
    parser.add_argument(
        "output_aim", type=str, help="Path to where you want the output AIM saved to."
    )
    parser.add_argument(
        "--log", "-l", type=str, default="", help="Message to add to processing log."
    )
    parser.add_argument(
        "--overwrite", "-ow", action="store_true", help="Overwrite output without asking."
    )

    return parser


def main():
    args = create_parser().parse_args()
    convert_back_to_aim(args)


if __name__ == "__main__":
    main()
