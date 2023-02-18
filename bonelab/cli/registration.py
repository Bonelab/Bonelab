from __future__ import annotations

# external imports
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace
import SimpleITK as sitk
from matplotlib import pyplot as plt
import csv
import yaml

# internal imports
from bonelab.util.vtk_util import vtkImageData_to_numpy
from bonelab.io.vtk_helpers import get_vtk_reader
from bonelab.util.multiscale_registration import smooth_and_resample, create_metric_tracking_callback


def output_format_checker(s: str) -> str:
    s = str(s)
    if s in ["transform", "image", "compressed-image"]:
        return s
    else:
        raise ValueError(f"output-format must be `transform`, `image`, or `compressed-image`. got {s}")


# TODO: The plan is to have several options for optimizer, metric, interpolator, and initialization
# TODO: Optimizers - GradientDescent, L-BFGS2
# TODO: Metrics - MeanSquares, Correlation, JointHistogramMutualInformation, MattesMutualInformation
# TODO: Interpolators - NN, Linear, Gaussian
# TODO: Initialization - GEOMETRY, MOMENTS
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
        "--output-format", "-of", default="image", type=output_format_checker, metavar="STR",
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


def main():
    args = create_parser().parse_args()
    # save the arguments of this registration to a yaml file
    # this has the added benefit of ensuring up-front that we can write files to the "output" that was provided,
    # so we do not waste a lot of time doing the registration and then crashing at the end because of write permissions
    write_args_to_yaml(args, f"{args.output}.yaml")
    fixed_image, moving_image = read_and_downsample_images(args)


if __name__ == "__main__":
    pass
