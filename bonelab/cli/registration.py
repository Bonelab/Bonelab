from __future__ import annotations

# external imports
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import SimpleITK as sitk
from matplotlib import pyplot as plt

# internal imports
from bonelab.util.vtk_util import vtkImageData_to_numpy
from bonelab.io.vtk_helpers import get_vtk_reader
from bonelab.util.multiscale_registration import create_metric_tracking_callback


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
