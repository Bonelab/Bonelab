from __future__ import annotations

# external imports
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace, ArgumentTypeError
import SimpleITK as sitk

# internal imports
from bonelab.util.time_stamp import message
from bonelab.io.vtk_helpers import get_vtk_writer
from bonelab.cli.registration import (
    INTERPOLATORS, read_image, create_string_argument_checker, create_file_extension_checker,
    check_inputs_exist, check_for_output_overwrite,
    INPUT_EXTENSIONS, TRANSFORM_EXTENSIONS
)
from bonelab.cli.demons_registration import IMAGE_EXTENSIONS


def read_transform(fn: str, invert: bool, silent: bool) -> sitk.Transform:
    if not silent:
        message(f"Reading transform from {fn}.")
    for ext in TRANSFORM_EXTENSIONS:
        if fn.lower().endswith(ext):
            transform = sitk.ReadTransform(fn)
            if invert:
                return transform.GetInverse()
            else:
                return transform
    for ext in IMAGE_EXTENSIONS:
        if fn.lower().endswith(ext):
            field = sitk.ReadImage(fn)
            if invert:
                return sitk.DisplacementFieldTransform(sitk.InverseDisplacementField(field))
            else:
                return sitk.DisplacementFieldTransform(field)
    raise ValueError("`transform` has invalid extension and was not caught")


def apply_sitk_transform(args: Namespace):
    check_inputs_exist([args.fixed_image, args.transform, args.moving_image], args.silent)
    check_for_output_overwrite([args.output], args.overwrite, args.silent)
    moving_image = read_image(args.moving_image, "moving_image", args.silent)
    transform = read_transform(args.transform, args.invert_transform, args.silent)
    if args.fixed_image is not None:
        fixed_image = read_image(args.fixed_image, "fixed_image", args.silent)
        if not args.silent:
            message("Resampling moving image onto fixed image using given transform.")
        transformed_image = sitk.Resample(moving_image, fixed_image, transform, INTERPOLATORS[args.interpolator])
    else:
        if not args.silent:
            message("Resampling moving image onto itself using given transform.")
        transformed_image = sitk.Resample(moving_image, transform, INTERPOLATORS[args.interpolator])
    if not args.silent:
        message(f"Writing transformed moving image to {args.output}")
    sitk.WriteImage(transformed_image, args.output)


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="This tool allows you to apply a transformation to an image using SimpleITK. The transformation "
                    "can be either a rigid transformation stored in a transformation file, or it could be a deformable "
                    "registration stored in an image. Remember that a transformation obtained using blRegistration "
                    "or blRegistrationDemons will point from the MOVING to FIXED domain. If you want to transform "
                    "an image or mask the other direction, you can give this program the FIXED image/mask as the "
                    "MOVING argument and then give the `--invert-transform` option to invert the transformation.",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "moving_image", type=create_file_extension_checker(INPUT_EXTENSIONS, "fixed_image"), metavar="MOVING",
        help=f"Provide moving image input filename ({', '.join(INPUT_EXTENSIONS)})"
    )
    parser.add_argument(
        "transform", metavar="TRANSFORM",
        type=create_file_extension_checker(IMAGE_EXTENSIONS+TRANSFORM_EXTENSIONS, "transform"),
        help=f"Provide transform filename ({', '.join(IMAGE_EXTENSIONS+TRANSFORM_EXTENSIONS)})"
    )
    parser.add_argument(
        "output", metavar="OUTPUT",
        type=create_file_extension_checker(IMAGE_EXTENSIONS, "output"),
        help=f"Provide output filename ({', '.join(IMAGE_EXTENSIONS)})"
    )
    parser.add_argument(
        "--overwrite", "-ow", default=False, action="store_true",
        help="enable this flag to overwrite existing files, if they exist at output targets"
    )
    parser.add_argument(
        "--fixed_image", "-mi", type=create_file_extension_checker(INPUT_EXTENSIONS, "moving_image"),
        default=None, metavar="FIXED",
        help=f"Optionally provide fixed image input filename ({', '.join(INPUT_EXTENSIONS)}). "
             "If given, the fixed image will be resampled onto the moving image using the transform. If you do not "
             "give a moving image then the fixed image will be resampled onto itself using the transform, which could "
             "possibly result in the data going out of the bounds of the image - recommended to provide this since "
             "there should usually be a moving image that you used to get the transform in the first place anyways."
    )
    parser.add_argument(
        "--invert-transform", "-it", default=False, action="store_true",
        help="enable this flag to invert the transform before applying it. you would want to do this if you registered "
             "image A (fixed) to image B (moving) but now you want to transform something from the coordinate system "
             "of image B to image A"
    )
    parser.add_argument(
        "--interpolator", "-int", default="Linear", metavar="STR",
        type=create_string_argument_checker(list(INTERPOLATORS.keys()), "interpolator"),
        help="the interpolator to use, options: `Linear`, `NearestNeighbour`, `BSpline`"
    )
    parser.add_argument(
        "--silent", "-s", default=False, action="store_true",
        help="enable this flag to suppress terminal output about how the program is proceeding"
    )
    return parser


def main():
    apply_sitk_transform(create_parser().parse_args())


if __name__ == "__main__":
    main()
