from __future__ import annotations

# external imports
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace, ArgumentTypeError
import SimpleITK as sitk

# internal imports
from bonelab.io.vtk_helpers import get_vtk_writer
from bonelab.cli.registration import INTERPOLATORS, read_image, create_string_argument_checker


def read_transform(fn: str, invert: bool) -> sitk.Transform:
    if fn.endswith(".mat"):
        transform = sitk.ReadTransform(fn)
        if invert:
            return transform.GetInverse()
        else:
            return transform
    else:
        field = sitk.ReadImage(fn)
        if invert:
            return sitk.DisplacementFieldTransform(sitk.InverseDisplacementField(field))
        else:
            return sitk.DisplacementFieldTransform(field)


def apply_sitk_transform(args: Namespace):
    fixed_image = read_image(args.fixed_image)
    transform = read_transform(args.transform, args.invert_transform)
    if args.moving_image is not None:
        moving_image = read_image(args.moving_image)
        transformed_image = sitk.Resample(fixed_image, moving_image, transform, INTERPOLATORS[args.interpolator])
    else:
        transformed_image = sitk.Resample(fixed_image, transform, INTERPOLATORS[args.interpolator])
    sitk.WriteImage(transformed_image, args.output)


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
        help="path to where you want the transformed image saved, should have a file extension that is compatible "
             "with sitk.WriteImage - if you want an AIM at the end of this then you'll need to deal with converting "
             "your transformed image back to an AIM yourself or with another utility because that's beyond the scope "
             "of this tool."
    )
    parser.add_argument(
        "--moving-image", "-mi", type=str, default=None, metavar="STR",
        help="if given, the fixed image will be resampled onto the moving image using the transform. If you do not "
             "give a moving image then the fixed image will be resampled onto itself using the transform, which could "
             "possibly result in the data going out of the bounds of the image - recommended to provide this since "
             "there should usually be a moving image that you used to get the transform in the first place anyways"
    )
    parser.add_argument(
        "--invert-transform", "-it", default=False, action="store_true",
        help="enable this flag to invert the transform before applying it. you would want to do this if you registered "
             "image A (fixed) to image B (moving) but now you want to transform something from the coordindate system "
             "of image B to image A"
    )
    parser.add_argument(
        "--interpolator", "-int", default="Linear", metavar="STR",
        type=create_string_argument_checker(list(INTERPOLATORS.keys()), "interpolator"),
        help="the interpolator to use, options: `Linear`, `NearestNeighbour`, `BSpline`"
    )
    return parser


def main():
    apply_sitk_transform(create_parser().parse_args())


if __name__ == "__main__":
    main()