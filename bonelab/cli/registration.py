from __future__ import annotations

# external imports
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace, ArgumentTypeError
import SimpleITK as sitk
from matplotlib import pyplot as plt
import csv
import yaml
from typing import List, Callable
import os

# internal imports
from bonelab.util.time_stamp import message
from bonelab.util.vtk_util import vtkImageData_to_numpy
from bonelab.io.vtk_helpers import get_vtk_reader
from bonelab.util.multiscale_registration import smooth_and_resample, MetricTrackingCallback

# define an interpolators dict
INTERPOLATORS = {
    "Linear": sitk.sitkLinear,
    "NearestNeighbour": sitk.sitkNearestNeighbor,
    "BSpline": sitk.sitkBSpline
}

# define file extensions that we consider available for input images
INPUT_EXTENSIONS = [".aim", ".nii", ".nii.gz"]

# define file extensions that we would consider available for saving transforms
TRANSFORM_EXTENSIONS = [".txt", ".tfm", ".xfm", ".hdf", ".mat"]


def create_file_extension_checker(extensions: List[str], argument_name: str) -> Callable[[str], str]:
    def filename_checker(fn: str) -> str:
        fn = str(fn)
        extension_matched = False
        for ext in extensions:
            if fn.lower().endswith(ext.lower()):
                extension_matched = True
        if extension_matched:
            return fn
        else:
            raise ArgumentTypeError(f"given filename for {argument_name} must end with one of {', '.join(extensions)} "
                                    f"but got {fn}")

    return filename_checker


def create_string_argument_checker(options: List[str], argument_name: str) -> Callable[[str], str]:
    def argument_checker(s: str) -> str:
        s = str(s)
        if s in options:
            return s
        else:
            raise ArgumentTypeError(f"`{argument_name}` must be one of {', '.join(options)} but got {s}")

    return argument_checker


def check_percentage(x: float) -> float:
    x = float(x)
    if (x < 0.0) or (x > 1.0):
        raise ArgumentTypeError(f"value must be between 0.0 and 1.0, got {x}")
    return x


def get_output_base(output: str, extensions: List[str], silent: bool) -> str:
    if not silent:
        message("Extracting the base filename from the given output path...")
    for ext in extensions:
        if output.lower().endswith(ext):
            output_base = output[:(-len(ext))]
            if not silent:
                message(f"Base filename is {output_base}")
            return output_base
    raise ValueError("output base could not be created because the output does not end with an available extension")


def write_args_to_yaml(fn: str, args: Namespace, silent: bool) -> None:
    if not silent:
        message(f"Writing the input arguments to {fn}")
    with open(fn, "w") as f:
        yaml.dump(vars(args), f)


def check_inputs_exist(fns: List[Optional[str]], silent: bool) -> None:
    if not silent:
        message(f"Checking that inputs exist before continuing.")
    for fn in fns:
        if fn is not None:
            if not os.path.isfile(fn):
                raise FileNotFoundError(f"{fn} does not exist")
    if not silent:
        message("Inputs exist.")


def check_for_output_overwrite(outputs: List[str], overwrite: bool, silent: bool) -> None:
    if overwrite:
        if not silent:
            message("`--overwrite` is enabled, proceeding without checking if outputs already exist.")
        return
    existing_outputs = []
    for output in outputs:
        if os.path.isfile(output):
            existing_outputs.append(output)
    if len(existing_outputs) > 0:
        raise FileExistsError(f"the following output files already exist: {', '.join(existing_outputs)}. Either enable "
                              f"the `--overwrite` option, move these files, or choose a different `output` filename.")


def read_image(fn: str, image_name: str, silent: bool) -> sitk.Image:
    if not silent:
        message(f"Reading {image_name} from {fn}.")
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


def write_metrics_to_csv(fn: str, metric_history: List[float], silent: bool) -> None:
    if not silent:
        message(f"Writing metrics to {fn}.")
    with open(fn, "w") as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(metric_history)


def create_and_save_metrics_plot(fn: str, metrics_history: List[float], silent: bool) -> None:
    if not silent:
        message(f"Saving metrics plot to {fn}.")
    plt.figure()
    plt.plot(metrics_history, "k-o")
    plt.xlabel('iteration')
    plt.ylabel('metric')
    plt.grid()
    plt.savefig(fn)


def read_and_downsample_images(
        fixed_image: str,
        moving_image: str,
        downsampling_shrink_factor: float,
        downsampling_smoothing_sigma: float,
        silent: bool
) -> Tuple[sitk.Image, sitk.Image]:
    if not silent:
        message("Reading inputs.")
    # load images, cast to single precision float
    fixed_image = sitk.Cast(read_image(fixed_image, "fixed_image", silent), sitk.sitkFloat32)
    moving_image = sitk.Cast(read_image(moving_image, "moving_image", silent), sitk.sitkFloat32)
    # optionally, downsample the fixed and moving images
    if (downsampling_shrink_factor is not None) and (downsampling_smoothing_sigma is not None):
        if not silent:
            message(f"Downsampling and smoothing inputs with shrink factor {downsampling_shrink_factor} and sigma "
                    f"{downsampling_smoothing_sigma}.")
        fixed_image = smooth_and_resample(
            fixed_image, downsampling_shrink_factor, downsampling_smoothing_sigma
        )
        moving_image = smooth_and_resample(
            moving_image, downsampling_shrink_factor, downsampling_smoothing_sigma
        )
    elif (downsampling_shrink_factor is None) and (downsampling_smoothing_sigma is None):
        # do not downsample fixed and moving images
        if not silent:
            message("Using inputs at full resolution.")
    else:
        raise ValueError("one of `downsampling-shrink-factor` or `downsampling-smoothing-sigma` have not been specified"
                         " - you must either leave both as the default `None` or specify both")
    return fixed_image, moving_image


def setup_optimizer(
        registration_method: sitk.ImageRegistrationMethod,
        max_iterations: int,
        gradient_descent_learning_rate: float,
        gradient_descent_convergence_min_value: float,
        gradient_descent_convergence_window_size: int,
        powell_max_line_iterations: int,
        powell_step_length: float,
        powell_step_tolerance: float,
        powell_value_tolerance: float,
        optimizer: str,
        silent: bool
) -> sitk.ImageRegistrationMethod:
    if optimizer == "GradientDescent":
        if not silent:
            message(f"Using {optimizer} with max iterations: {max_iterations:d}, learning rate: "
                    f"{gradient_descent_learning_rate:e}, convergence min value: "
                    f"{gradient_descent_convergence_min_value:e}, and convergence window size: "
                    f"{gradient_descent_convergence_window_size:e}")
        registration_method.SetOptimizerAsGradientDescent(
            learningRate=gradient_descent_learning_rate,
            numberOfIterations=max_iterations,
            convergenceMinimumValue=gradient_descent_convergence_min_value,
            convergenceWindowSize=gradient_descent_convergence_window_size
        )
    elif optimizer == "Powell":
        if not silent:
            message(f"Using {optimizer} with max line iterations: {powell_max_line_iterations:d}, step length: "
                    f"{powell_step_length:e}, step tolerance: {powell_step_tolerance:e}, and value tolerance: "
                    f"{powell_value_tolerance:e}")
        registration_method.SetOptimizerAsPowell(
            numberOfIterations=max_iterations,
            maximumLineIterations=powell_max_line_iterations,
            stepLength=powell_step_length,
            stepTolerance=powell_step_tolerance,
            valueTolerance=powell_value_tolerance
        )
    else:
        raise ValueError("`optimizer` is invalid and was not caught")
    return registration_method


def setup_similarity_metric(
        registration_method: sitk.ImageRegistrationMethod,
        similarity_metric: str,
        mutual_information_num_histogram_bins: int,
        joint_mutual_information_joint_smoothing_variance: float,
        sampling_strategy: str,
        sampling_rate: float,
        seed: int,
        silent: bool
) -> sitk.ImageRegistrationMethod:
    if not silent:
        message(f"Setting similarity metric: {similarity_metric}, strategy: {sampling_strategy}, seed: {seed}, "
                f"and sampling rate: {sampling_rate}.")
    if similarity_metric == "MeanSquares":
        registration_method.SetMetricAsMeanSquares()
    elif similarity_metric == "Correlation":
        registration_method.SetMetricAsCorrelation()
    elif similarity_metric == "JointHistogramMutualInformation":
        registration_method.SetMetricAsJointHistogramMutualInformation(
            numberOfHistogramBins=mutual_information_num_histogram_bins,
            varianceForJointPDFSmoothing=joint_mutual_information_joint_smoothing_variance
        )
    elif similarity_metric == "MattesMutualInformation":
        registration_method.SetMetricAsMattesMutualInformation(
            numberOfHistogramBins=mutual_information_num_histogram_bins
        )
    else:
        raise ValueError("`similarity-metric` is invalid and was not caught")
    if sampling_strategy == "None":
        registration_method.SetMetricSamplingStrategy(registration_method.NONE)
    elif sampling_strategy == "Regular":
        registration_method.SetMetricSamplingStrategy(registration_method.REGULAR)
    elif sampling_strategy == "Random":
        registration_method.SetMetricSamplingStrategy(registration_method.RANDOM)
    else:
        raise ValueError("`similarity-sampling-strategy` is invalid but was not caught")
    seed = seed if seed is not None else sitk.sitkWallClock
    registration_method.SetMetricSamplingPercentage(sampling_rate, seed)
    return registration_method


def setup_interpolator(
        registration_method: sitk.ImageRegistrationMethod,
        interpolator: str,
        silent: bool
) -> sitk.ImageRegistrationMethod:
    if not silent:
        message(f"Setting interpolator: {interpolator}")
    if interpolator in INTERPOLATORS:
        registration_method.SetInterpolator(INTERPOLATORS[interpolator])
    else:
        raise ValueError("`interpolator` is invalid and was not caught")
    return registration_method


def setup_transform(
        registration_method: sitk.ImageRegistrationMethod,
        fixed_image: sitk.Image,
        moving_image: sitk.Image,
        transform_type: str,
        centering_initialization: str,
        silent: bool
) -> sitk.ImageRegistrationMethod:
    if not silent:
        message(f"Initializing transform, with a transform type of {transform_type} "
                f"and a centering initialization of {centering_initialization}")
    if transform_type == "Euler3D":
        transform = sitk.Euler3DTransform()
    elif transform_type == "Euler2D":
        transform = sitk.Euler2DTransform()
    else:
        raise ValueError("`transform-type` is invalid and was not caught")
    if centering_initialization == "Geometry":
        initializer = sitk.CenteredTransformInitializerFilter.GEOMETRY
    elif centering_initialization == "Moments":
        initializer = sitk.CenteredTransformInitializerFilter.MOMENTS
    else:
        raise ValueError("`centering_initialization` is invalid and was not caught")
    initial_transform = sitk.CenteredTransformInitializer(
        fixed_image, moving_image,
        transform, initializer
    )
    registration_method.SetInitialTransform(initial_transform)
    return registration_method


def setup_multiscale_progression(
        registration_method: sitk.ImageRegistrationMethod,
        shrink_factors: List[int],
        smoothing_sigmas: List[float],
        silent: bool
) -> sitk.ImageRegistrationMethod:
    if (shrink_factors is not None) and (smoothing_sigmas is not None):
        if len(shrink_factors) == len(smoothing_sigmas):
            if not silent:
                message(f"Performing multiscale registration with shrink factors: "
                        f"{', '.join([str(sf) for sf in shrink_factors])}; "
                        f"and smoothing sigmas: "
                        f"{', '.join([str(ss) for ss in smoothing_sigmas])}")
            registration_method.SetShrinkFactorsPerLevel(shrink_factors)
            registration_method.SetSmoothingSigmasPerLevel(smoothing_sigmas)
            return registration_method
        else:
            raise ValueError("`shrink-factors` and `smoothing-sigmas` must have same length")
    elif (shrink_factors is None) and (smoothing_sigmas is None):
        if not silent:
            message("Not performing multiscale registration.")
        return registration_method
    else:
        raise ValueError("one of `shrink-factors` or `smoothing-sigmas` have not been specified. you must "
                         "either leave both as the default `None` or specify both (with equal length)")


def check_image_size_and_shrink_factors(
        fixed_image: sitk.Image,
        moving_image: sitk.Image,
        shrink_factors: Optional[List[int]],
        silent: bool
) -> None:
    if not silent:
        message("Checking that image size and shrink factors are compatible.")
    if shrink_factors is not None:
        smallest_dim = min(fixed_image.GetSize() + moving_image.GetSize())
        largest_shrink_factor = max(shrink_factors)
        if smallest_dim // largest_shrink_factor == 1:
            raise RuntimeError(f"The image sizes and shrink factors will result in an image being shrunk too much, "
                               f"such that the downsampled image will have a unit size (or smaller). Revise parameters."
                               f"\nfixed_image size: {fixed_image.GetSize()}"
                               f"\nmoving_image size: {moving_image.GetSize()}"
                               f"\nshrink_factors: {shrink_factors}")
        if not silent:
            message("Image size and shrink factors are compatible.")
    else:
        if not silent:
            message("No shrink factors given.")


def registration(args: Namespace):
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
        args.silent
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
    metric_callback = MetricTrackingCallback(registration_method, args.silent, False)
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
