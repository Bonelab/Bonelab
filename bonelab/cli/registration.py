from __future__ import annotations

# external imports
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace
import SimpleITK as sitk

# internal imports
from bonelab.util.registration_util import (
    create_file_extension_checker, create_string_argument_checker, INTERPOLATORS,
    INPUT_EXTENSIONS, TRANSFORM_EXTENSIONS, check_percentage, get_output_base, write_args_to_yaml, check_inputs_exist,
    check_for_output_overwrite, write_metrics_to_csv, create_and_save_metrics_plot, read_and_downsample_images,
    setup_optimizer, setup_similarity_metric, setup_interpolator, setup_transform, setup_multiscale_progression,
    check_image_size_and_shrink_factors, MetricTrackingCallback
)
from bonelab.util.time_stamp import message


def registration(args: Namespace):
    """
    Perform a registration between two images.

    Parameters
    ----------
    args : Namespace
        The parsed arguments from the command line.

    Returns
    -------
    None
    """
    # get the base of the output, so we can construct the filenames of the auxiliary outputs
    output_base = get_output_base(args.output, TRANSFORM_EXTENSIONS, args.silent)
    output_yaml = f"{output_base}.yaml"
    output_metric_csv = f"{output_base}_metric_history.csv"
    output_metric_png = f"{output_base}_metric_history.png"
    # check that the inputs actually exist
    check_inputs_exist([args.fixed_image, args.moving_image], args.silent)
    # check if we're going to overwrite some outputs
    check_for_output_overwrite(
        [args.output, output_yaml, output_metric_csv, output_metric_png],
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
    # create the object
    registration_method = sitk.ImageRegistrationMethod()
    # set it up
    registration_method = setup_optimizer(
        registration_method,
        args.max_iterations,
        args.gradient_descent_learning_rate,
        args.gradient_descent_convergence_min_value,
        args.gradient_descent_convergence_window_size,
        args.powell_max_line_iterations,
        args.powell_step_length,
        args.powell_step_tolerance,
        args.powell_value_tolerance,
        args.optimizer,
        args.silent
    )
    registration_method = setup_similarity_metric(
        registration_method,
        args.similarity_metric,
        args.mutual_information_num_histogram_bins,
        args.joint_mutual_information_joint_smoothing_variance,
        args.similarity_metric_sampling_strategy,
        args.similarity_metric_sampling_rate,
        args.similarity_metric_sampling_seed,
        args.silent
    )
    registration_method = setup_interpolator(registration_method, args.interpolator, args.silent)
    registration_method = setup_transform(
        registration_method,
        fixed_image, moving_image,
        args.transform_type, args.centering_initialization,
        args.silent
    )
    registration_method = setup_multiscale_progression(
        registration_method,
        args.shrink_factors, args.smoothing_sigmas,
        args.silent
    )
    # monitor the metric over time - init the list and add the callback
    metric_callback = MetricTrackingCallback(registration_method, args.silent)
    registration_method.AddCommand(sitk.sitkIterationEvent, metric_callback)
    # do the registration
    if not args.silent:
        message("Starting registration.")
    transform = registration_method.Execute(fixed_image, moving_image)
    if not args.silent:
        message(f"Registration stopping condition: {registration_method.GetOptimizerStopConditionDescription()}")
    # write transform to file
    if not args.silent:
        message(f"Writing transformation to {args.output}")
    sitk.WriteTransform(transform, args.output)
    # save the metric history
    write_metrics_to_csv(output_metric_csv, metric_callback.metric_history, args.silent)
    # optionally, create a plot of the metric history and save it
    if args.plot_metric_history:
        create_and_save_metrics_plot(output_metric_png, metric_callback.metric_history, args.silent)


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="This tool allows you to do a rigid registration using the SimpleITK registration framework. "
                    "Options are provided to configure the initialization, optimizer, metric, and interpolation "
                    "scheme, and whether and how to do a multiscale registration. "
                    "NOTE: The resulting transformation will transform points from the MOVING frame to the FIXED "
                    "frame, so keep that in mind when using the transformation to transform images or masks.",
        epilog="This tool provides limited access to the full functionality of SimpleITK's registration framework. "
               "If you want to do something more advanced, consult the following resources: "
               "(1)https://simpleitk.org/SPIE2019_COURSE/04_basic_registration.html  --------- "
               "(2)https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ImageRegistrationMethod.html - "
               "Alternately, feel free to extend this tool to add more flexibility if you want to.",
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
        "output", type=create_file_extension_checker(TRANSFORM_EXTENSIONS, "output"), metavar="OUTPUT",
        help=f"Provide output filename ({', '.join(TRANSFORM_EXTENSIONS)})"
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
        "--max-iterations", "-mi", default=100, type=int, metavar="N",
        help="number of iterations to run registration algorithm for at each stage"
    )
    parser.add_argument(
        "--shrink-factors", "-sf", default=None, type=int, nargs="+", metavar="X",
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
    parser.add_argument(
        "--optimizer", "-opt", default="GradientDescent", metavar="STR",
        type=create_string_argument_checker(["GradientDescent", "Powell"], "optimizer"),
        help="the optimizer to use, options: `GradientDescent`, `Powell`"
    )
    parser.add_argument(
        "--gradient-descent-learning-rate", "-gdlr", default=1e-3, type=float, metavar="X",
        help="learning rate when using gradient descent optimizer"
    )
    parser.add_argument(
        "--gradient-descent-convergence-min-value", "-gdcmv", default=1e-6, type=float, metavar="X",
        help="minimum value for convergence when using gradient descent optimizer"
    )
    parser.add_argument(
        "--gradient-descent-convergence-window-size", "-gdcws", default=10, type=int, metavar="N",
        help="window size for checking for convergence when using gradient descent optimizer"
    )
    parser.add_argument(
        "--powell_max_line_iterations", "-pmli", default=100, type=int, metavar="N",
        help="maximum number of line iterations when using Powell optimizer"
    )
    parser.add_argument(
        "--powell_step_length", "-psl", default=1.0, type=float, metavar="X",
        help="maximum step length when using Powell optimizer"
    )
    parser.add_argument(
        "--powell_step_tolerance", "-pst", default=1e-6, type=float, metavar="X",
        help="step tolerance when using Powell optimizer"
    )
    parser.add_argument(
        "--powell_value_tolerance", "-pvt", default=1e-6, type=float, metavar="X",
        help="value tolerance when using Powell optimizer"
    )
    parser.add_argument(
        "--similarity-metric", "-sm", default="MeanSquares", metavar="STR",
        type=create_string_argument_checker(
            ["MeanSquares", "Correlation", "JointHistogramMutualInformation", "MattesMutualInformation"],
            "similarity-metric"
        ),
        help="the similarity metric to use, options: `MeanSquares`, `Correlation`, "
             "`JointHistogramMutualInformation`, `MattesMutualInformation`"
    )
    parser.add_argument(
        "--similarity-metric-sampling-strategy", "-smss", default="None", metavar="STR",
        type=create_string_argument_checker(["None", "Regular", "Random"], "similarity-metric-sampling-strategy"),
        help="sampling strategy for similarity metric, options: "
             "`None` -> use all points, "
             "`Regular` -> sample on a regular grid with specified sampling rate, "
             "`Random` -> sample randomly with specified sampling rate."
    )
    parser.add_argument(
        "--similarity-metric-sampling-rate", "-smsr", default=0.2, type=check_percentage, metavar="P",
        help="sampling rate for similarity metric, must be between 0.0 and 1.0"
    )
    parser.add_argument(
        "--similarity-metric-sampling-seed", "-smssd", default=None, type=int, metavar="N",
        help="the seed for random sampling, leave as `None` if you want a random seed. Can be useful if you want a "
             "deterministic registration with random sampling for debugging/testing. Don't go crazy and use huge "
             "numbers since SITK might report an OverflowError. I found keeping it <=255 worked."
    )
    parser.add_argument(
        "--mutual-information-num-histogram-bins", "-minhb", default=20, type=int, metavar="N",
        help="number of bins in histogram when using joint histogram or Mattes mutual information similarity metrics"
    )
    parser.add_argument(
        "--joint-mutual-information-joint-smoothing-variance", "-jmijsv", default=1.5, type=float, metavar="X",
        help="variance to use when smoothing the joint PDF when using the joint histogram mutual information "
             "similarity metric"
    )
    parser.add_argument(
        "--interpolator", "-int", default="Linear", metavar="STR",
        type=create_string_argument_checker(list(INTERPOLATORS.keys()), "interpolator"),
        help="the interpolator to use, options: `Linear`, `NearestNeighbour`, `BSpline`"
    )
    parser.add_argument(
        "--centering-initialization", "-ci", default="Geometry", metavar="STR",
        type=create_string_argument_checker(["Geometry", "Moments"], "centering-initialization"),
        help="the centering initialization to use, options: `Geometry`, `Moments`"
    )
    parser.add_argument(
        "--transform-type", "-tt", default="Euler3D", metavar="STR",
        type=create_string_argument_checker(["Euler3D", "Euler2D"], "transform-type"),
        help="the type of transformation to do, options: `Euler3D`, `Euler2D`. NOTE: these are just rigid "
             "transformations in 3D or 2D, non-rigid transforms are beyond the current scope of this tool. If you "
             "want a deformable registration, then either use blDemonsRegistration, extend this tool to be more "
             "flexible, or write a custom registration script and manually specify the transform you want to fit. "
    )

    return parser


def main():
    registration(create_parser().parse_args())


if __name__ == "__main__":
    main()
