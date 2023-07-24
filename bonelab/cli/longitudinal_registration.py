from __future__ import annotations

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace
import os

import SimpleITK

from bonelab.util.registration_util import (
    create_file_extension_checker, create_string_argument_checker, INTERPOLATORS,
    INPUT_EXTENSIONS, TRANSFORM_EXTENSIONS, check_percentage, get_output_base, write_args_to_yaml, check_inputs_exist,
    check_for_output_overwrite, write_metrics_to_csv, create_and_save_metrics_plot, read_and_downsample_image,
    setup_optimizer, setup_similarity_metric, setup_interpolator, setup_transform, setup_multiscale_progression,
    check_image_size_and_shrink_factors, message_s
)


def longitudinal_registration(args: Namespace):
    """
    Performs rigid longitudinal registration on a series of images. Intended for a time series but can also be used
    for a series of repeat scans from the same subject for precision.

    Parameters
    ----------
    args : Namespace
        The parsed command line arguments.

    Returns
    -------
    None
    """
    check_inputs_exist([args.baseline_image] + args.follow_up_images, args.silent)
    output_common_region_fn = os.path.join(args.output_directory, f"{args.output_label}_common_region.nii.gz")
    output_transformation_fns = [
        os.path.join(args.output_directory, f"{args.output_label}_transformation_{i}.txt")
        for i in range(len(args.follow_up_images))
    ]
    output_yaml_fn = os.path.join(args.output_directory, f"{args.output_label}.yaml")
    check_for_output_overwrite(
        [output_yaml_fn, output_common_region_fn] + output_transformation_fns,
        args.overwrite, args.silent
    )
    write_args_to_yaml(output_yaml_fn, args, args.silent)
    baseline_image = read_and_downsample_image(
        args.baseline_image, "baseline",
        args.downsampling_shrink_factor, args.downsampling_smoothing_sigma,
        args.silent
    )
    common_region = sitk.Add(sitk.Image(*baseline_image.GetSize(), sitk.sitkUInt8), 1)
    registration_method = sitk.ImageRegistrationMethod()
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
    registration_method = setup_multiscale_progression(
        registration_method,
        args.shrink_factors, args.smoothing_sigmas,
        args.silent
    )
    metric_callback = MetricTrackingCallback(registration_method, args.silent, False)
    registration_method.AddCommand(sitk.sitkIterationEvent, metric_callback)
    for i, (follow_up_image_fn, transform_fn) in enumerate(zip(args.follow_up_images, output_transformation_fns)):
        message_s(f"Processing follow-up {i}", args.silent)
        follow_up_image = read_and_downsample_image(
            follow_up_image_fn, f"follow-up {i}",
            args.downsampling_shrink_factor, args.downsampling_smoothing_sigma,
            args.silent
        )
        check_image_size_and_shrink_factors(
            baseline_image, follow_up_image,
            args.shrink_factors, args.silent
        )
        registration_method = setup_transform(
            registration_method,
            baseline_image, follow_up_image,
            args.transform_type, args.centering_initialization,
            args.silent
        )
        message_s("Starting registration", args.silent)
        transform = registration_method.Execute(fixed_image, moving_image)
        message_s(
            f"Registration stopping condition: {registration_method.GetOptimizerStopConditionDescription()}",
            args.silent
        )
        message_s(f"Writing transformation to {transform_fn}", args.silent)
        sitk.WriteTransform(transform, transform_fn)
        message_s("Transforming follow-up image to baseline space to update common region", args.silent)
        common_region = SimpleITK.Multiply(
            common_region,
            sitk.Resample(
                sitk.Add(sitk.Image(*baseline_image.GetSize(), sitk.sitkUInt8), 1),
                baseline_image,
                transform,
                sitk.sitkNearestNeighbor
            )
        )




def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Performs rigid longitudinal registration on a series of images. Intended for a time series but "
                    "can also be used for a series of repeat scans from the same subject for precision. The first "
                    "input is the baseline image. The second input is a list of follow-up images. You must also "
                    "specify a set of parameters for the rigid registrations, and finally an output directory. "
                    "and output label."
                    "The output directory will contain a transformation file for each follow-up image, and a "
                    "common region mask in the reference frame of the baseline image.",
        formatter_class=ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "baseline_image", type=create_file_extension_checker(INPUT_EXTENSIONS, "baseline_image"),
        help=f"Provide baseline image input filename ({', '.join(INPUT_EXTENSIONS)})"
    )
    parser.add_argument(
        "follow_up_images", nargs="+", type=create_file_extension_checker(INPUT_EXTENSIONS, "follow_up_images"),
        help=f"Provide follow-up image input filename ({', '.join(INPUT_EXTENSIONS)})"
    )
    parser.add_argument(
        "output_directory", type=str, help="Provide output directory"
    )
    parser.add_argument(
        "output_label", type=str, help="Provide output label"
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
        "--silent", "-s", default=False, action="store_true",
        help="enable this flag to suppress terminal output."
    )

    return parser


def main():
    args = create_parser().parse_args()
    longitudinal_registration(args)


if __name__ == "__main__":
    main()
