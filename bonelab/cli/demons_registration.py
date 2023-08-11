from __future__ import annotations

# external imports
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace
import SimpleITK as sitk

# internal imports
from bonelab.util.time_stamp import message
from bonelab.util.echo_arguments import echo_arguments
from bonelab.util.demons_registration_util import multiscale_demons, DEMONS_FILTERS, \
    IMAGE_EXTENSIONS, TRANSFORM_EXTENSIONS, demons_type_checker, construct_multiscale_progression, \
    get_initial_transform, add_initial_transform_to_displacement_field, write_transform_or_field, \
    write_displacement_visualization
from bonelab.util.registration_util import (
    create_file_extension_checker, create_string_argument_checker,
    INPUT_EXTENSIONS, get_output_base, write_args_to_yaml, check_inputs_exist, check_for_output_overwrite,
    write_metrics_to_csv, create_and_save_metrics_plot, read_and_downsample_images, check_image_size_and_shrink_factors
)


def demons_registration(args: Namespace):
    # echo arguments
    print(echo_arguments("Demons Registration", vars(args)))
    # get the base of the output, so we can construct the filenames of the auxiliary outputs
    output_base = get_output_base(args.output, TRANSFORM_EXTENSIONS + IMAGE_EXTENSIONS, args.silent)
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
        args.moving_is_downsampled_atlas, args.silent
    )
    check_image_size_and_shrink_factors(fixed_image, moving_image, args.shrink_factors, args.silent)
    initial_transform = get_initial_transform(
        args.initial_transform, fixed_image, moving_image, args.centering_initialization, args.silent
    )
    if not args.silent:
        message("Resampling moving image onto the fixed image using initial transform.")
    moving_image = sitk.Resample(
        moving_image, fixed_image, initial_transform,
        defaultPixelValue=args.background_value
    )
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
        "output", type=create_file_extension_checker(TRANSFORM_EXTENSIONS + IMAGE_EXTENSIONS, "output"), metavar="OUTPUT",
        help=f"Provide output filename ({', '.join(TRANSFORM_EXTENSIONS + IMAGE_EXTENSIONS)})"
    )
    parser.add_argument(
        "--overwrite", "-ow", default=False, action="store_true",
        help="enable this flag to overwrite existing files, if they exist at output targets"
    )
    parser.add_argument(
        "--moving-is-downsampled-atlas", "-mida", action="store_true", default=False,
        help="enable this flag if the moving image is an atlas that is already downsampled and does not need to be "
             "downsampled further."
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
        "--background-value", "-bv", default=0, type=float, metavar="X",
        help="default value to set voxels to when outside of the image domain when resampling the moving image"
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
