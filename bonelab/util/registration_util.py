from __future__ import annotations

import csv
import os
from argparse import ArgumentTypeError, Namespace

import SimpleITK as sitk
from typing import List, Callable
import yaml
from matplotlib import pyplot as plt

from bonelab.io.vtk_helpers import get_vtk_reader
from bonelab.util.multiscale_demons_registration_util import smooth_and_resample
from bonelab.util.time_stamp import message
from bonelab.util.vtk_util import vtkImageData_to_numpy

# CONSTANTS #
INTERPOLATORS = {
    "Linear": sitk.sitkLinear,
    "NearestNeighbour": sitk.sitkNearestNeighbor,
    "BSpline": sitk.sitkBSpline
}

INPUT_EXTENSIONS = [".aim", ".nii", ".nii.gz"]

TRANSFORM_EXTENSIONS = [".txt", ".tfm", ".xfm", ".hdf", ".mat"]


# FUNCTIONS #
def create_file_extension_checker(extensions: List[str], argument_name: str) -> Callable[[str], str]:
    """
    Create a function that checks that the given filename ends with one of the given extensions. If it does, return it,
    otherwise raise an error.

    Parameters
    ----------
    extensions : List[str]
        The list of extensions to check against.

    argument_name : str
        The name of the argument to check.

    Returns
    -------
    Callable[[str], str]
        A function that checks that the given filename ends with one of the given extensions. If it does, return it,
        otherwise raise an error.
    """
    def filename_checker(fn: str) -> str:
        """
        Check that the given filename ends with one of the given extensions. If it does, return it, otherwise raise an
        error.

        Parameters
        ----------
        fn : str
            The filename to check.

        Returns
        -------
        str
            The filename if it ends with one of the given extensions.
        """
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
    """
    Create a function that checks that the given string is one of the given options. If it is, return it, otherwise
    raise an error.

    Parameters
    ----------
    options : List[str]
        The list of options to check against.

    argument_name : str
        The name of the argument to check.

    Returns
    -------
    Callable[[str], str]
        A function that checks that the given string is one of the given options. If it is, return it, otherwise
        raise an error.
    """
    def argument_checker(s: str) -> str:
        """
        Check that the given string is one of the given options. If it is, return it, otherwise raise an error.

        Parameters
        ----------
        s : str
            The string to check.

        Returns
        -------
        str
            The string if it is one of the given options.
        """
        s = str(s)
        if s in options:
            return s
        else:
            raise ArgumentTypeError(f"`{argument_name}` must be one of {', '.join(options)} but got {s}")

    return argument_checker


def check_percentage(x: float) -> float:
    """
    Check that the given value is between 0.0 and 1.0. If it is, return it, otherwise raise an error.

    Parameters
    ----------
    x : float
        The value to check.

    Returns
    -------
    float
        The given value, if it is between 0.0 and 1.0.
    """
    x = float(x)
    if (x < 0.0) or (x > 1.0):
        raise ArgumentTypeError(f"value must be between 0.0 and 1.0, got {x}")
    return x


def get_output_base(output: str, extensions: List[str], silent: bool) -> str:
    """
    Get the base filename of the given output path, by removing the given extensions.

    Parameters
    ----------
    output : str
        The output path to get the base filename of.

    extensions : List[str]
        The extensions to remove from the output path.

    silent : bool
        Whether to suppress messages.

    Returns
    -------
    str
        The base filename of the given output path.
    """
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
    """
    Write the given arguments to the given filename in YAML format.

    Parameters
    ----------
    fn : str
        The filename to write the arguments to.

    args : Namespace
        The arguments to write.

    silent : bool
        Whether to suppress messages.

    Returns
    -------
    None
    """
    if not silent:
        message(f"Writing the input arguments to {fn}")
    with open(fn, "w") as f:
        yaml.dump(vars(args), f)


def check_inputs_exist(fns: List[Optional[str]], silent: bool) -> None:
    """
    Check that the given inputs exist, and raise an error if they don't.

    Parameters
    ----------
    fns : List[Optional[str]]
        The list of filenames to check.

    silent : bool
        Whether to suppress messages.

    Returns
    -------
    None
    """
    if not silent:
        message(f"Checking that inputs exist before continuing.")
    for fn in fns:
        if fn is not None:
            if not os.path.isfile(fn):
                raise FileNotFoundError(f"{fn} does not exist")
    if not silent:
        message("Inputs exist.")


def check_for_output_overwrite(outputs: List[str], overwrite: bool, silent: bool) -> None:
    """
    Check if the given outputs already exist, and raise an error if they do and `overwrite` is not enabled.

    Parameters
    ----------
    outputs : List[str]
        The list of output filenames to check.

    overwrite : bool
        Whether to overwrite existing outputs.

    silent : bool
        Whether to suppress messages.

    Returns
    -------
    None
    """
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
    """
    Read the image with the given filename and image name.

    Parameters
    ----------
    fn : str
        The filename of the image to read.

    image_name : str
        The name of the image to read.

    silent : bool
        Whether to suppress messages.

    Returns
    -------
    sitk.Image
        The image read from the given filename.
    """
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
    """
    Write the given metrics history to the given filename.

    Parameters
    ----------
    fn : str
        The filename to write the metrics history to.

    metric_history : List[float]
        The metrics history to write.

    silent : bool
        Whether to suppress messages.

    Returns
    -------
    None
    """
    if not silent:
        message(f"Writing metrics to {fn}.")
    with open(fn, "w") as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(metric_history)


def create_and_save_metrics_plot(fn: str, metrics_history: List[float], silent: bool) -> None:
    """
    Create a plot of the metrics history and save it to the given filename.

    Parameters
    ----------
    fn : str
        The filename to save the plot to.

    metrics_history : List[float]
        The metrics history to plot.

    silent : bool
        Whether to suppress messages.

    Returns
    -------
    None
    """
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
        moving_is_downsampled_atlas: bool,
        silent: bool
) -> Tuple[sitk.Image, sitk.Image]:
    """
    Read the fixed and moving images, optionally downsampling both or just the fixed image if the moving image is an
    atlas that is already downsampled.

    Parameters
    ----------
    fixed_image : str
        The fixed image filename.

    moving_image : str
        The moving image filename.

    downsampling_shrink_factor : float
        The downsampling shrink factor.

    downsampling_smoothing_sigma : float
        The downsampling smoothing sigma.

    moving_is_downsampled_atlas : bool
        Whether the moving image is an atlas that is already downsampled.

    silent : bool
        Whether to suppress messages.

    Returns
    -------
    Tuple[sitk.Image, sitk.Image]
        The fixed and moving images.
    """
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
        if not moving_is_downsampled_atlas:
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
    """
    Set up the optimizer for the registration method.

    Parameters
    ----------
    registration_method : sitk.ImageRegistrationMethod
        The registration method to set up.

    max_iterations : int
        The maximum number of iterations to run the optimizer for.

    gradient_descent_learning_rate : float
        The learning rate for the gradient descent optimizer.

    gradient_descent_convergence_min_value : float
        The minimum value for the convergence window for the gradient descent optimizer.

    gradient_descent_convergence_window_size : int
        The size of the convergence window for the gradient descent optimizer.

    powell_max_line_iterations : int
        The maximum number of line iterations for the Powell optimizer.

    powell_step_length : float
        The step length for the Powell optimizer.

    powell_step_tolerance : float
        The step tolerance for the Powell optimizer.

    powell_value_tolerance : float
        The value tolerance for the Powell optimizer.

    optimizer : str
        The optimizer to use.

    silent : bool
        Whether to print messages.

    Returns
    -------
    sitk.ImageRegistrationMethod
        The registration method with the optimizer set up.
    """
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
    """
    Create and set the similarity metric for the registration method.

    Parameters
    ----------
    registration_method : sitk.ImageRegistrationMethod
        The registration method to set the similarity metric for.

    similarity_metric : str
        The similarity metric to use. One of:
        MeanSquares
        Correlation
        JointHistogramMutualInformation
        MattesMutualInformation

    mutual_information_num_histogram_bins : int
        The number of histogram bins to use for the JointHistogramMutualInformation similarity metric.

    joint_mutual_information_joint_smoothing_variance : float
        The variance for joint PDF smoothing to use for the JointHistogramMutualInformation similarity metric.

    sampling_strategy : str
        The sampling strategy to use. One of:
        None
        Regular
        Random

    sampling_rate : float
        The sampling rate to use.

    seed : int
        The seed to use for the random number generator.

    silent : bool
        Whether to suppress messages.

    Returns
    -------
    sitk.ImageRegistrationMethod
        The registration method with the similarity metric set.
    """
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
    """
    Create an interpolator and add it to the registration method.

    Parameters
    ----------
    registration_method : sitk.ImageRegistrationMethod
        The registration method to add the interpolator to.

    interpolator : str
        The interpolator to use.

    silent : bool
        Whether to print messages.

    Returns
    -------
    sitk.ImageRegistrationMethod
        The registration method with the interpolator added.
    """
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
    """
    Create an initial transform and add it to the registration method.

    Parameters
    ----------
    registration_method : sitk.ImageRegistrationMethod
        The registration method to add the transform to.

    fixed_image : sitk.Image
        The fixed image.

    moving_image : sitk.Image
        The moving image.

    transform_type : str
        The type of transform to use.

    centering_initialization : str
        The type of centering initialization to use.

    silent : bool
        Whether or not to print messages.

    Returns
    -------

    """
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
        shrink_factors: Optional[List[int]],
        smoothing_sigmas: Optional[List[float]],
        silent: bool
) -> sitk.ImageRegistrationMethod:
    """
    Set up the multiscale progression for the registration method.

    Parameters
    ----------
    registration_method : sitk.ImageRegistrationMethod
        The registration method to add the multiscale progression to.

    shrink_factors : Optional[List[int]]
        The shrink factors to use for the multiscale progression.

    smoothing_sigmas : Optional[List[float]]
        The smoothing sigmas to use for the multiscale progression.

    silent : bool
        Whether or not to print messages.

    Returns
    -------
    sitk.ImageRegistrationMethod
        The registration method with the multiscale progression added.
    """
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
    """
    Check that the image size and shrink factors are compatible. If the smallest dimension of the image divided by the
    largest shrink factor is 1, then the image will be shrunk too much, such that the downsampled image will have a unit
    size (or smaller). If this is the case, an exception is raised.

    Parameters
    ----------
    fixed_image : sitk.Image
        The fixed image.

    moving_image : sitk.Image
        The moving image.

    shrink_factors : Optional[List[int]]
        The shrink factors.

    silent : bool
        Whether to print messages.

    Returns
    -------
    None
    """
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


def message_s(m: str, s: bool) -> None:
    """
    Print a message to the terminal, if the silent flag is not set.

    Parameters
    ----------
    m : str
        Message to print

    s : bool
        Silent flag

    Returns
    -------
    None
    """
    if not s:
        message(m)


def read_and_downsample_image(
        image: str,
        label: str,
        downsampling_shrink_factor: Optional[float],
        downsampling_smoothing_sigma: Optional[float],
        silent: bool
) -> sitk.Image:
    """
    Read and downsample the fixed and moving images.

    Parameters
    ----------
    image : str
        Image filename

    label : str
        Image label for terminal output

    downsampling_shrink_factor : Optional[float]
        The shrink factor to apply to the fixed and moving image before starting the registration. If `None`, the
        image will not be downsampled. If `downsampling_smoothing_sigma` is `None`, this parameter must also be `None`

    downsampling_smoothing_sigma : Optional[float]
        The smoothing sigma to apply to the fixed and moving image before starting the registration. If `None`, the
        image will not be smoothed. If `downsampling_shrink_factor` is `None`, this parameter must also be `None`

    silent : bool
        Silent flag

    Returns
    -------
    sitk.Image
        The image, possibly downsampled and smoothed
    """
    message_s("Reading inputs.", silent)
    # load images, cast to single precision float
    image = sitk.Cast(read_image(image, label, silent), sitk.sitkFloat32)
    # optionally, downsample the fixed and moving images
    if (downsampling_shrink_factor is not None) and (downsampling_smoothing_sigma is not None):
        message_s(f"Downsampling and smoothing inputs with shrink factor {downsampling_shrink_factor} and sigma "
                  f"{downsampling_smoothing_sigma}.", silent)
        image = smooth_and_resample(
            image, downsampling_shrink_factor, downsampling_smoothing_sigma
        )
    elif (downsampling_shrink_factor is None) and (downsampling_smoothing_sigma is None):
        # do not downsample fixed and moving images
        message_s("Using inputs at full resolution.", silent)
    else:
        raise ValueError("one of `downsampling-shrink-factor` or `downsampling-smoothing-sigma` have not been specified"
                         " - you must either leave both as the default `None` or specify both")
    return image
