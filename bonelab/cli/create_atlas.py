from __future__ import annotations

# external imports
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace
import SimpleITK as sitk

# internal imports
from bonelab.cli.registration import (
    read_image, check_inputs_exist, check_for_output_overwrite, write_args_to_yaml,
    create_file_extension_checker, create_string_argument_checker,
    INPUT_EXTENSIONS, get_output_base, write_metrics_to_csv, create_and_save_metrics_plot
)
from bonelab.cli.demons_registration import IMAGE_EXTENSIONS, DEMONS_FILTERS, demons_type_checker
from bonelab.util.time_stamp import message
from bonelab.util.multiscale_registration import multiscale_demons, smooth_and_resample


# functions
def create_initial_average_atlas() -> sitk.Image:
    pass


def update_average_atlas() -> sitk.Image:
    pass


def get_atlas_difference(atlas: sitk.Image, prior_atlas: sitk.Image) -> float:
    pass


def create_atlas_segmentation() -> sitk.Image:
    pass


def create_atlas(args: Namespace) -> None:
    # error checking
    output_base = get_output_base(args.atlas_average, INPUT_EXTENSIONS, args.silent)
    output_yaml = f"{output_base}.yaml"
    differences_csv = f"{output_base}_atlas_differences.csv"
    differences_png = f"{output_base}_atlas_differences.png"
    # check same number of images and segmentations and that there are at least 2 reference images
    if len(args.images) != len(args.segmentations):
        raise ValueError("Number of input images and segmentations do not match.")
    if len(args.images) < 2:
        raise ValueError(f"Cannot construct an average atlas with less than 2 reference images, "
                         f"given {len(args.images)}")
    check_inputs_exist(args.images + args.segmentations, args.silent)
    check_for_output_overwrite(
        [args.atlas_average, args.atlas_segmentation, output_yaml, differences_csv, differences_png],
        args.overwrite, args.silent
    )
    # write args to yaml file
    write_args_to_yaml(output_yaml, args, args.silent)
    # create the first atlas using affine registration
    prior_atlas = create_atlas_segmentation()
    # iteratively update the atlas until convergence
    differences = []
    for i in range(args.atlas_iterations):
        atlas = update_average_atlas()
        differences.append(get_atlas_difference(atlas, prior_atlas))
        if differences[-1] < args.atlas_convergence_threshold:
            if not args.silent:
                message(f"Average atlas converged after {i+1} iterations.")
            break
        else:
            prior_atlas = atlas
    else:
        if not args.silent:
            message(f"Average atlas did not converge after {args.atlas_iterations} iterations."
                    f"Final residual was {atlas_residual}, threshold was {args.atlas_convergence_threshold}.")
    # get the atlas segmentation
    atlas_segmentation = create_atlas_segmentation()
    # write outputs
    write_metrics_to_csv(differences_csv, differences, args.silent)
    if args.plot_metric_history:
        create_and_save_metrics_plot(differences_png, differences, args.silent)
    if not args.silent:
        message(f"Writing average atlas to {args.atlas_average}")
    sitk.WriteImage(atlas, args.atlas_average)
    if not args.silent:
        message(f"Writing atlas segmentation to {args.atlas_segmentation}")
    sitk.WriteImage(atlas_segmentation, args.atlas_segmentation)

    # step 6: use the converged transformations to transform all segmentations to the atlas
    # step 7: use STAPLE to generate the final atlas segmentation
    # step 8: write the atlas image and segmentation to file

    pass


# parser
def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="This tool generates a segmented average-atlas image from a list of images with segmentations. "
                    "The atlas generation procedure was originally published in (1) and was evaluated in (2). "
                    "The steps of the procedure are: (1) Select the first image given in the list as the atlas "
                    "image, (2) affinely register all other images to the atlas image, (3) transform all images "
                    "to the space of the atlas image, compute the average image, and set this as the new atlas "
                    "image, (4) deformably register all images to the atlas image, (5) transform all images to the "
                    "space of the atlas image, re-compute the average image, and set this as the new atlas "
                    "image, (6) repeat steps 4 and 5 until the atlas image has converged, (7) deformably register "
                    "all images to the final atlas image, (8) transform all segmentations to the atlas space "
                    "using nearest neighbour interpolation, (9) use STAPLE to generate the atlas segmentation, "
                    "(10) write the average-atlas and atlas segmentation to file. "
                    "The user is given all of of the necessary command line options to configure both the affine and "
                    "deformable registration parameters so that the method of atlas generation can be consistent with "
                    "the method of atlas-based segmentation using the atlas.",
        epilog="(1) DOI: 10.1109/MMBIA.2001.991733, (2) DOI: 10.1016/j.neuroimage.2003.11.010 ",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "images",
        type=create_file_extension_checker(INPUT_EXTENSIONS, "images"), nargs="+",
        metavar="IMAGES",
        help=f"Provide image filenames ({', '.join(INPUT_EXTENSIONS)})."
    )
    parser.add_argument(
        "segmentations",
        type=create_file_extension_checker(INPUT_EXTENSIONS, "segmentations"), nargs="+",
        metavar="SEGMENTATIONS",
        help=f"Provide image filenames ({', '.join(INPUT_EXTENSIONS)})."
    )
    parser.add_argument(
        "atlas_average",
        type=create_file_extension_checker(IMAGE_EXTENSIONS, "atlas_average"),
        metavar="ATLAS_AVERAGE",
        help=f"Provide output filename for the average-atlas image ({', '.join(IMAGE_EXTENSIONS)})."
    )
    parser.add_argument(
        "atlas_segmentation",
        type=create_file_extension_checker(IMAGE_EXTENSIONS, "atlas_segmentation"),
        metavar="ATLAS_SEGMENTATION",
        help=f"Provide output filename for the atlas segmentation image ({', '.join(IMAGE_EXTENSIONS)})."
    )
    parser.add_argument(
        "--overwrite", "-ow", default=False, action="store_true",
        help="enable this flag to overwrite existing files, if they exist at output targets"
    )
    # image pre-processing
    parser.add_argument(
        "--downsampling-shrink-factor", "-dsf", type=float, default=None, metavar="X",
        help="the shrink factor to apply to the fixed and moving image before starting the registration"
    )
    parser.add_argument(
        "--downsampling-smoothing-sigma", "-dss", type=float, default=None, metavar="X",
        help="the smoothing sigma to apply to the fixed and moving image before starting the registration"
    )
    # atlas iteration parameters
    parser.add_argument(
        "--atlas-iterations", "-ai", default=100, type=int, metavar="N",
        help="number of iterations when updating the atlas"
    )
    parser.add_argument(
        "--atlas-convergence-threshold", "-act", default=1e-3, type=float, metavar="X",
        help="threshold for convergence of atlas updates"
    )
    # deformable registration specs
    parser.add_argument(
        "--centering-initialization", "-ci", default="Geometry", metavar="STR",
        type=create_string_argument_checker(["Geometry", "Moments"], "centering-initialization"),
        help="if no initial transform provided, the centering initialization to use. "
             "options: `Geometry`, `Moments`"
    )
    parser.add_argument(
        "--demons-type", "-dt", default="demons", type=demons_type_checker, metavar="STR",
        help=f"type of demons algorithm to use. options: {list(DEMONS_FILTERS.keys())}"
    )
    parser.add_argument(
        "--max-iterations", "-mi", default=100, type=int, metavar="N",
        help="number of iterations to run registration algorithm for at each stage"
    )
    parser.add_argument(
        "--displacement-smoothing-std", "-ds", default=1.0, type=float, metavar="X",
        help="standard deviation for the Gaussian smoothing applied to the displacement field at each step."
             "this is how you control the elasticity of the smoothing of the deformation"
    )
    parser.add_argument(
        "--update-smoothing-std", "-us", default=1.0, type=float, metavar="X",
        help="standard deviation for the Gaussian smoothing applied to the update field at each step."
             "this is how you control the viscosity of the smoothing of the deformation"
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
    # output flags
    parser.add_argument(
        "--silent", "-s", default=False, action="store_true",
        help="enable this flag to suppress terminal output about how the registration is proceeding"
    )
    parser.add_argument(
        "--plot-metric-history", "-pmh", default=False, action="store_true",
        help="enable this flag to save a plot of the metric history to file in addition to the raw data"
    )

    return parser


# main
def main():
    create_atlas(create_parser().parse_args())


if __name__ == "__main__":
    main()
