from __future__ import annotations

# external imports
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
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


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description='blRegistration: SimpleITK Registration Tool',
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
        "--initial-transform", "-it", default=None, type=str, metavar="FN",
        help="the path to a file that can be read by sitk.ReadTransform and that contains the transform you want "
             "to initialize the registration process with (e.g. can obtain using blRegister)"
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


def main():
    args = create_parser().parse_args()


if __name__ == "__main__":
    pass
