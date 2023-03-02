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


def read_transform(initial_transform: str) -> Optional[sitk.Transform]:
    if initial_transform is not None:
        return sitk.ReadTransform(initial_transform)
    else:
        return None


def construct_multiscale_progression(
        shrink_factors: List[float],
        smoothing_sigmas: List[float],
        silent: bool
) -> Optional[List[Tuple[float]]]:
    if (shrink_factors is not None) and (smoothing_sigmas is not None):
        if len(shrink_factors) == len(smoothing_sigmas):
            if not silent:
                message(f"Performing multiscale registration with shrink factors: "
                        f"{', '.join([str(sf) for sf in shrink_factors])}; "
                        f"and smoothing sigmas: "
                        f"{', '.join([str(ss) for ss in smoothing_sigmas])}")
            return list(zip(shrink_factors, smoothing_sigmas))
        else:
            raise ValueError("`shrink-factors` and `smoothing-sigmas` must have same length")
    elif (shrink_factors is None) and (smoothing_sigmas is None):
        if not silent:
            message("Not performing multiscale registration.")
        return None
    else:
        raise ValueError("one of `shrink-factors` or `smoothing-sigmas` have not been specified. you must "
                         "either leave both as the default `None` or specify both (with equal length)")


def create_centering_transform(
        fixed_image: sitk.Image,
        moving_image: sitk.Image,
        centering_initialization: str,
        silent: bool
) -> sitk.Transform:
    if fixed_image.GetDimension() == 3:
        if not silent:
            message("Initializing a 3D rigid transform")
        transform_type = sitk.Euler3DTransform()
    elif fixed_image.GetDimension() == 2:
        if not silent:
            message("Initializing a 2D rigid transform")
        transform_type = sitk.Euler2DTransform()
    else:
        raise ValueError(f"`fixed_image` has dimension of {fixed_image.GetDimension()}, only 2 and 3 supported")
    if centering_initialization == "Geometry":
        if not silent:
            message("Centering the initial transform using geometry")
        centering_initialization = sitk.CenteredTransformInitializerFilter.GEOMETRY
    elif centering_initialization == "Moments":
        if not silent:
            message("Centering the initial transform using moments")
        centering_initialization = sitk.CenteredTransformInitializerFilter.MOMENTS
    else:
        raise ValueError("`centering_initialization` is invalid and was not caught")
    return sitk.CenteredTransformInitializer(
        fixed_image, moving_image,
        transform_type, centering_initialization
    )


def get_initial_transform(
        initial_transform: str,
        fixed_image: sitk.Image,
        moving_image: sitk.Image,
        centering_initialization: str,
        silent: bool
) -> sitk.Transform:
    if initial_transform is not None:
        if not silent:
            message("Reading initial transform.")
        return read_transform(initial_transform)
    else:
        return create_centering_transform(fixed_image, moving_image, centering_initialization, silent)


def add_initial_transform_to_displacement_field(
        field: sitk.Image,
        transform: sitk.Transform,
        silent: bool
) -> sitk.Image:
    if not silent:
        message("Converting initial transform to displacement field and adding it to the Demons displacement field.")
    return sitk.Add(
        field,
        sitk.TransformToDisplacementField(
            transform,
            field.GetPixelID(),
            field.GetSize(),
            field.GetOrigin(),
            field.GetSpacing(),
            field.GetDirection()
        )
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


def write_displacement_visualization(
        fn: str,
        field: sitk.Image,
        grid_spacing: int,
        grid_sigma: float,
        silent: bool
) -> None:
    if not silent:
        message(f"Writing displacement field visualization to {fn}")
    dim = field.GetDimension()
    grid_image = sitk.GridSource(
        size=field.GetSize(),
        sigma=tuple([grid_sigma] * dim),
        gridSpacing=tuple([grid_spacing] * dim),
        origin=field.GetOrigin(),
        spacing=field.GetSpacing(),
        direction=field.GetDirection()
    )
    sitk.WriteImage(sitk.Resample(grid_image, sitk.DisplacementFieldTransform(field)), fn)


def demons_registration(args: Namespace):
    # get the base of the output, so we can construct the filenames of the auxiliary outputs
    output_base = get_output_base(args.output, TRANSFORM_EXTENSIONS+IMAGE_EXTENSIONS, args.silent)
    output_yaml = f"{output_base}.yaml"
    output_metric_csv = f"{output_base}_metric_history.csv"
    output_metric_png = f"{output_base}_metric_history.png"
    output_displacement_visualization = f"{output_base}_deformation_visualization.nii"
    # check that the inputs actually exist
    check_inputs_exist([args.fixed_image, args.moving_image, args.initial_transform], args.silent)
    # check if we're going to overwrite some outputs
    check_for_output_overwrite(
        [
            args.output, output_yaml, output_metric_csv, output_metric_png,
            output_displacement_visualization
        ],
        args.overwrite, args.silent
    )
    # save the arguments of this registration to a yaml file
    # this has the added benefit of ensuring up-front that we can write files to the "output" that was provided,
    # so we do not waste a lot of time doing the registration and then crashing at the end because of write permissions
    write_args_to_yaml(output_yaml, args, args.silent)
    fixed_image, moving_image = read_and_downsample_images(
        args.fixed_image, args.moving_image,
        args.downsampling_shrink_factor, args.downsampling_smoothing_sigma,
        args.silent
    )
    check_image_size_and_shrink_factors(fixed_image, moving_image, args.shrink_factors, args.silent)
    initial_transform = get_initial_transform(
        args.initial_transform, fixed_image, moving_image, args.centering_initialization, args.silent
    )
    if not args.silent:
        message("Resampling fixed image onto the moving image using initial transform.")
    fixed_image = sitk.Resample(fixed_image, moving_image, initial_transform)
    multiscale_progression = construct_multiscale_progression(
        args.shrink_factors, args.smoothing_sigmas, args.silent
    )
    # do the registration
    displacement_field, metric_history = multiscale_demons(
        fixed_image, moving_image, args.demons_type, args.max_iterations,
        demons_displacement_field_smooth_std=args.displacement_smoothing_std,
        demons_update_field_smooth_std=args.update_smoothing_std,
        initial_transform=None,
        multiscale_progression=multiscale_progression,
        silent=args.silent
    )
    # add the initial transform and the demons transform together
    displacement_field = add_initial_transform_to_displacement_field(
        displacement_field, initial_transform, args.silent
    )
    # write the displacement transform or field
    write_transform_or_field(args.output, displacement_field, args.silent)
    # save the metric history
    write_metrics_to_csv(output_metric_csv, metric_history, args.silent)
    # optionally, create a plot of the metric history and save it
    if args.plot_metric_history:
        create_and_save_metrics_plot(output_metric_png, metric_history, args.silent)
    # optionally, write the deformation visualization image
    if args.write_displacement_visualization:
        write_displacement_visualization(
            output_displacement_visualization,
            displacement_field,
            args.visualization_grid_spacing,
            args.visualization_grid_sigma,
            args.silent
        )


def create_parser() -> ArgumentParser:

    parser = ArgumentParser(
        description="This tool allows you to do a deformable registration using the SimpleITK Demons registration "
                    "filters. Options are provided to configure the type of Demons filter, the amount of "
                    "regularization applied, and whether or how to do a multiscale registration. "
                    "Additionally, you can export an image visualizing the deformable registration on a typical "
                    "grid image. "
                    "NOTE: The resulting transformation will transform points from the MOVING frame to the FIXED "
                    "frame, so keep that in mind when using the transformation to transform images or masks.",
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
        "--write-displacement-visualization", "-wdv", default=False, action="store_true",
        help="enable this flag to write an image showing the deformation applied to a grid"
    )
    parser.add_argument(
        "--visualization-grid-spacing", "-vgsp", default=10, type=int, metavar="N",
        help="spacing of grid lines on the deformation visualization image"
    )
    parser.add_argument(
        "--visualization-grid-sigma", "-vgsg", default=0.1, type=float, metavar="X",
        help="sigma of filter applied to the deformation visualization image"
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
