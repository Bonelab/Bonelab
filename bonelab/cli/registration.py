from __future__ import annotations

# external imports
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace
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
            raise ValueError(f"`{argument_name}` must be one of {options}. got {s}")

    return argument_checker


# TODO: The plan is to have several options for optimizer, metric, interpolator, and initialization
# TODO: Optimizers - GradientDescent, L-BFGS2
# TODO: Metrics - MeanSquares, Correlation, JointHistogramMutualInformation, MattesMutualInformation
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
        "--similarity-metric", "-sm", default="MeanSquares", metavar="STR",
        type=create_string_argument_checker(
            ["MeanSquares", "Correlation", "JointHistogramMutualInformation", "MattesMutualInformation"],
            "similarity-metric"
        ),
        help="the similarity metric to use, options: `MeanSquares`, `Correlation`, "
             "`JointHistogramMutualInformation`, `MattesMutualInformation`"
    )
    parser.add_argument(
        "--interpolation-method", "-im", default="Linear", metavar="STR",
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
    elif (args.downsampling_shrink_factor is None) and (arg.downsampling_smoothing_sigma is None):
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
    return registration_method


def setup_similarity_metric(
        registration_method: sitk.ImageRegistrationMethod,
        args: Namespace
) -> sitk.ImageRegistrationMethod:
    return registration_method


def setup_interpolator(
        registration_method: sitk.ImageRegistrationMethod,
        args: Namespace
) -> sitk.ImageRegistrationMethod:
    if args.interpolator == "Linear":
        interpolation_method = sitk.sitkLinear
    elif args.interpolator == "NearestNeighbour":
        interpolation_method = sitk.sitkNearestNeighbor
    elif args.interpolator == "Gaussian":
        interpolation_method = sitk.sitkGaussian
    else:
        raise ValueError("`interpolator` is invalid and was not caught")
    registration_method.SetInterpolator(interpolation_method)
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


def main():
    args = create_parser().parse_args()
    # save the arguments of this registration to a yaml file
    # this has the added benefit of ensuring up-front that we can write files to the "output" that was provided,
    # so we do not waste a lot of time doing the registration and then crashing at the end because of write permissions
    write_args_to_yaml(args, f"{args.output}.yaml")
    fixed_image, moving_image = read_and_downsample_images(args)
    registration_method = sitk.ImageRegistrationMethod()
    registration_method = setup_optimizer(registration_method, args)
    registration_method = setup_similarity_metric(registration_method, args)
    registration_method = setup_interpolator(registration_method, args)
    registration_method = setup_transform(registration_method, fixed_image, moving_image, args)
    metric_history = []
    registration_method.AddCommand(
        sitk.sitkIterationEvent,
        create_metric_tracking_callback(registration_method, metric_history, args.verbose)
    )
    transform = registration_method.Execute(fixed_image, moving_image)


if __name__ == "__main__":
    pass
