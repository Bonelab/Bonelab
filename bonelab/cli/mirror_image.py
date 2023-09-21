from __future__ import annotations

# external imports
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace, ArgumentTypeError
import SimpleITK as sitk
from typing import List
import numpy as np

# internal imports
from bonelab.util.time_stamp import message
from bonelab.util.registration_util import create_file_extension_checker, check_inputs_exist, \
    check_for_output_overwrite, read_image, INTERPOLATORS

# define file extensions that we consider available for input images
INPUT_EXTENSIONS = [".aim", ".nii", ".nii.gz"]

# define file extensions that we consider available for output images
OUTPUT_EXTENSIONS = [".nii", ".nii.gz"]


def get_image_center(img: sitk.Image) -> Tuple[float, ...]:
    origin = np.asarray(img.GetOrigin())
    spacing = np.asarray(img.GetSpacing())
    size = np.asarray(img.GetSize())
    direction = np.asarray(img.GetDirection()).reshape(3, 3)
    return origin + np.matmul(direction, (spacing*size/2))


def mirror_image(args: Namespace):
    check_inputs_exist([args.input], args.silent)
    check_for_output_overwrite([args.output], args.overwrite, args.silent)
    img = read_image(args.input, "image", args.silent)
    # create an affine transform
    if not args.silent:
        message(f"Creating transform that will mirror on axis {args.axis}")
    transform = sitk.AffineTransform(img.GetDimension())
    transform.SetCenter(get_image_center(img))
    transform.Scale([-1 if i == args.axis else 1 for i in range(img.GetDimension())])
    if not args.silent:
        message("Mirroring image")
    mirrored = sitk.Resample(img, img, transform, INTERPOLATORS[args.interpolator])
    if not args.silent:
        message(f"Writing mirrored image to {args.output}")
    sitk.WriteImage(mirrored, args.output)


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Mirror an image along the specified axis.",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "input", type=create_file_extension_checker(INPUT_EXTENSIONS, "input"), metavar="INPUT",
        help=f"Provide image input filename ({', '.join(INPUT_EXTENSIONS)})"
    )
    parser.add_argument(
        "axis", type=int, choices=range(3), metavar="AXIS",
        help="The axis along which you want to mirror the image."
    )
    parser.add_argument(
        "output", type=create_file_extension_checker(OUTPUT_EXTENSIONS, "output"), metavar="OUTPUT",
        help=f"Provide image output filename ({', '.join(OUTPUT_EXTENSIONS)})"
    )
    parser.add_argument(
        "--interpolator", "-int", default="Linear", metavar="STR",
        type=create_string_argument_checker(list(INTERPOLATORS.keys()), "interpolator"),
        help="the interpolator to use, options: `Linear`, `NearestNeighbour`, `BSpline`"
    )
    parser.add_argument(
        "--overwrite", "-ow", default=False, action="store_true",
        help="enable this flag to overwrite existing files, if they exist at output targets"
    )
    parser.add_argument(
        "--silent", "-s", default=False, action="store_true",
        help="enable this flag to suppress terminal output about how the program is proceeding"
    )
    return parser


def main():
    mirror_image(create_parser().parse_args())


if __name__ == "__main__":
    main()
