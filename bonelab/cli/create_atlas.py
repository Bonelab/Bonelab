from __future__ import annotations

# external imports
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace
import SimpleITK as sitk
import numpy as np
import math
from scipy import stats
from typing import Tuple, List
from memory_profiler import profile

# internal imports
from bonelab.cli.registration import (
    read_image, check_inputs_exist, check_for_output_overwrite, write_args_to_yaml,
    create_file_extension_checker, create_string_argument_checker,
    INPUT_EXTENSIONS, get_output_base, write_metrics_to_csv, create_and_save_metrics_plot,
    setup_optimizer, setup_interpolator, setup_similarity_metric, setup_multiscale_progression,
    check_percentage, check_image_size_and_shrink_factors, INTERPOLATORS
)
from bonelab.cli.demons_registration import (
    IMAGE_EXTENSIONS, DEMONS_FILTERS, demons_type_checker, construct_multiscale_progression
)
from bonelab.util.time_stamp import message
from bonelab.util.multiscale_registration import multiscale_demons, smooth_and_resample


# functions
def affine_registration(atlas: sitk.Image, image: sitk.Image, args: Namespace) -> sitk.Transform:
    atlas, image = sitk.Cast(atlas, sitk.sitkFloat32), sitk.Cast(image, sitk.sitkFloat32)
    if (args.downsampling_shrink_factor is not None) and (args.downsampling_smoothing_sigma is not None):
        if not args.silent:
            message("Downsampling...")
        atlas = smooth_and_resample(
            atlas,
            args.downsampling_shrink_factor,
            args.downsampling_smoothing_sigma
        )
        image = smooth_and_resample(
            image,
            args.downsampling_shrink_factor,
            args.downsampling_smoothing_sigma
        )
    if not args.silent:
        message("Affinely registering...")
    registration_method = sitk.ImageRegistrationMethod()
    # hard-code to use the moments initialization of the transform
    registration_method.SetInitialTransform(
        sitk.CenteredTransformInitializer(
            atlas, image,
            sitk.AffineTransform(atlas.GetDimension()),
            sitk.CenteredTransformInitializerFilter.MOMENTS
        )
    )
    # but set up the optimizer, similarity metric, interpolator, and multiscale progression as normal using args
    registration_method = setup_optimizer(
        registration_method,
        args.max_affine_iterations,
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
    if not args.silent:
        message("Starting registration.")
    transform = registration_method.Execute(atlas, image)
    if not args.silent:
        message(f"Registration stopping condition: {registration_method.GetOptimizerStopConditionDescription()}")
    return transform


def create_initial_average_atlas(
        data: List[Tuple[sitk.Image, sitk.Image]], args: Namespace
) -> Tuple[sitk.Image, List[sitk.Transform]]:
    atlas = data[0][0]
    average_image = sitk.Image(*atlas.GetSize(), atlas.GetPixelID())
    average_image.CopyInformation(atlas)
    # the first image starts out with a identity transform because it is the first reference image
    transforms = [sitk.Transform()]
    for i, (image, _) in enumerate(data[1:]):
        if not args.silent:
            message("registering to atlas...")
        transform = affine_registration(atlas, image, args)
        if not args.silent:
            message("Adding transformed image to average image...")
        average_image = sitk.Add(average_image, sitk.Resample(image, atlas, transform, sitk.sitkLinear))
        transforms.append(transform)
    if not args.silent:
        message("Dividing accumulated average image by number of images...")
    return sitk.Divide(average_image, len(data) - 1), transforms


@profile()
def deformable_registration(
        atlas: sitk.Image, image: sitk.Image, transform: sitk.Transform, args: Namespace
) -> sitk.Transform:
    if (args.downsampling_shrink_factor is not None) and (args.downsampling_smoothing_sigma is not None):
        if not args.silent:
            message("Downsampling...")
        atlas = smooth_and_resample(
            atlas,
            args.downsampling_shrink_factor,
            args.downsampling_smoothing_sigma
        )
        image = smooth_and_resample(
            image,
            args.downsampling_shrink_factor,
            args.downsampling_smoothing_sigma
        )
    image = sitk.Resample(image, atlas, transform)
    displacement, _ = multiscale_demons(
        atlas, image,
        demons_type=args.demons_type,
        demons_iterations=args.max_demons_iterations,
        demons_displacement_field_smooth_std=args.displacement_smoothing_std,
        demons_update_field_smooth_std=args.update_smoothing_std,
        initial_transform=None,
        multiscale_progression=construct_multiscale_progression(
            args.shrink_factors, args.smoothing_sigmas, args.silent
        ),
        silent=args.silent
    )
    return sitk.DisplacementFieldTransform(sitk.Add(
        displacement,
        sitk.TransformToDisplacementField(
            transform,
            displacement.GetPixelID(),
            displacement.GetSize(),
            displacement.GetOrigin(),
            displacement.GetSpacing(),
            displacement.GetDirection()
        )
    ))


@profile()
def update_average_atlas(
        atlas: sitk.Image, data: List[Tuple[sitk.Image, sitk.Image]], transforms: List[sitk.Transform], args: Namespace
) -> Tuple[sitk.Image, List[sitk.Transform]]:
    average_image = sitk.Image(*atlas.GetSize(), atlas.GetPixelID())
    average_image.CopyInformation(atlas)
    updated_transforms = []
    for i, ((image, _), transform) in enumerate(zip(data, transforms)):
        if not args.silent:
            message("registering to atlas...")
        updated_transform = deformable_registration(atlas, image, transform, args)
        if not args.silent:
            message("Adding transformed image to average image...")
        average_image = sitk.Add(average_image, sitk.Resample(image, atlas, updated_transform, sitk.sitkLinear))
        updated_transforms.append(updated_transform)
    if not args.silent:
        message("Dividing accumulated average image by number of images...")
    return sitk.Divide(average_image, len(data)), updated_transforms


def get_atlas_difference(atlas: sitk.Image, prior_atlas: sitk.Image) -> float:
    # get the difference between the two images, take the mean of the absolute value of the differences
    atlas = sitk.GetArrayFromImage(atlas)
    prior_atlas = sitk.GetArrayFromImage(prior_atlas)
    return math.sqrt(((atlas-prior_atlas)**2).mean()) / atlas.max()


def create_atlas_segmentation(
        atlas: sitk.Image, data: List[Tuple[sitk.Image, sitk.Image]], transforms: List[sitk.Transform]
) -> sitk.Image:
    segmentations_np = []
    # loop through all the segmentations, transform to the atlas frame, append to a list
    for (_, segmentation), transform in zip(data, transforms):
        segmentations_np.append(
            sitk.GetArrayFromImage(sitk.Resample(segmentation, atlas, transform, sitk.sitkNearestNeighbor))
        )
    # use simple voting to get voxel labels using stack and mode functions, convert to an image, copy atlas information
    atlas_segmentation = sitk.GetImageFromArray(stats.mode(np.stack(segmentations_np))[0][0, ...])
    atlas_segmentation.CopyInformation(atlas)
    return atlas_segmentation


@profile()
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
    # load all the images and masks right away, so we aren't slowed down by constant file IO
    data = [
        (sitk.Cast(read_image(img_fn, f"image {i}", args.silent), sitk.sitkFloat32), sitk.ReadImage(seg_fn))
        for i, (img_fn, seg_fn) in enumerate(zip(args.images, args.segmentations))
    ]
    # create the first atlas using affine registration
    atlas, transforms = create_initial_average_atlas(data, args)
    if args.write_intermediate_atlases:
        sitk.WriteImage(atlas, f"{output_base}_affine.nii")
    # iteratively update the atlas until convergence
    differences = []
    for i in range(args.atlas_iterations):
        prior_atlas = atlas
        atlas, transforms = update_average_atlas(atlas, data, transforms, args)
        differences.append(get_atlas_difference(atlas, prior_atlas))
        # apply successive over-relaxation
        atlas = sitk.Add(
            prior_atlas, sitk.Multiply(
                sitk.Subtract(atlas, prior_atlas),
                args.atlas_sor_alpha
            )
        )
        if differences[-1] < args.atlas_convergence_threshold:
            if not args.silent:
                message(f"Average atlas converged after {i+1} iterations.")
            break
        else:
            if not args.silent:
                message(f"Iteration {i} complete. Difference is {differences[-1]}")
            if args.write_intermediate_atlases:
                sitk.WriteImage(atlas, f"{output_base}_iteration_{i}.nii")
    else:
        if not args.silent:
            message(f"Average atlas did not converge after {args.atlas_iterations} iterations."
                    f"Final difference was {differences[-1]}, threshold was {args.atlas_convergence_threshold}.")
    # get the atlas segmentation
    atlas_segmentation = create_atlas_segmentation(atlas, data, transforms)
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
                    "using nearest neighbour interpolation, (9) use voting to generate the atlas segmentation, "
                    "(10) write the average-atlas and atlas segmentation to file. "
                    "The user is given all of of the necessary command line options to configure both the affine and "
                    "deformable registration parameters so that the method of atlas generation can be consistent with "
                    "the method of atlas-based segmentation using the atlas.",
        epilog="(1) DOI: 10.1109/MMBIA.2001.991733, (2) DOI: 10.1016/j.neuroimage.2003.11.010 ",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    # inputs and outputs
    parser.add_argument(
        "--images", "-img",
        type=create_file_extension_checker(INPUT_EXTENSIONS, "images"), nargs="+",
        metavar="IMAGES",
        help=f"Provide image filenames ({', '.join(INPUT_EXTENSIONS)}).",
        required=True
    )
    parser.add_argument(
        "--segmentations", "-seg",
        type=create_file_extension_checker(INPUT_EXTENSIONS, "segmentations"), nargs="+",
        metavar="SEGMENTATIONS",
        help=f"Provide image filenames ({', '.join(INPUT_EXTENSIONS)}).",
        required=True
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
        "--atlas-sor-alpha", "-sora", default=1.0, type=float, metavar="X",
        help="alpha value for successive over-relaxation (sor) of atlas update. must be >0. decrease to improve "
             "stability (but slow it down) or increase to speed up convergence (but risk instability).  "
    )
    parser.add_argument(
        "--atlas-convergence-threshold", "-act", default=1e-3, type=float, metavar="X",
        help="threshold for convergence of atlas updates"
    )
    parser.add_argument(
        "--write-intermediate-atlases", "-wia", default=False, action="store_true",
        help="enable this flag to write out the average atlas image at the end of each iteration"
    )
    # shared registration parameters
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
    # affine registration specs
    parser.add_argument(
        "--max-affine-iterations", "-mai", default=100, type=int, metavar="N",
        help="number of iterations to run registration algorithm for at each stage in the affine registration"
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
    # deformable registration specs
    parser.add_argument(
        "--max-demons-iterations", "-mdi", default=100, type=int, metavar="N",
        help="number of iterations to run registration algorithm for at each stage in the demons registration"
    )
    parser.add_argument(
        "--demons-type", "-dt", default="demons", type=demons_type_checker, metavar="STR",
        help=f"type of demons algorithm to use. options: {list(DEMONS_FILTERS.keys())}"
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
