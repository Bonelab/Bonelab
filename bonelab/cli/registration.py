from __future__ import annotations

# external imports
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace, ArgumentTypeError
import SimpleITK as sitk
from matplotlib import pyplot as plt
import csv
import yaml
from typing import List, Callable

# internal imports
from bonelab.util.vtk_util import vtkImageData_to_numpy
from bonelab.io.vtk_helpers import get_vtk_reader
from bonelab.util.multiscale_registration import smooth_and_resample, create_metric_tracking_callback


def create_string_argument_checker(options: List[str], argument_name: str) -> Callable:
    def argument_checker(s: str) -> str:
        s = str(s)
        if s in options:
            return s
        else:
            raise ArgumentTypeError(f"`{argument_name}` must be one of {options}. got {s}")

    return argument_checker


def check_percentage(x: float) -> float:
    x = float(x)
    if (x < 0.0) or (x > 1.0):
        raise ArgumentTypeError(f"value must be between 0.0 and 1.0, got {x}")
    return x


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="blRegistration: SimpleITK Registration Tool.",
        epilog="This tool provides limited access to the full functionality of SimpleITK's registration framework. "
               "If you want to do something more advanced, consult the following resources: "
               "(1)https://simpleitk.org/SPIE2019_COURSE/04_basic_registration.html  --------- "
               "(2)https://simpleitk.org/doxygen/latest/html/classitk_1_1simple_1_1ImageRegistrationMethod.html - "
               "Alternately, feel free to extend this tool to add more flexibility if you want to.",
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
        "--max-iterations", "-mi", default=100, type=int, metavar="N",
        help="number of iterations to run registration algorithm for at each stage"
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
    parser.add_argument(
        "--optimizer", "-opt", default="GradientDescent", metavar="STR",
        type=create_string_argument_checker(["GradientDescent", "L-BFGS2"], "optimizer"),
        help="the optimizer to use, options: `GradientDescent`, `L-BFGS2`"
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
        "--lbfgs-solution-accuracy", "-lsa", default=1e-5, type=float, metavar="X",
        help="solution accuracy when using L-BFGS2 as optimizer"
    )
    parser.add_argument(
        "--lbfgs-hessian-approximate-accuracy", "-lhaa", default=6, type=int, metavar="N",
        help="hessian approximate accuracy when using L-BFGS2 as optimizer"
    )
    parser.add_argument(
        "--lbfgs-delta-convergence-distance", "-ldcd", default=0, type=int, metavar="N",
        help="delta convergence distance when using L-BFGS2 as optimizer"
    )
    parser.add_argument(
        "--lbfgs-delta-convergence-tolerance", "-ldct", default=1e-5, type=float, metavar="X",
        help="delta convergence tolerance when using L-BFGS2 as optimizer"
    )
    parser.add_argument(
        "--lbfgs-linesearch-maximum-evaluations", "-llme", default=40, type=int, metavar="X",
        help="maximum number of linesearch evaluations when using L-BFGS2 as optimizer"
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
        help="sampling strategy for similarity metric, options: `NONE`, `REGULAR`, `RANDOM`"
    )
    parser.add_argument(
        "--similarity-metric-sampling-rate", "-smsr", default=0.2, type=check_percentage, metavar="P",
        help="sampling rate for similarity metric, must be between 0.0 and 1.0"
    )
    parser.add_argument(
        "--similarity-metric-sampling-seed", "-smssd", default=None, type=int, metavar="N",
        help="the seed for random sampling, leave as `None` if you want a random seed. Can be useful if you want a "
             "deterministic registration with random sampling for debugging/testing"
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
        type=create_string_argument_checker(["Linear", "NearestNeighbour", "Gaussian"], "interpolator"),
        help="the interpolator to use, options: `Linear`, `NearestNeighbour`, `Gaussian`"
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


def write_args_to_yaml(args: Namespace, fn: str) -> None:
    with open(fn, "w") as f:
        yaml.dump(vars(args), f)


def read_image(fn: str) -> sitk.Image:
    # first let's see if SimpleITK can do it
    try:
        return sitk.ReadImage(fn)
    except RuntimeError as err:
        # if that gave an error, check if it's the error to do with not being able to find an appropriate ImageIO
        if "Unable to determine ImageIO reader" in str(err):
            # if so, let's see if the vtk helpers in Bonelab can handle it
            reader = get_vtk_reader(fn)
            if reader is None:
                raise ValueError(f"Could not find a reader for {fn}")
            reader.SetFileName(fn)
            reader.Update()
            vtk_image = reader.GetOutput()
            image = sitk.GetImageFromArray(vtkImageData_to_numpy(vtk_image))
            image.SetSpacing(vtk_image.GetSpacing())
            image.SetOrigin(vtk_image.GetOrigin())
            # vtk image data doesn't seem to store direction data -- problem??
            # just be sure to apply the transform that gets derived consistently later on I guess
            return image
        else:
            raise err


def write_metrics_to_csv(metric_history: List[float], fn: str) -> None:
    with open(fn, "w") as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(metric_history)


def create_and_save_metrics_plot(metrics_history: List[float], fn: str) -> None:
    plt.figure()
    plt.plot(metrics_history)
    plt.xlabel('iteration')
    plt.ylabel('metric')
    plt.yscale('log')
    plt.grid()
    plt.savefig(fn)


def read_and_downsample_images(args: Namespace) -> Tuple[sitk.Image, sitk.Image]:
    # load images, cast to single precision float
    fixed_image = sitk.Cast(read_image(args.fixed_image), sitk.sitkFloat32)
    moving_image = sitk.Cast(read_image(args.moving_image), sitk.sitkFloat32)
    # optionally, downsample the fixed and moving images
    if (args.downsampling_shrink_factor is not None) and (args.downsampling_smoothing_sigma is not None):
        fixed_image = smooth_and_resample(
            fixed_image, args.downsampling_shrink_factor, args.downsampling_smoothing_sigma
        )
        moving_image = smooth_and_resample(
            moving_image, args.downsampling_shrink_factor, args.downsampling_smoothing_sigma
        )
    elif (args.downsampling_shrink_factor is None) and (args.downsampling_smoothing_sigma is None):
        # do not downsample fixed and moving images
        pass
    else:
        raise ValueError("one of `downsampling-shrink-factor` or `downsampling-smoothing-sigma` have not been specified"
                         "you must either leave both as the default `None` or specify both")
    return fixed_image, moving_image


def setup_optimizer(
        registration_method: sitk.ImageRegistrationMethod,
        args: Namespace
) -> sitk.ImageRegistrationMethod:
    if args.optimizer == "GradientDescent":
        registration_method.SetOptimizerAsGradientDescent(
            learningRate=args.gradient_descent_learning_rate,
            numberOfIterations=args.max_iterations,
            convergenceMinimumValue=args.gradient_descent_convergence_min_value,
            convergenceWindowSize=args.gradient_descent_convergence_window_size
        )
    elif args.optimizer == "L-BFGS2":
        registration_method.SetOptimizerAsLBFGS2(
            solutionAccuracy=args.lbfgs_solution_accuracy,
            numberOfIterations=args.max_iterations,
            hessianApproximateAccuracy=args.lbfgs_hessian_approximate_accuracy,
            deltaConvergenceDistance=args.lbfgs_delta_convergence_distance,
            deltaConvergenceTolerance=args.lbfgs_delta_convergence_tolerance,
            lineSearchMaximumEvaluations=args.lbfgs_linesearch_maximum_evaluations
        )
    else:
        raise ValueError("`optimizer` is invalid and was not caught")
    return registration_method


def setup_similarity_metric(
        registration_method: sitk.ImageRegistrationMethod,
        args: Namespace
) -> sitk.ImageRegistrationMethod:
    if args.similarity_metric == "MeanSquares":
        registration_method.SetMetricAsMeanSquares()
    elif args.similarity_metric == "Correlation":
        registration_method.SetMetricAsCorrelation()
    elif args.similarity_metric == "JointHistogramMutualInformation":
        registration_method.SetMetricAsJointHistogramMutualInformation(
            numberOfHistogramBins=args.mutual_information_num_histogram_bins,
            varianceForJointPDFSmoothing=args.joint_mutual_information_joint_smoothing_variance
        )
    elif args.similarity_metric == "MattesMutualInformation":
        registration_method.SetMetricAsMattesMutualInformation(
            numberOfHistogramBins=args.mutual_information_num_histogram_bins
        )
    else:
        raise ValueError("`similarity-metric` is invalid and was not caught")
    if args.similarity_metric_sampling_strategy == "None":
        strategy = registration_method.NONE
    elif args.similarity_metric_sampling_strategy == "Regular":
        strategy = registration_method.REGULAR
    elif args.similarity_metric_sampling_strategy == "Random":
        strategy = registration_method.RANDOM
    else:
        raise ValueError("`similarity-sampling-strategy` is invalid but was not caught")
    registration_method.SetMetricSamplingStrategy(strategy)
    seed = (
        args.similarity_metric_sampling_seed if args.similarity_metric_sampling_seed is not None
        else sitk.sitkWallClock
    )
    registration_method.SetMetricSamplingPercentage(args.similarity_metric_sampling_rate, seed)
    return registration_method


def setup_interpolator(
        registration_method: sitk.ImageRegistrationMethod,
        args: Namespace
) -> sitk.ImageRegistrationMethod:
    if args.interpolator == "Linear":
        interpolator = sitk.sitkLinear
    elif args.interpolator == "NearestNeighbour":
        interpolator = sitk.sitkNearestNeighbor
    elif args.interpolator == "Gaussian":
        interpolator = sitk.sitkGaussian
    else:
        raise ValueError("`interpolator` is invalid and was not caught")
    registration_method.SetInterpolator(interpolator)
    return registration_method


def setup_transform(
        registration_method: sitk.ImageRegistrationMethod,
        fixed_image: sitk.Image,
        moving_image: sitk.Image,
        args: Namespace
) -> sitk.ImageRegistrationMethod:
    if args.transform_type == "Euler3D":
        transform_type = sitk.Euler3DTransform()
    elif args.transform_type == "Euler2D":
        transform_type = sitk.Euler2DTransform()
    else:
        raise ValueError("`transform-type` is invalid and was not caught")
    if args.centering_initialization == "Geometry":
        centering_initialization = sitk.CenteredTransformInitializerFilter.GEOMETRY
    elif args.centering_initialization == "Moments":
        centering_initialization = sitk.CenteredTransformInitializerFilter.MOMENTS
    else:
        raise ValueError("`centering_initialization` is invalid and was not caught")
    initial_transform = sitk.CenteredTransformInitializer(
        fixed_image, moving_image,
        transform_type, centering_initialization
    )
    registration_method.SetInitialTransform(initial_transform)
    return registration_method


def setup_multiscale_progression(
        registration_method: sitk.ImageRegistrationMethod,
        args: Namespace
) -> sitk.ImageRegistrationMethod:
    if (args.shrink_factors is not None) and (args.smoothing_sigmas is not None):
        if len(args.shrink_factors) == len(args.smoothing_sigmas):
            registration_method.SetShrinkFactorsPerLevel(args.shrink_factors)
            registration_method.SetSmoothingSigmasPerLevel(args.smoothing_sigmas)
            return registration_method
        else:
            raise ValueError("`shrink-factors` and `smoothing-sigmas` must have same length")
    elif (args.shrink_factors is None) and (args.smoothing_sigmas is None):
        return registration_method
    else:
        raise ValueError("one of `shrink-factors` or `smoothing-sigmas` have not been specified. you must "
                         "either leave both as the default `None` or specify both (with equal length)")


def registration(args: Namespace):
    # save the arguments of this registration to a yaml file
    # this has the added benefit of ensuring up-front that we can write files to the "output" that was provided,
    # so we do not waste a lot of time doing the registration and then crashing at the end because of write permissions
    write_args_to_yaml(args, f"{args.output}.yaml")
    fixed_image, moving_image = read_and_downsample_images(args)
    # create the object
    registration_method = sitk.ImageRegistrationMethod()
    # set it up
    registration_method = setup_optimizer(registration_method, args)
    registration_method = setup_similarity_metric(registration_method, args)
    registration_method = setup_interpolator(registration_method, args)
    registration_method = setup_transform(registration_method, fixed_image, moving_image, args)
    registration_method = setup_multiscale_progression(registration_method, args)
    # monitor the metric over time - init the list and add the callback
    metric_history = []
    registration_method.AddCommand(
        sitk.sitkIterationEvent,
        create_metric_tracking_callback(registration_method, metric_history, args.verbose)
    )
    # do the registration
    transform = registration_method.Execute(fixed_image, moving_image)
    # write transform to file
    sitk.WriteTransform(transform, f"{args.output}.mat")
    # save the metric history
    write_metrics_to_csv(metric_history, f"{args.output}_metric_history.csv")
    # optionally, create a plot of the metric history and save it
    if args.plot_metric_history:
        create_and_save_metrics_plot(metric_history, f"{args.output}_metric_history.png")


def main():
    registration(create_parser().parse_args())


if __name__ == "__main__":
    main()
