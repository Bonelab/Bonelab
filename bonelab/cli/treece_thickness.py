from __future__ import annotations

# IMPORTS
# external
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace, ArgumentTypeError
import numpy as np
import pyvista as pv
from datetime import datetime
import os
import sys

# internal
from bonelab.util.registration_util import (
    create_file_extension_checker, read_image,
    check_inputs_exist, check_for_output_overwrite
)
from bonelab.util.echo_arguments import echo_arguments
from bonelab.util.time_stamp import message
from bonelab.util.cortical_thickness.LocalTreeceMinimization import LocalTreeceMinimization
from bonelab.util.cortical_thickness.GlobalControlPointTreeceMinimization import GlobalControlPointTreeceMinimization
from bonelab.util.cortical_thickness.GlobalRegularizationTreeceMinimization import GlobalRegularizationTreeceMinimization
from bonelab.util.cortical_thickness.ctth_util import (
    dilate_mask, binary_dilation, sample_all_intensity_profiles,
    median_smooth_polydata
)


# CONSTANTS
# define file extensions that we consider available for input images
INPUT_EXTENSIONS = [".nii", ".nii.gz"]


def treece_thickness(args: Namespace) -> None:
    '''
    Compute the cortical thickness using the Treece' model.

    Parameters
    ----------
    args : Namespace
        The parsed command line arguments.
    '''
    echoed_args = echo_arguments("Treece Thickness", vars(args))
    print(echoed_args)
    input_fns = args.bone_masks + [args.image]
    if args.sub_mask:
        input_fns.append(args.sub_mask)
    check_inputs_exist(input_fns, args.silent)
    output_surface = f"{args.output_base}.vtk"
    output_log = f"{args.output_base}.log"
    check_for_output_overwrite([output_surface, output_log], args.overwrite, args.silent)
    if args.constrain_normal_to_plane and args.constraint_normal_to_axis:
        raise ValueError("Cannot constrain the normal to both a plane and an axis.")
    if ~args.silent:
        message("Reading in the image...")
    image = pv.read(args.image)
    if ~args.silent:
        message("Determining the line resolution, if not given...")
    dx = args.line_resolution if args.line_resolution else min(image.spacing) / 10
    if ~args.silent:
        message("Reading in the bone masks...")
    bone_mask = image.copy()
    bone_mask["NIFTI"][:] = 0
    for fn in args.bone_masks:
        bone_mask["NIFTI"] += pv.read(fn)["NIFTI"]
    bone_mask["NIFTI"] = (bone_mask["NIFTI"] > 0).astype(int)
    if args.sub_mask:
        if ~args.silent:
            message("Reading in the sub-mask...")
        sub_mask = pv.read(args.sub_mask)
        if args.sub_mask_label:
            sub_mask["NIFTI"] = (sub_mask["NIFTI"] == args.sub_mask_label).astype(int)
        else:
            sub_mask["NIFTI"] = (sub_mask["NIFTI"] > 0).astype(int)
    else:
        if ~args.silent:
            message("No sub-mask provided. Proceeding without it...")
        sub_mask = None
    if sub_mask:
        if ~args.silent:
            message("Dilating the sub mask...")
        sub_mask = dilate_mask(sub_mask, args.sub_mask_dilation)
        bone_mask["use_point"] = sub_mask["NIFTI"]
    else:
        bone_mask["use_point"] = np.ones_like(bone_mask["NIFTI"])
    if ~args.silent:
        message("Computing the surface of the bone mask...")
    surface = bone_mask.contour([1], progress_bar=~args.silent)
    if args.smooth_surface:
        if ~args.silent:
            message("Smoothing the surface...")
        surface = surface.smooth_taubin(
            n_iter=args.surface_smoothing_iterations,
            pass_band=args.surface_smoothing_passband,
            progress_bar=~args.silent
        )
    else:
        if ~args.silent:
            message("Not smoothing the surface...")
    if ~args.silent:
        message("Computing the normals...")
    surface = surface.compute_normals(
        auto_orient_normals=True,
        flip_normals=True,
        progress_bar=~args.silent
    )
    if args.constrain_normal_to_plane:
        surface.point_data["Normals"][:,constrain_normal_to_plane] = 0
    elif args.constrain_normal_to_axis:
        surface.point_data["Normals"][:,:] = 0
        surface.point_data["Normals"][:,constrain_normal_to_axis] = np.sign(constrain_normal_to_axis)
    surface.point_data["Normals"] = (
        surface.point_data["Normals"]
        / (
            np.sqrt(
                (surface.point_data["Normals"]**2).sum(axis=-1)
            )[:,np.newaxis]
            + 1e-6
        )
    )

    if ~args.silent:
        message("Computing all of the intensity profiles in parallel...")
    use_indices = np.where(surface["use_point"] == 1)[0]
    intensity_profiles, x = sample_all_intensity_profiles(
        image,
        surface.points[use_indices,:],
        surface.point_data["Normals"][use_indices,:],
        args.sample_outside_distance,
        args.sample_inside_distance,
        dx,
        args.constrain_normal_to_plane,
        args.constraint_normal_to_axis,
        args.silent
    )
    surface.point_data["thickness"] = np.zeros((surface.n_points,))
    surface.point_data["cort_center"] = np.zeros((surface.n_points,))

    # here is where we check the mode and then create a minimization object and fit the model
    if args.mode == "local":
        minimization = LocalTreeceMinimization(
           args.cortical_density,
           intensity_profiles,
           x,
           args.residual_boost_factor,
           args.thickness_initial_guess,
           args.soft_tissue_intensity_initial_guess,
           args.trabecular_bone_intensity_initial_guess,
           args.model_sigma_initial_guess,
           args.thickness_bounds,
           args.soft_tissue_intensity_bounds,
           args.trabecular_bone_intensity_bounds,
           args.model_sigma_bounds,
           args.silent,
           args.max_iterations,
           args.function_tolerance,
           args.gradient_tolerance
        )
    elif args.mode == "global-interpolation":
        minimization = GlobalControlPointTreeceMinimization(
            surface.points[use_indices,:],
            args.control_point_separations,
            args.neighbours,
            args.cortical_density,
            intensity_profiles,
            x,
            args.residual_boost_factor,
            args.thickness_initial_guess,
            args.soft_tissue_intensity_initial_guess,
            args.trabecular_bone_intensity_initial_guess,
            args.model_sigma_initial_guess,
            args.thickness_bounds,
            args.soft_tissue_intensity_bounds,
            args.trabecular_bone_intensity_bounds,
            args.model_sigma_bounds,
            args.silent,
            args.max_iterations,
            args.function_tolerance,
            args.gradient_tolerance
        )
    elif args.mode == "global-regularization":
        minimization = GlobalRegularizationTreeceMinimization(
            surface.points[use_indices,:],
            args.neighbours,
            args.sigma_regularization,
            args.lambda_regularization,
            args.cortical_density,
            intensity_profiles,
            x,
            args.residual_boost_factor,
            args.thickness_initial_guess,
            args.soft_tissue_intensity_initial_guess,
            args.trabecular_bone_intensity_initial_guess,
            args.model_sigma_initial_guess,
            args.thickness_bounds,
            args.soft_tissue_intensity_bounds,
            args.trabecular_bone_intensity_bounds,
            args.model_sigma_bounds,
            args.silent,
            args.max_iterations,
            args.function_tolerance,
            args.gradient_tolerance
        )
    else:
        raise ValueError(
            f"Unrecognized mode: {args.mode}. "
            f"Must be one of: 'local', 'global-interpolation', 'global-regularization'"
        )
    parameters = minimization.fit()
    surface.point_data["thickness"][use_indices] = parameters[1]
    surface.point_data["cort_center"][use_indices] = parameters[0]

    if args.median_smooth_thicknesses:
        if ~args.silent:
            message("Smoothing the thickness using a median filter...")
        surface = median_smooth_polydata(surface, "thickness", "use_point", silent=args.silent)

    if ~args.silent:
        message("Writing the cortical thickness surface to disk...")
    surface.save(output_surface)

    if ~args.silent:
        message("Calculate mean and standard deviation of thickness...")
    thickness = surface["thickness"][surface["use_point"] == 1]
    mean_thickness = np.mean(thickness[thickness>0])
    std_thickness = np.std(thickness[thickness>0])

    if ~args.silent:
        message("Writing log file...")

    with open(output_log, "w") as f:
        f.write(echoed_args)
        f.write(f"Date and time: {datetime.now()}\n")
        f.write("-"*30 + "\n")
        f.write(f"Mean Thickness: {mean_thickness}\n")
        f.write(f"Standard Deviation of Thickness: {std_thickness}\n")
        f.write("-"*30 + "\n")

    if ~args.silent:
        message("Done.")



def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Use a modified version of Treece' method (doi:10.1016/j.media.2010.01.003) to compute "
                    "a cortical thickness map from an image, a bone mask, and an optional sub-mask."
                    "The output will be a *.vtk polydata file and a *.log file. The polydata can be used to "
                    "visualize or continue processing the cortical thicknesses. The log file will contain "
                    "the mean and standard deviation of the thicknesses (for the points where the model "
                    " could be fit to the data properly) as well as debug information for points where the "
                    "model failed to fit properly.",
        formatter_class=ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "image", type=create_file_extension_checker(INPUT_EXTENSIONS, "image"), metavar="IMAGE",
        help=f"Provide image input filename ({', '.join(INPUT_EXTENSIONS)})"
    )
    parser.add_argument(
        "output_base", type=str, metavar="OUTPUT",
        help=f"Provide base for outputs, you will get a file `output`.vtk and `output`.log"
    )
    parser.add_argument(
        "--bone_masks", "-bm", type=create_file_extension_checker(INPUT_EXTENSIONS, "bone mask"),
        nargs="+", required=True, metavar="BONE_MASK",
        help=f"Provide bone mask input filename(s) ({', '.join(INPUT_EXTENSIONS)})."
             f"You can provice multiple because the whole bone mask may be split into "
             f"multiple masks (e.g. cort, trab)"
    )
    parser.add_argument(
        "--sub-mask", "-sm", type=create_file_extension_checker(INPUT_EXTENSIONS, "sub-mask"), default=None, metavar="SUB_MASK",
        help=f"Provide optional sub-mask input filename ({', '.join(INPUT_EXTENSIONS)})"
    )
    parser.add_argument(
        "--sub-mask-label", "-sml", type=int, default=None,
        help="Label of the sub-mask to use, if not provided then the sub mask will be binarized (>0 -> 1)."
    )
    parser.add_argument(
        "--sub-mask-dilation", "-smd", type=int, nargs=3, default=[1, 1, 1],
        help="Dilation of the sub-mask in x, y, and z directions."
    )
    parser.add_argument(
        "--smooth-surface", "-ss",  default=False, action="store_true",
        help="enable this flag to smooth the bone surface before computing the normals"
    )
    parser.add_argument(
        "--surface-smoothing-iterations", "-ssi", type=int, default=15,
        help="number of iterations for the Taubin surface smoothing"
    )
    parser.add_argument(
        "--surface-smoothing-passband", "-ssp", type=float, default=0.1,
        help="passband for the Taubin surface smoothing"
    )
    parser.add_argument(
        "--intensity-smoothing-sigma", "-iss", type=float, default=1.0,
        help="sigma for the Gaussian smoothing of the intensity profile"
    )
    parser.add_argument(
        "--cortical-density", "-cd", type=float, default=None,
        help="prescribed cortical density, in the units of the image, for the model. If left as None, "
             "the cortical density for each point will be calculated as the maximum value sampled on the line."
    )
    parser.add_argument(
        "--line-resolution", "-lr", type=float, default=None,
        help="resolution of the line in the Treece' algorithm, in physical spatial units of the image."
             "If not provided, will default to 1/10 the smallest voxel size"
    )
    parser.add_argument(
        "--residual-boost-factor", "-rbf", type=float, default=3.0,
        help="boost factor for the residuals near the start of the line in the Treece' algorithm"
    )
    parser.add_argument(
        "--sample-outside-distance", "-sod", type=float, default=3,
        help="distance outside the boundary to sample the intensities for the Treece' algorithm"
    )
    parser.add_argument(
        "--sample-inside-distance", "-sid", type=float, default=8,
        help="distance inside the boundary to sample the intensities for the Treece' algorithm"
    )
    parser.add_argument(
        "--thickness-initial-guess", "-tig", type=float, default=None,
        help="initial guess for the thickness of the cortical bone in the model. If not provided, "
             "will be set to the middle of the thickness bounds"
    )
    parser.add_argument(
        "--soft-tissue-intensity-initial-guess", "-stig", type=float, default=0,
        help="initial guess for the intensity of soft tissue in the model"
    )
    parser.add_argument(
        "--soft-tissue-intensity-bounds", "-stb", type=float, nargs=2, default=[-200, 400],
        help="bounds for the intensity of soft tissue in the model"
    )
    parser.add_argument(
        "--trabecular-bone-intensity-initial-guess", "-tbig", type=float, default=200,
        help="initial guess for the intensity of trabecular bone in the model"
    )
    parser.add_argument(
        "--trabecular-bone-intensity-bounds", "-tbb", type=float, nargs=2, default=[-200, 400],
        help="bounds for the intensity of trabecular bone in the model"
    )
    parser.add_argument(
        "--thickness-bounds", "-tb", type=float, nargs=2, default=None,
        help="bounds for the cortical thickness in the model, if not set then "
             "then the bounds will be from the line resolution to the line length"
    )
    parser.add_argument(
        "--model-sigma-initial-guess", "-msig", type=float, default=1,
        help="initial guess for the sigma of inplane blurring in the model"
    )
    parser.add_argument(
        "--model-sigma-bounds", "-msb", type=float, nargs=2, default=[0.1, 100],
        help="bounds for the sigma of inplane blurring in the model"
    )

    parser.add_argument(
        "--constrain-normal-to-plane", "-cnp", type=int, default=None,
        help="Set this to 0, 1, or 2 to zero out the normal in the given direction. For radius and "
             "tibia images you probably should zero out the normal in axis 2 (axial direction)."
    )
    parser.add_argument(
        "--constrain-normal-to-axis", "-cna", type=int, default=None,
        help=(
            "Set this to +/- 0, 1, or 2 to constrain the normal to the given axis. "
            "Positive numbers will use a positive normal, negative numbers will use a negative normal. "
        )
    )
    parser.add_argument(
        "--median-smooth-thicknesses", "-mst", default=False, action="store_true",
        help="enable this flag to median smooth the thicknesses at the end of the algorithm"
    )

    parser.add_argument(
        "--overwrite", "-ow", default=False, action="store_true",
        help="enable this flag to overwrite existing files, if they exist at output targets"
    )
    parser.add_argument(
        "--silent", "-s", default=False, action="store_true",
        help="enable this flag to suppress terminal output"
    )
    parser.add_argument(
        "--mode", "-m", default="local", choices=["local", "global-interpolation", "global-regularization"],
        help=(
            "mode of the algorithm. 'local' fits the model to each surface point individually. "
            "'global-interpolation' fits the model to the entire surface using control points "
            "and nearest neighbour Gaussian distance weighted interpolation. "
            "'global-regularization' fits the model to the entire surface using a spatial "
            "regularization term added to the minimization problem."
        )
    )
    parser.add_argument(
        "--control-point-separations", "-cps", type=float, default=[5], nargs="+",
        help="separation of control points at each stage of the global "
             "hierarchical global model fitting"
    )
    parser.add_argument(
        "--neighbours", "-n", type=int, default=10,
        help="number of neighbours to use for the inverse distance weighting interpolation"
    )
    parser.add_argument(
        "--lambda-regularization", "-l", type=float, default=0.1,
        help="lambda parameter for the regularization term in the global-regularization mode"
    )
    parser.add_argument(
        "--sigma-regularization", "-sr", type=float, default=3.0,
        help="sigma parameter for the regularization term in the global-regularization mode"
    )
    parser.add_argument(
        "--max-iterations", "-mi", type=int, default=400,
        help="maximum number of iterations for the optimization algorithm"
    )
    parser.add_argument(
        "--function-tolerance", "-ft", type=float, default=1e-6,
        help="function tolerance for the optimization algorithm"
    )
    parser.add_argument(
        "--gradient-tolerance", "-gt", type=float, default=1e-6,
        help="gradient tolerance for the optimization algorithm"
    )
    parser.add_argument(
        "--control-point-rbf-splines", "-cprbf", default=False, action="store_true",
        help=(
            "enable this flag to use RBF splines as the final interpolation step "
            "between stages and at the end in the global-regularization mode."
        )
    )

    return parser


def main():
    args = create_parser().parse_args()
    treece_thickness(args)


if __name__ == "__main__":
    main()
