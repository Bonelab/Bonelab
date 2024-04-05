from __future__ import annotations

# IMPORTS
# external
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace, ArgumentTypeError
from typing import Callable, Tuple
import pyvista as pv
import numpy as np
import SimpleITK as sitk
from tqdm import tqdm
from skimage.morphology import binary_erosion, binary_dilation
from matplotlib import pyplot as plt
from scipy.optimize import least_squares
from datetime import datetime

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
def indefinite_integral(x: np.ndarray, dx: float) -> np.ndarray:
    '''
    Compute the indefinite integral of x with respect to dx.

    Parameters
    ----------
    x : np.ndarray
        The function to integrate.

    dx : float
        The spacing between values in x.

    Returns
    -------
    np.ndarray
        The indefinite integral of x with respect to dx.
    '''
    return np.cumsum(x) * dx

def create_treece_model(
    y1: float, r: float, dx: float
) -> Callable[[np.ndarray, float, float, float, float, float], np.ndarray]:
    '''
    Create a model function for Treece' method.

    Parameters
    ----------
    y1 : float
        The density of the tissue between x0 and x1 (cortical bone).

    r : float
        Half of the value of the out-of-plane blur effect caused by the misalignment
        of the cortical surface and the slice orientation.

    dx : float
        The spacing between values in x (spatial resolution of the discrete parameterized line).

    Returns
    -------
    Callable[[np.ndarray, float, float, float, float, float], float]
        A function for Treece' model with y1 and r fixed.
    '''
    sqrtpi = np.sqrt(np.pi)

    def model(x: np.ndarray, x0: float, x1: float, y0: float, y2: float, sigma: float) -> np.ndarray:
        '''
        A model that predicts the intensity at a given location on a parameterized line normal to
        the cortical surface based on a function with two step functions and some blurring.

        Parameters
        ----------
        x : np.ndarray
            The locations along the parameterized line where the intensities are measured.

        x0 : float
            The location of the first step function.

        x1 : float
            The location of the second step function.

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
        integrand = (
            (y1 - y0) / (2*r*sigma*sqrtpi) * (
                np.exp(-(x+r-x0)**2/(sigma**2)) - np.exp(-(x-r-x0)**2/(sigma**2))
            )
            + (y2 - y1) / (2*r*sigma*sqrtpi) * (
                np.exp(-(x+r-x1)**2/(sigma**2)) - np.exp(-(x-r-x1)**2/(sigma**2))
            )
        )
        return y0 + indefinite_integral(indefinite_integral(integrand, dx), dx)

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
    def residual_function(args: Tuple[float, float, float, float, float]) -> np.ndarray:
        '''
        Compute the residuals between the model and the measured intensities.
        '''
        modelled_intensities = model(x, *args)
        mult = np.linspace(residual_boost_factor, 1, len(x))
        return mult * (modelled_intensities - intensities)

    return residual_function


def treece_fit(
    intensities: np.ndarray,
    x: np.ndarray,
    normal: np.ndarray,
    dx: float,
    y1: float,
    residual_boost_factor: float,
    slice_thickness: float,
    cortical_threshold: float,
    y0_initial_guess: float,
    y2_initial_guess: float,
    sigma_initial_guess: float,

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

    y1 : float
        The density of the tissue between x0 and x1 (cortical bone).

    residual_boost_factor : float
        A factor to boost the residuals near the start of the line to make the model fit better
        to the first peak which will correspond to the cortical bone and less likely to be
        influenced by subsequent peaks, which will correspond to trabecular bone in high-res images.

    slice_thickness : float
        The thickness of the slice in the direction of the normal.

    cortical_threshold : float
        The threshold to determine the initial guess for the start of the cortical bone.

    y0_initial_guess : float
        The initial guess for the density outside the cortical bone (soft tissue).

    y2_initial_guess : float
        The initial guess for the density past the cortical bone (marrow and trabecular bone).

    sigma_initial_guess : float
        The initial guess for the standard deviation of the Gaussian blur approximating in-plane
        partial volume effects and other blurring effects from the measurement system.

    Returns
    -------
    Tuple[float, float, np.ndarray]
        The distance along the line where the cortical bone starts and ends,
        and the modelled intensities for debug purposes.
    '''
    r = (
        (slice_thickness / 2)
        * np.abs(normal[2])
        / np.sqrt(normal[0]**2 + normal[1]**2)
    )

    x0 = [
        x[list(intensities > cortical_threshold).index(True)],
        x[list(intensities > cortical_threshold).index(True) + 10],
        y0_initial_guess,
        y2_initial_guess,
        sigma_initial_guess
    ]

    model = create_treece_model(y1, r, dx)
    residual_function = create_treece_residual_function(model, intensities, x, residual_boost_factor)

    result = least_squares(residual_function, x0=x0, method="lm")
    return result.x[0], result.x[1], model(x, *result.x)


def compute_boundary_mask(mask: np.ndarray) -> np.ndarray:
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
    normal = normal / np.sqrt((normal**2).sum())
    x = np.arange(-outside_dist, inside_dist, dx)
    sample_points = pv.PolyData(point[np.newaxis,:] + x[:,np.newaxis]*normal[np.newaxis,:])
    sample_points = sample_points.sample(image)
    return np.array(sample_points["NIFTI"]), x


def treece_thickness(args: Namespace):
    echoed_args = echo_arguments("Treece Thickness", vars(args))
    print(echoed_args)
    input_fns = [args.bone_mask, args.image]
    if args.sub_mask:
        input_fns.append(args.sub_mask)
    check_inputs_exist(input_fns, args.silent)
    output_image = f"{args.output_base}.nii.gz"
    output_log = f"{args.output_base}.log"
    check_for_output_overwrite([output_image, output_log], args.overwrite, args.silent)
    if ~args.silent:
        message("Reading in the image...")
    image = pv.read(args.image) #pv.wrap(reader.GetOutput())
    if ~args.silent:
        message("Determining the line resolution, if not given...")
    dx = args.line_resolution if args.line_resolution else min(image.spacing) / 10
    if ~args.silent:
        message("Reading in the bone mask...")
    bone_mask = pv.read(args.bone_mask) #pv.wrap(reader.GetOutput())
    if args.sub_mask:
        if ~args.silent:
            message("Reading in the sub-mask...")
        sub_mask = pv.read(args.sub_mask) #pv.wrap(reader.GetOutput())
    else:
        if ~args.silent:
            message("No sub-mask provided. Proceeding without it...")
        sub_mask = None
    if ~args.silent:
        message("Computing the boundary voxels...")
    bone_mask["boundary"] = compute_boundary_mask(bone_mask.active_scalars.reshape(bone_mask.dimensions, order="F")).flatten(order="F")
    if args.sub_mask:
        if ~args.silent:
            message("Using only the boundary voxels in the sub-mask...")
        bone_mask["boundary"] = bone_mask["boundary"] * sub_mask["NIFTI"]
    if ~args.silent:
        message("Computing the bone surface...")
    bone_surface = bone_mask.contour([1], scalars="NIFTI", progress_bar=~args.silent)
    if args.smooth_surface:
        if ~args.silent:
            message("Smoothing the surface...")
        bone_surface = bone_surface.smooth_taubin(
            n_iter=args.surface_smoothing_iterations,
            pass_band=args.surface_smoothing_passband,
            progress_bar=~args.silent
        )
    else:
        if ~args.silent:
            message("Not smoothing the surface...")
    if ~args.silent:
        message("Computing the normals...")
    bone_surface = bone_surface.compute_normals(
        auto_orient_normals=True,
        flip_normals=True,
        progress_bar=~args.silent
    )
    if ~args.silent:
        message("Resampling the surface normals back to the boundary voxels...")
    bone_mask = bone_mask.interpolate(
        bone_surface,
        strategy="closest_point",
        progress_bar=~args.silent
    )
    bone_mask["Normals"] = bone_mask["Normals"] * bone_mask["boundary"][:,np.newaxis]
    if ~args.silent:
        message("Computing the cortical thickness at each boundary voxel...")
    bone_mask["thickness"] = np.zeros((bone_mask.n_points,))
    problems = []
    for i in tqdm(np.where(bone_mask["boundary"] == 1)[0], disable=args.silent):
        intensities, x = sample_intensity_profile(
            image,
            bone_mask.points[i,:],
            bone_mask["Normals"][i,:],
            args.sample_outside_distance,
            args.sample_inside_distance,
            dx
        )
        x0, x1, model_intensities = treece_fit(
            intensities,
            x,
            bone_mask["Normals"][i,:],
            dx,
            args.cortical_density,
            args.residual_boost_factor,
            image.spacing[2], # assuming that we want the z-spacing for slice thickness
            args.cortical_threshold,
            args.soft_tissue_intensity_initial_guess,
            args.trabecular_bone_intensity_initial_guess,
            args.model_sigma_initial_guess,
        )
        bone_mask["thickness"][i] = x1 - x0

        if (x0 > x1) or (x0 < x.min()) or (x1 > x.max()):
            problems.append("-"*30)
            problems.append(f"Problem with voxel {i}.")
            problems.append(f"Point: {bone_mask.points[i,:]}")
            problems.append(f"Normal: {bone_mask['Normals'][i,:]}")
            problems.append(f"x: {x}")
            problems.append(f"Intensities: {intensities}")
            problems.append(f"Model Intensities: {model_intensities}")
            problems.append(f"x bounds: [{x.min()}, {x.max()}]")
            problems.append(f"[x0, x1]: [{x0}, {x1}]")
            problems.append(f"thickness: {bone_mask['thickness'][i]}")
            problems.append("-"*30)

        if args.debug_check_model_fit:
            plt.figure()
            plt.plot(x, intensities, "k-")
            plt.plot(x, model_intensities, "r--")
            plt.axvline(x0, color="black", linestyle="--")
            plt.axvline(x1, color="black", linestyle="--")
            plt.xlabel("x")
            plt.ylabel("intensity")
            plt.show()
            break

    if ~args.silent:
        message("Writing the cortical thickness image to disk...")
    thickness = bone_mask["thickness"].reshape(bone_mask.dimensions, order="F")
    thickness = sitk.GetImageFromArray(thickness)
    thickness.SetSpacing(image.spacing)
    thickness.SetOrigin(image.origin)
    sitk.WriteImage(thickness, output_image)

    if ~args.silent:
        message("Calculate mean and standard deviation of thickness...")
    thickness = bone_mask["thickness"][bone_mask["boundary"] == 1]
    mean_thickness = np.mean(thickness)
    std_thickness = np.std(thickness)

    if ~args.silent:
        message("Writing log file...")

    with open(output_log, "w") as f:
        f.write(echoed_args)
        f.write(f"Date and time: {datetime.now()}\n")
        f.write("-"*30 + "\n")
        f.write(f"Mean Thickness: {mean_thickness}\n")
        f.write(f"Standard Deviation of Thickness: {std_thickness}\n")
        f.write("-"*30 + "\n")
        f.write("Problems:\n")
        for problem in problems:
            f.write(problem + "\n")
        f.write("-"*30 + "\n")

    if ~args.silent:
        message("Done.")


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Use a modified version of Treece' method (doi:10.1016/j.media.2010.01.003) to compute "
                    "a cortical thickness map from an image, a bone mask, and an optional sub-mask.",
        formatter_class=ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "image", type=create_file_extension_checker(INPUT_EXTENSIONS, "image"), metavar="IMAGE",
        help=f"Provide image input filename ({', '.join(INPUT_EXTENSIONS)})"
    )
    parser.add_argument(
        "bone_mask", type=create_file_extension_checker(INPUT_EXTENSIONS, "bone mask"), metavar="BONE_MASK",
        help=f"Provide bone mask input filename ({', '.join(INPUT_EXTENSIONS)})"
    )
    parser.add_argument(
        "output_base", type=str, metavar="OUTPUT",
        help=f"Provide base for outputs, you will get a file `output`.nii.gz and `output`.log"
    )
    parser.add_argument(
        "--sub-mask", type=create_file_extension_checker(INPUT_EXTENSIONS, "sub-mask"), default=None, metavar="SUB_MASK",
        help=f"Provide optional sub-mask input filename ({', '.join(INPUT_EXTENSIONS)})"
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
        "--cortical-density", "-cd", type=float, default=800,
        help="prescribed cortical density, in the units of the image, for the model"
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
        "--cortical-threshold", "-ct", type=float, default=800,
        help="threshold for the cortical bone, used only to decide where to place the initial guesses for x0, x1"
    )
    parser.add_argument(
        "--soft-tissue-intensity-initial-guess", "-stig", type=float, default=0,
        help="initial guess for the intensity of soft tissue in the model"
    )
    parser.add_argument(
        "--trabecular-bone-intensity-initial-guess", "-tbig", type=float, default=200,
        help="initial guess for the intensity of trabecular bone in the model"
    )
    parser.add_argument(
        "--model-sigma-initial-guess", "-msig", type=float, default=1,
        help="initial guess for the sigma of inplane blurring in the model"
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
        help="enable this flag to plot the model fit for one boundary voxel, for debugging purposes"
    )

    return parser


def main():
    args = create_parser().parse_args()
    treece_thickness(args)


if __name__ == "__main__":
    main()
