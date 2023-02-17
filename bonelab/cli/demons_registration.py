from __future__ import annotations

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import SimpleITK as sitk

from bonelab.util.vtk_util import vtkImageData_to_numpy
from bonelab.io.vtk_helpers import get_vtk_reader
from bonelab.util.multiscale_registration import multiscale_demons, DEMONS_FILTERS


def demons_type_checker(s: str) -> s:
    s = str(s)
    if s in DEMONS_FILTERS.keys():
        return s
    else:
        return ValueError(f"Demons type {s}, not valid, please choose from: {list(DEMONS_FILTERS.keys())}")


def create_parser() -> ArgumentParser:

    parser = ArgumentParser(
        description='blDemonsRegister: Demons Registration Tool',
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "fixed_image", type=str, metavar="FIXED",
        help="path to the fixed image (don't use DICOMs, AIM  or NIfTI should work)"
    )
    parser.add_argument(
        "moving_image", type=str, metavar="MOVING",
        help="path to the moving image (don't use DICOMs, AIM  or NIfTI should work)"
    )
    parser.add_argument(
        "displacement_field", type=str, metavar="DISPLACEMENT",
        help="path to where you want the final displacement field saved to, "
             "use a sitk.WriteImage compatible extension"
    )
    parser.add_argument(
        "--initial-transform", "-it", default=None, type=str, metavar="FN",
        help="the path to a file that can be read by sitk.ReadTransform and that contains the transform you want"
             "to initialize the registration process with (e.g. can obtain using blRegister)"
    )
    parser.add_argument(
        "--demons-type", "-dt", default="demons", type=demons_type_checker, metavar="STR",
        help=f"type of demons algorithm to use, options: {list(DEMONS_FILTERS.keys())}"
    )
    parser.add_argument(
        "--max-iterations", "-mi", default=100, type=int, metavar="N",
        help="number of iterations to run registration algorithm for at each stage"
    )
    parser.add_argument(
        "--displacement-smoothing-std", "-ds", default=1.0, type=float, metavar="X",
        help="standard deviation for the Gaussian smoothing applied to the displacement field at each step"
    )
    parser.add_argument(
        "--update-smoothing-std", "-us", default=1.0, type=float, metavar="X",
        help="standard deviation for the Gaussian smoothing applied to the update field at each step"
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

    return parser


def read_image(fn: str) -> sitk.Image:
    # first let's see if SimpleITK can do it
    try:
        return sitk.ReadImage(fn)
    except RuntimeError as err:
        if "Unable to determine ImageIO reader" in err:
            # now let's see if the vtk helpers in Bonelab can handle it
            reader = get_vtk_reader(fn)
            if reader is None:
                raise ValueError(f"Could not find a reader for {fn}")
            reader.SetFileName(fn)
            reader.Update()
            vtk_image = reader.GetOutput()
            image = sitk.GetImageFromArray(vtkImageData_to_numpy(vtk_image))
            image.SetSpacing(vtk_image.GetSpacing())
            image.SetOrigin(vtk_image.GetOrigin())
            return image
        else:
            raise err


def align_images(data: List[Tuple[sitk.Image, List[int]]]) -> List[sitk.Image]:
    min_position = np.asarray([p for _, p in data]).min(axis=0)
    pad_lower = [p - min_position for _, p in data]
    max_shape = np.asarray([(img.GetSize() + pl) for (img, _), pl in zip(data, pad_lower)]).max(axis=0)
    pad_upper = [(max_shape - (img.GetSize() + pl)) for (img, _), pl in zip(data, pad_lower)]
    pad_lower = [[int(l) for l in pl] for pl in pad_lower]
    pad_upper = [[int(u) for u in pu] for pu in pad_upper]
    return [sitk.ConstantPad(img, tuple(pl), tuple(pu)) for (img, _), pl, pu in zip(data, pad_lower, pad_upper)]


def main():
    args = create_parser().parse_args()
    # load images, cast to single precision float
    fixed_image = sitk.Cast(read_image(args.fixed_image), sitk.sitkFloat32)
    moving_image = sitk.Cast(read_image(args.moving_image), sitk.sitkFloat32)
    # optionally load the initial transform
    if args.initial_transform is not None:
        initial_transform = sitk.ReadTransform(args.initial_transform)
    else:
        initial_transform = None
    # construct multiscale progression
    if (args.shrink_factors is not None) and (args.smoothing_sigmas is not None):
        if len(args.shrink_factors) == len(args.smoothing_sigmas):
            multiscale_progression = list(zip(args.shrink_factors, args.smoothing_sigmas))
        else:
            return ValueError("`shrink-factors` and `smoothing-sigmas` must have same length")
    else:
        if (args.shrink_factors is None) and (args.smoothing_sigmas is None):
            multiscale_progression = None
        else:
            raise ValueError("one of `shrink-factors` or `smoothing-sigmas` have not been specified. you must "
                             "either leave both as the default `None` or specify both (with equal length)")

    displacement_field = multiscale_demons(
        fixed_image, moving_image, args.demons_type, args.max_iterations,
        demons_displacement_field_smooth_std=args.displacement_smoothing_std,
        demons_update_field_smooth_std=args.update_smoothing_std,
        initial_transform=initial_transform,
        multiscale_progression=multiscale_progression
    )


if __name__ == "__main__":
    main()
