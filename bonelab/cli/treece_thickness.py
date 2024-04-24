from __future__ import annotations

# IMPORTS
# external
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace, ArgumentTypeError
from typing import Callable, Tuple, Optional
import pyvista as pv
import numpy as np
import SimpleITK as sitk
from tqdm import tqdm, trange
from skimage.morphology import binary_erosion, binary_dilation
from matplotlib import pyplot as plt
from scipy.special import erf
from scipy.optimize import least_squares
from scipy.ndimage import gaussian_filter1d
from datetime import datetime
import os

# internal
from bonelab.util.registration_util import (
    create_file_extension_checker, read_image,
    check_inputs_exist, check_for_output_overwrite
)
from bonelab.util.echo_arguments import echo_arguments
from bonelab.util.time_stamp import message


# CONSTANTS
# define file extensions that we consider available for input images
INPUT_EXTENSIONS = [".nii", ".nii.gz"]


# FUNCTIONS
def create_treece_model(
    y1: float
) -> Callable[[np.ndarray, float, float, float, float, float], np.ndarray]:
    '''
    Create a model function for Treece' method.

    Parameters
    ----------
    y1 : float
        The density of the tissue between x0 and x1 (cortical bone).

    Returns
    -------
    Callable[[np.ndarray, float, float, float, float, float], np.ndarray]
        A function for Treece' model with y1 fixed.
    '''

    sqrt_of_two = np.sqrt(2)

    def model(
        x: np.ndarray,
        x0: float,
        t: float,
        y0: float,
        y2: float,
        sigma: float
    ) -> np.ndarray:
        '''
        A model that predicts the intensity at a given location on a parameterized line normal to
        the cortical surface based on a function with two step functions and some blurring.

        Parameters
        ----------
        x : np.ndarray
            The locations along the parameterized line where the intensities are measured.

        x0 : float
            The middle of the cortical bone.

        t : float
            The thickness of the cortical bone.

        y0 : float
            The density outside the cortical bone (soft tissue).

        y2 : float
            The density past the cortical bone (marrow and trabecular bone).

        sigma : float
            The standard deviation of the Gaussian blur approximating in-plane partial volume effects
            and other blurring effects from the measurement system.

        Returns
        -------
        np.ndarray
            The predicted intensities at the locations x.
        '''
        term1 = ((y1 - y0) / 2) * (1 + erf((x - x0 + t/2) / (sigma * sqrt_of_two)))
        term2 = ((y2 - y1) / 2) * (1 + erf((x - x0 - t/2) / (sigma * sqrt_of_two)))

        return y0 + term1 + term2

    return model



def create_treece_residual_function(
    model: Callable[[np.ndarray, float, float, float, float, float], np.ndarray],
    intensities: np.ndarray,
    x: np.ndarray,
    residual_boost_factor: float = 2.0
) -> Callable[[Tuple[float, float, float, float, float]], np.ndarray]:
    '''
    Create a residual function for Treece' method to fit the model using least squares.

    Parameters
    ----------
    model : Callable[[np.ndarray, float, float, float, float, float], float]
        The model function to fit.

    intensities: np.ndarray
        The measured intensities at the locations x.

    x : np.ndarray
        The locations along the parameterized line where the intensities were measured.

    Returns
    -------
    Callable[[Tuple[float, float, float, float, float]], np.ndarray]
        A function that computes the residuals between the model and the measured intensities.
    '''
    distance_from_middle = np.abs(x) - np.abs(x).min()
    distance_from_middle = 1 - (distance_from_middle / distance_from_middle.max())
    mult = residual_boost_factor * distance_from_middle

    def residual_function(args: Tuple[float, float, float, float, float]) -> np.ndarray:
        '''
        Compute the residuals between the model and the measured intensities.

        Parameters
        ----------
        args : Tuple[float, float, float, float, float]
            The parameters to fit the model: x0, x1, y0, y2, sigma.

        Returns
        -------
        np.ndarray
            The residuals between the modelled and the sampled intensities.
        '''
        modelled_intensities = model(x, *args)
        return mult * (modelled_intensities - intensities)

    return residual_function


def treece_fit(
    intensities: np.ndarray,
    x: np.ndarray,
    normal: np.ndarray,
    dx: float,
    y1: Optional[float],
    residual_boost_factor: float,
    t_initial_guess: Optional[float],
    y0_initial_guess: float,
    y2_initial_guess: float,
    sigma_initial_guess: float,
    t_bounds: Optional[Tuple[float, float]],
    y0_bounds: Tuple[float, float],
    y2_bounds: Tuple[float, float],
    sigma_bounds: Tuple[float, float]
) -> Tuple[float, float, np.ndarray]:
    '''
    Fit the Treece' model to the measured intensities and normal and return the location
    where the cortical bone starts and ends.

    Parameters
    ----------
    intensities : np.ndarray
        The measured intensities at the locations x.

    x : np.ndarray
        The locations along the parameterized line where the intensities were measured.

    normal : np.ndarray
        The normal vector to the cortical surface at the locations x.

    dx : float
        The spacing between values in x (spatial resolution of the discrete parameterized line).

    y1 : Optional[float]
        The density of the tissue between x0 and x1 (cortical bone).

    residual_boost_factor : float
        A factor to boost the residuals near the start of the line to make the model fit better
        to the first peak which will correspond to the cortical bone and less likely to be
        influenced by subsequent peaks, which will correspond to trabecular bone in high-res images.

    t_initial_guess : Optional[float]
        The initial guess for the thickness of the cortical bone.

    y0_initial_guess : float
        The initial guess for the density outside the cortical bone (soft tissue).

    y2_initial_guess : float
        The initial guess for the density past the cortical bone (marrow and trabecular bone).

    sigma_initial_guess : float
        The initial guess for the standard deviation of the Gaussian blur approximating in-plane
        partial volume effects and other blurring effects from the measurement system.

    t_bounds : Optional[Tuple[float, float]]
        The bounds for the thickness of the cortical bone.

    y0_bounds : Tuple[float, float]
        The bounds for the density outside the cortical bone (soft tissue).

    y2_bounds : Tuple[float, float]
        The bounds for the density past the cortical bone (marrow and trabecular bone).

    sigma_bounds : Tuple[float, float]
        The bounds for the standard deviation of the Gaussian blur approximating in-plane
        partial volume effects and other blurring effects from the measurement system.

    Returns
    -------
    Tuple[float, float, np.ndarray]
        The distance along the line where the cortical bone starts and ends,
        and the modelled intensities for debug purposes.
    '''

    if y1 is None:
        y1 = intensities.max()

    if t_bounds is None:
        t_bounds = (dx, x.max() - x.min())

    lower_bounds = [
        x.min(), t_bounds[0],
        y0_bounds[0], y2_bounds[0], sigma_bounds[0]
    ]

    upper_bounds = [
        x.max(), t_bounds[1],
        y0_bounds[1], y2_bounds[1], sigma_bounds[1]
    ]

    if t_initial_guess is None:
        t_initial_guess = ( t_bounds[0] + t_bounds[1] ) / 2

    initial_guess = [
        0, # we always guess '0' for the x0 parameter because this is where the mask placed the surface
        t_initial_guess,
        y0_initial_guess,
        y2_initial_guess,
        sigma_initial_guess
    ]

    model = create_treece_model(y1)
    residual_function = create_treece_residual_function(model, intensities, x, residual_boost_factor)

    result = least_squares(
        residual_function,
        x0=initial_guess,
        bounds=(lower_bounds, upper_bounds),
        method="trf"
    )
    return result.x[0], result.x[1], model(x, *result.x)


def compute_boundary_mask(mask: np.ndarray) -> np.ndarray:
    '''
    Compute a mask of the boundary of the input mask.

    Parameters
    ----------
    mask : np.ndarray
        The input mask.

    Returns
    -------
    np.ndarray
        The mask of the boundary of the input mask.
    '''
    eroded_mask = binary_erosion(mask, selem=np.ones((3,3,3)))
    return mask - eroded_mask


def sample_intensity_profile(
    image: pv.UniformGrid,
    point: np.ndarray,
    normal: np.ndarray,
    outside_dist: float,
    inside_dist: float,
    dx: float
) -> Tuple[np.ndarray, np.ndarray]:
    '''
    Sample an intensity profile along a line in the image.

    Parameters
    ----------
    image : pv.UniformGrid
        The image to sample from.

    point : np.ndarray
        The starting point of the line.

    normal : np.ndarray
        The normal vector for the line.

    outside_dist : float
        The distance to start sampling from outside the point along the normal.

    inside_dist : float
        The distance to sample up to inside the point along the normal.

    dx : float
        The spacing between sample points.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        The sampled intensities and the x values of the sample points.
    '''
    normal = normal / np.sqrt((normal**2).sum())
    x = np.arange(-outside_dist, inside_dist, dx)
    sample_points = pv.PolyData(point[np.newaxis,:] + x[:,np.newaxis]*normal[np.newaxis,:])
    sample_points = sample_points.sample(image)
    return np.array(sample_points["NIFTI"]), x


def dilate_mask(mask: pv.UniformGrid, dilate_amount: Tuple[int, int, int]) -> pv.UniformGrid:
    '''
    Dilate the mask.

    Parameters
    ----------
    mask : pv.UniformGrid
        The mask to dilate.

    dilate_amount : Tuple[int, int, int]
        The amount to dilate the mask by in each dimension.

    Returns
    -------
    pv.UniformGrid
        The dilated mask.
    '''
    '''
    mask[mask.active_scalars_name] = binary_dilation(
        binary_dilation(
            binary_dilation(
                mask[mask.active_scalars_name].reshape(mask.dimensions, order="F"), np.ones((dilate_amount[0],1,1))
            ), np.ones((1,dilate_amount[1],1))
        ), np.ones((1,1,dilate_amount[2]))
    ).flatten(order="F")
    '''
    mask_np = mask[mask.active_scalars_name].reshape(mask.dimensions, order="F")
    for i, d in enumerate(dilate_amount):
        dilation_shape = [1, 1, 1]
        dilation_shape[i] = 2 * d + 1
        dilation_shape = tuple(dilation_shape)
        mask_np = binary_dilation(mask_np, selem=np.ones(dilation_shape))
    mask[mask.active_scalars_name] = mask_np.flatten(order="F")
    return mask


def debug_surface_viz(surface: pv.PolyData) -> None:
    '''
    Visualize the surface with normals as arrows.

    Parameters
    ----------
    surface : pv.PolyData
        The surface to visualize.

    Returns
    -------
    None
    '''
    arrows = surface.glyph(orient="Normals", scale="Normals", tolerance=0.02)
    pl = pv.Plotter()
    pl.subplot(0,0)
    pl.add_mesh(surface, scalars="use_point", opacity=0.1)
    pl.add_mesh(arrows, color="black")
    pl.show()


def sample_all_intensity_profiles(
    image: pv.UniformGrid,
    points: np.ndarray,
    normals: np.ndarray,
    outside_dist: float,
    inside_dist: float,
    dx: float,
    constrain_normal_to_plane: Optional[int],
    silent: bool
):
    '''
    Sample intensity profiles along lines in the image.

    Parameters
    ----------
    image : pv.UniformGrid
        The image to sample from.

    points : np.ndarray
        The starting points of the lines.

    normals : np.ndarray
        The normal vectors for the lines.

    outside_dist : float
        The distance to start sampling from outside the points along the normals.

    inside_dist : float
        The distance to sample up to inside the points along the normals.

    dx : float
        The spacing between sample points.

    constrain_normal_to_plane : Optional[int]
        The index of the axis to constrain the normal vectors to. If None, no constraint is applied.

    silent : bool
        Set this flag to not show the progress bar.

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        The sampled intensities and the x values of the sample points.
    '''
    if constrain_normal_to_plane:
        normals[:,constrain_normal_to_plane] = 0
    normals = normals / (np.sqrt((normals**2).sum(axis=-1))[:,np.newaxis] + 1e-6)
    x = np.arange(-outside_dist, inside_dist, dx)
    nx = x.shape[0]
    x = np.tile(x, points.shape[0])
    points = np.repeat(points, nx, axis=0)
    normals = np.repeat(normals, nx, axis=0)
    sample_points = pv.PolyData(points + x[:,np.newaxis]*normals)
    sample_points = sample_points.sample(image, progress_bar=~silent)
    intensities = np.array(sample_points["NIFTI"]).reshape(-1, nx)
    return intensities, x[:nx]


def median_smooth_polydata(pd: pv.PolyData, scalar: str, flag_scalar: str, silent: bool) -> pv.PolyData:
    '''
    Smooth the scalar values of a PolyData object using a median filter.

    Parameters
    ----------
    pd : pv.PolyData
        The PolyData object to smooth.

    scalar : str
        The name of the scalar to smooth.

    flag_scalar : str
        The name of the flag scalar that determines if the point is used.

    silent : bool

    Returns
    -------
    pv.PolyData
        The smoothed PolyData object.
    '''
    neighbours = {}
    for i in trange(pd.n_points, disable=silent):
        neighbours[i] = []
    for i in trange(pd.n_cells, disable=silent):
        cell_ids = pd.get_cell(i).point_ids
        for j in cell_ids:
            neighbours[j].extend(cell_ids)
    for i in trange(pd.n_points, disable=silent):
        neighbours[i] = list(set(neighbours[i]))
    out = pd.copy()
    for i in tqdm(np.where(pd[flag_scalar] == 1)[0], disable=silent):
        flag = pd[flag_scalar][neighbours[i]] * (pd[scalar][neighbours[i]] > 0)
        vals = pd[scalar][neighbours[i]]
        out[scalar][i] = np.median(vals[flag==1])
    return out



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
        surface["use_point"] = np.ones(surface.n_points)
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
    if args.debug_check_model_fit:
        debug_surface_viz(surface)
    if ~args.silent:
        message("Computing the cortical thickness at each surface point...")
    use_indices = np.where(surface["use_point"] == 1)[0]
    surface.point_data["thickness"] = np.zeros((surface.n_points,))
    surface.point_data["cort_center"] = np.zeros((surface.n_points,))
    if ~args.silent:
        message("Computing all of the intensity profiles in parallel...")
    intensity_profiles, x = sample_all_intensity_profiles(
        image,
        surface.points[use_indices,:],
        surface.point_data["Normals"][use_indices,:],
        args.sample_outside_distance,
        args.sample_inside_distance,
        dx,
        args.constrain_normal_to_plane,
        args.silent
    )
    for j, i in enumerate(tqdm(use_indices, disable=args.silent)):
        # j is the index into the intensities array
        # i is the index into the surface points and normals
        if args.plot_model_fit_for_point:
            i = args.plot_model_fit_for_point
        normal = surface.point_data["Normals"][i,:]
        if args.constrain_normal_to_plane:
            normal[args.constrain_normal_to_plane] = 0
        intensities = gaussian_filter1d(
            intensity_profiles[j], sigma=args.intensity_smoothing_sigma
        )
        x0, t, model_intensities = treece_fit(
            intensities,
            x,
            normal,
            dx,
            args.cortical_density,
            args.residual_boost_factor,
            args.thickness_initial_guess,
            args.soft_tissue_intensity_initial_guess,
            args.trabecular_bone_intensity_initial_guess,
            args.model_sigma_initial_guess,
            args.thickness_bounds,
            args.soft_tissue_intensity_bounds,
            args.trabecular_bone_intensity_bounds,
            args.model_sigma_bounds,
        )
        surface["thickness"][i] = t
        surface["cort_center"][i] = x0

        if args.debug_check_model_fit or args.plot_model_fit_for_point:
            point = surface.extract_points([i], include_cells=False)
            if args.constrain_normal_to_plane:
                point["Normals"][:,args.constrain_normal_to_plane] = 0
            print(f"point: ", surface.points[i,:])
            print(normal)
            plt.figure()
            plt.plot(x, intensities, "k-")
            plt.plot(x, model_intensities, "r--")
            plt.axvline(x0, color="black", linestyle="-")
            plt.axvline(x0 - t/2, color="black", linestyle="--")
            plt.axvline(x0 + t/2, color="black", linestyle="--")
            plt.title(f"x0: {x0}, t: {t}")
            plt.xlim([x.min(), x.max()])
            plt.xlabel("x")
            plt.ylabel("intensity")
            plt.show(block=False)
            pl = pv.Plotter()
            pl.add_mesh(
                image.slice_orthogonal(
                    max(surface.points[i,0], dx),
                    max(surface.points[i,1], dx),
                    max(surface.points[i,2], dx)
                ),
                cmap="gist_gray"
            )
            pl.add_mesh(
                point.glyph(orient="Normals", scale="Normals"),
                color="black"
            )
            pl.add_axes()
            pl.show()
            plt.show()

            if args.plot_model_fit_for_point:
                break

            response = input("Continue? [`y` to continue, anything else to quit] ")
            if response != "y":
                break

    if args.median_smooth_thicknesses:
        if ~args.silent:
            message("Smoothing the thickness using a median filter...")
        surface = median_smooth_polydata(surface, "thickness", "use_point", args.silent)

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
        "--constrain-normal-to-plane", "-cnxy", type=int, default=None,
        help="Set this to 0, 1, or 2 to zero out the normal in the given direction. For radius and "
             "tibia images you probably should zero out the normal in axis 2 (axial direction)."
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
        "--debug-check-model-fit", "-dcmf", default=False, action="store_true",
        help="enable this flag to plot the model fit for one surface point, for debugging purposes"
    )
    parser.add_argument(
        "--debug-on-problem", "-dop", default=False, action="store_true",
        help="enable this flag to plot the model fit for one surface point, for debugging purposes, if there is a flagged problem"
    )
    parser.add_argument(
        "--plot-model-fit-for-point", "-pmfv", type=int, default=None,
        help="plot the model fit for the point at the given index, for debugging purposes"
    )

    return parser


def main():
    args = create_parser().parse_args()
    treece_thickness(args)


if __name__ == "__main__":
    main()
