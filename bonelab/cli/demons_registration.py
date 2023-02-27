from __future__ import annotations

# external imports
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace
import SimpleITK as sitk
from pathlib import Path
import csv
import yaml
from typing import Tuple, Optional
from enum import Enum

# internal imports
from bonelab.util.time_stamp import message
from bonelab.util.multiscale_registration import multiscale_demons, smooth_and_resample, DEMONS_FILTERS
from bonelab.cli.registration import (
    read_and_downsample_images, create_and_save_metrics_plot, write_metrics_to_csv, get_output_base,
    create_string_argument_checker, write_args_to_yaml, check_image_size_and_shrink_factors,
    create_file_extension_checker, check_inputs_exist, check_for_output_overwrite,
    INPUT_EXTENSIONS
)

# define output type enum
OutputType = Enum("OutputType", ["IMAGE", "TRANSFORM"])

# define file extensions that we would consider available for saving displacement_fields as images or transforms
IMAGE_EXTENSIONS = [".nii", ".nii.gz"]
TRANSFORM_EXTENSIONS = [".hdf", ".mat"]  # only allow the binary versions, no plain-text displacement fields


def demons_type_checker(s: str) -> str:
    s = str(s)
    if s in DEMONS_FILTERS.keys():
        return s
    else:
        return ValueError(f"Demons type {s}, not valid, please choose from: {list(DEMONS_FILTERS.keys())}")


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


def create_centering_transform(
        fixed_image: sitk.Image,
        moving_image: sitk.Image,
        args: Namespace
) -> sitk.Transform:
    if fixed_image.GetDimension() == 3:
        transform_type = sitk.Euler3DTransform()
    elif fixed_image.GetDimension() == 2:
        transform_type = sitk.Euler2DTransform()
    else:
        raise ValueError(f"`fixed_image` has dimension of {fixed_image.GetDimension()}, only 2 and 3 supported")
    if args.centering_initialization == "Geometry":
        centering_initialization = sitk.CenteredTransformInitializerFilter.GEOMETRY
    elif args.centering_initialization == "Moments":
        centering_initialization = sitk.CenteredTransformInitializerFilter.MOMENTS
    else:
        raise ValueError("`centering_initialization` is invalid and was not caught")
    return sitk.CenteredTransformInitializer(
        fixed_image, moving_image,
        transform_type, centering_initialization
    )


def write_transform_or_field(fn: str, field: sitk.Image, silent: bool) -> None:
    for ext in TRANSFORM_EXTENSIONS:
        if fn.lower().endswith(ext):
            if not silent:
                message(f"Writing transform to {fn}")
            sitk.WriteTransform(sitk.DisplacementFieldTransform(field), fn)
            return
    for ext in IMAGE_EXTENSIONS:
        if fn.lower().endswith(ext):
            if not silent:
                message(f"Writing displacement field to {fn}")
            sitk.WriteImage(field, fn)
            return
    raise ValueError(f"`output`, {fn}, does not have a valid extension and it was not caught.")


def demons_registration(args: Namespace):
    # get the base of the output, so we can construct the filenames of the auxiliary outputs
    output_base = get_output_base(args.output, TRANSFORM_EXTENSIONS+IMAGE_EXTENSIONS, args.silent)
    output_yaml = f"{output_base}.yaml"
    output_metric_csv = f"{output_base}_metric_history.csv"
    output_metric_png = f"{output_base}_metric_history.png"
    # check that the inputs actually exist
    check_inputs_exist([args.fixed_image, args.moving_image, args.initial_transform], args.silent)
    # check if we're going to overwrite some outputs
    check_for_output_overwrite(
        [args.output, output_yaml, output_metric_csv, output_metric_png],
        args.overwrite, args.silent
    )
    # save the arguments of this registration to a yaml file
    # this has the added benefit of ensuring up-front that we can write files to the "output" that was provided,
    # so we do not waste a lot of time doing the registration and then crashing at the end because of write permissions
    write_args_to_yaml(f"{args.output}.yaml", args, args.silent)
    fixed_image, moving_image = read_and_downsample_images(
        args.fixed_image, args.moving_image,
        args.downsampling_shrink_factor, args.downsampling_smoothing_sigma,
        args.silent
    )
    check_image_size_and_shrink_factors(fixed_image, moving_image, args.shrink_factors, args.silent)
    # we have to pad the images to be the same size - just a requirement of the Demons algorithms
    fixed_image, moving_image = pad_images_to_same_extent(fixed_image, moving_image)
    # I am a little bit unsure about this next thing. You need the fixed and moving images to exist in the same physical
    # space for the diffeomorphic, symmetric, and fast symmetric demons algorithms to work (otherwise they crash).
    # copying the metadata from the fixed_image onto the moving_image makes it so these algorithms will run, but I'm
    # not sure how this will affect the resulting transform. needs to be tested a bit to make sure we don't end up with
    # weird stuff happening (though the resulting displacement field is in the fixed frame, so maybe it doesn't matter?)
    # moving_image.CopyInformation(fixed_image)
    # it makes much more sense to me to resample the moving image to the physical space and grid of the fixed image
    # prior to registration, however I will see how this goes in testing. it's possible that here I need to be
    # applying a centering transform to make sure the images line up so we do not lose a bunch of information.
    # if I do end up changing it so the centering transform is applied here, I will then somehow have to make sure
    # that the final transform that gets saved is the two transforms combined somehow
    # this will likely involve using sitk.TransformToDisplacementField to convert that original centering
    # transform to a displacement field and just adding them together
    moving_image = sitk.Resample(moving_image, fixed_image)
    if args.initial_transform is not None:
        initial_transform = read_transform(args)
    else:
        initial_transform = create_centering_transform(fixed_image, moving_image, args)
    multiscale_progression = construct_multiscale_progression(args)
    # do the registration
    displacement_field, metric_history = multiscale_demons(
        fixed_image, moving_image, args.demons_type, args.max_iterations,
        demons_displacement_field_smooth_std=args.displacement_smoothing_std,
        demons_update_field_smooth_std=args.update_smoothing_std,
        initial_transform=initial_transform,
        multiscale_progression=multiscale_progression,
        silent=args.silent
    )
    # save the displacement transform or field
    write_transform_or_field(args.output, displacement_field, args.silent)

    # save the metric history
    write_metrics_to_csv(f"{args.output}_metric_history.csv", metric_history, args.silent)
    # optionally, create a plot of the metric history and save it
    if args.plot_metric_history:
        create_and_save_metrics_plot(f"{args.output}_metric_history.png", metric_history, args.silent)


def create_parser() -> ArgumentParser:

    parser = ArgumentParser(
        description='blDemonsRegistration: Demons Registration Tool',
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "fixed_image", type=create_file_extension_checker(INPUT_EXTENSIONS, "fixed_image"), metavar="FIXED",
        help=f"Provide fixed image input filename ({', '.join(INPUT_EXTENSIONS)})"
    )
    parser.add_argument(
        "moving_image", type=create_file_extension_checker(INPUT_EXTENSIONS, "moving_image"), metavar="MOVING",
        help=f"Provide moving image input filename ({', '.join(INPUT_EXTENSIONS)})"
    )
    parser.add_argument(
        "output", type=create_file_extension_checker(TRANSFORM_EXTENSIONS+IMAGE_EXTENSIONS, "output"), metavar="OUTPUT",
        help=f"Provide output filename ({', '.join(TRANSFORM_EXTENSIONS+IMAGE_EXTENSIONS)})"
    )
    parser.add_argument(
        "--overwrite", "-ow", default=False, action="store_true",
        help="enable this flag to overwrite existing files, if they exist at output targets"
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
        help=f"the path to a file that contains the transform you want "
             f"to initialize the registration process with ({', '.join(TRANSFORM_EXTENSIONS)}). "
             f"If you don't provide anything then a basic centering initialization will be done."
    )
    parser.add_argument(
        "--centering-initialization", "-ci", default="Geometry", metavar="STR",
        type=create_string_argument_checker(["Geometry", "Moments"], "centering-initialization"),
        help="if no initial transform provided, the centering initialization to use. "
             "options: `Geometry`, `Moments`"
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
        "--silent", "-s", default=False, action="store_true",
        help="enable this flag to suppress terminal output about how the registration is proceeding"
    )

    return parser


def main():
    demons_registration(create_parser().parse_args())


if __name__ == "__main__":
    main()
