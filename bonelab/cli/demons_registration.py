from __future__ import annotations

# external imports
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import SimpleITK as sitk
from pathlib import Path
import csv
import yaml
from typing import Tuple, Optional

# internal imports
from bonelab.util.multiscale_registration import multiscale_demons, smooth_and_resample, DEMONS_FILTERS
from bonelab.cli.registration import (
    read_and_downsample_images, create_and_save_metrics_plot, write_metrics_to_csv,
    create_string_argument_checker
)


def demons_type_checker(s: str) -> str:
    s = str(s)
    if s in DEMONS_FILTERS.keys():
        return s
    else:
        return ValueError(f"Demons type {s}, not valid, please choose from: {list(DEMONS_FILTERS.keys())}")


def create_parser() -> ArgumentParser:

    parser = ArgumentParser(
        description='blDemonsRegistration: Demons Registration Tool',
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "fixed_image", type=str, metavar="FIXED",
        help="path to the fixed image (don't use DICOMs; AIM  or NIfTI should work)"
    )
    parser.add_argument(
        "moving_image", type=str, metavar="MOVING",
        help="path to the moving image (don't use DICOMs; AIM  or NIfTI should work)"
    )
    parser.add_argument(
        "output", type=str, metavar="OUTPUT",
        help="path to where you want outputs saved to, with no extension (will be added)"
    )
    parser.add_argument(
        "--output-format", "-of", default="image", metavar="STR",
        type=create_string_argument_checker(["transform", "image", "compressed-image"], "output-format"),
        help="format to save the output in, must be `transform`, `image`, or `compressed-image`."
             "`transform` -> .mat,"
             "`image` -> .nii,"
             "`compressed-image` -> .nii.gz"
    )
    parser.add_argument(
        "--downsampling-shrink-factor", "-dsf", type=float, default=None, metavar="X",
        help="the shrink factor to apply to the fixed and moving image before starting the registration"
    )
    parser.add_argument(
        "--downsampling-smoothing-sigma", "-dss", type=float, default=None, metavar="X",
        help="the smoothing sigma to apply to the fixed and moving image before starting the registration"
    )
    parser.add_argument(
        "--initial-transform", "-it", default=None, type=str, metavar="FN",
        help="the path to a file that can be read by sitk.ReadTransform and that contains the transform you want "
             "to initialize the registration process with (e.g. can obtain using blRegister)"
    )
    parser.add_argument(
        "--demons-type", "-dt", default="demons", type=demons_type_checker, metavar="STR",
        help=f"type of demons algorithm to use. options: {list(DEMONS_FILTERS.keys())}"
    )
    parser.add_argument(
        "--max-iterations", "-mi", default=100, type=int, metavar="N",
        help="number of iterations to run registration algorithm for at each stage"
    )
    parser.add_argument(
        "--displacement-smoothing-std", "-ds", default=1.0, type=float, metavar="X",
        help="standard deviation for the Gaussian smoothing applied to the displacement field at each step."
             "this is how you control the elasticity of the smoothing of the deformation"
    )
    parser.add_argument(
        "--update-smoothing-std", "-us", default=1.0, type=float, metavar="X",
        help="standard deviation for the Gaussian smoothing applied to the update field at each step."
             "this is how you control the viscosity of the smoothing of the deformation"
    )
    parser.add_argument(
        "--shrink-factors", "-sf", default=None, type=float, nargs="+", metavar="X",
        help="factors by which to shrink the fixed and moving image at each stage of the multiscale progression. you "
             "must give the same number of arguments here as you do for `smoothing-sigmas`"
    )
    parser.add_argument(
        "--smoothing-sigmas", "-ss", default=None, type=float, nargs="+", metavar="X",
        help="sigmas for the Gaussians used to smooth the fixed and moving image at each stage of the multiscale "
             "progression. you must give the same number of arguments here as you do for `shrink-factors`"
    )
    parser.add_argument(
        "--plot-metric-history", "-pmh", default=False, action="store_true",
        help="enable this flag to save a plot of the metric history to file in addition to the raw data"
    )
    parser.add_argument(
        "--verbose", "-v", default=False, action="store_true",
        help="enable this flag to print a lot of stuff to the terminal about how the registration is proceeding"
    )

    return parser


def read_transform(args: Namespace) -> Optional[sitk.Transform]:
    if args.initial_transform is not None:
        initial_transform = sitk.ReadTransform(args.initial_transform)
    else:
        initial_transform = None
    return initial_transform


def pad_images_to_same_extent(fixed_image: sitk.Image, moving_image: sitk.Image) -> Tuple[sitk.Image, sitk.Image]:
    size_difference = [fs - ms for (fs, ms) in zip(fixed_image.GetSize(), moving_image.GetSize())]
    for i, sd in enumerate(size_difference):
        pad_lower = [0, 0, 0]
        pad_upper = [0, 0, 0]
        pad_lower[i] = abs(sd) // 2
        pad_upper[i] = abs(sd) - (abs(sd) // 2)
        if sd > 0:
            # fixed image is bigger, so pad the moving image
            moving_image = sitk.ConstantPad(moving_image, pad_lower, pad_upper)
        if sd < 0:
            # fixed image is smaller, so pad the fixed image
            fixed_image = sitk.ConstantPad(fixed_image, pad_lower, pad_upper)
    return fixed_image, moving_image


def construct_multiscale_progression(args: Namespace) -> Optional[List[Tuple[float]]]:
    if (args.shrink_factors is not None) and (args.smoothing_sigmas is not None):
        if len(args.shrink_factors) == len(args.smoothing_sigmas):
            return list(zip(args.shrink_factors, args.smoothing_sigmas))
        else:
            raise ValueError("`shrink-factors` and `smoothing-sigmas` must have same length")
    elif (args.shrink_factors is None) and (args.smoothing_sigmas is None):
        return None
    else:
        raise ValueError("one of `shrink-factors` or `smoothing-sigmas` have not been specified. you must "
                         "either leave both as the default `None` or specify both (with equal length)")


def demons_registration(args: Namespace):
    # save the arguments of this registration to a yaml file
    # this has the added benefit of ensuring up-front that we can write files to the "output" that was provided,
    # so we do not waste a lot of time doing the registration and then crashing at the end because of write permissions
    write_args_to_yaml(args, f"{args.output}.yaml")
    fixed_image, moving_image = read_and_downsample_images(args)
    # we have to pad the images to be the same size - just a requirement of the Demons algorithms
    fixed_image, moving_image = pad_images_to_same_extent(fixed_image, moving_image)
    initial_transform = read_transform(args)
    multiscale_progression = construct_multiscale_progression(args)
    # do the registration
    displacement_field, metric_history = multiscale_demons(
        fixed_image, moving_image, args.demons_type, args.max_iterations,
        demons_displacement_field_smooth_std=args.displacement_smoothing_std,
        demons_update_field_smooth_std=args.update_smoothing_std,
        initial_transform=initial_transform,
        multiscale_progression=multiscale_progression,
        verbose=args.verbose
    )
    # save the displacement transform or field
    if args.output_format == "transform":
        sitk.WriteTransform(sitk.DisplacementFieldTransform(displacement_field), f"{args.output}.mat")
    elif args.output_format == "image":
        sitk.WriteImage(
            displacement_field, f"{args.output}.nii"
        )
    elif args.output_format == "compressed-image":
        sitk.WriteImage(
            displacement_field, f"{args.output}.nii.gz"
        )
    else:
        raise ValueError(f"value given for `output-format`, {args.output_format}, is invalid and was not caught")
    # save the metric history
    write_metrics_to_csv(metric_history, f"{args.output}_metric_history.csv")
    # optionally, create a plot of the metric history and save it
    if args.plot_metric_history:
        create_and_save_metrics_plot(metric_history, f"{args.output}_metric_history.png")


def main():
    demons_registration(create_parser().parse_args())


if __name__ == "__main__":
    main()
