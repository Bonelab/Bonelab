"""
code source: https://simpleitk.org/SPIE2019_COURSE/05_advanced_registration.html

Modified slightly but mechanically the same as the source. Also some extra stuff added to make using it easier.
"""

from __future__ import annotations

from enum import Enum

import SimpleITK as sitk
import numpy as np
from typing import Callable, Optional, List, Tuple

from bonelab.util.time_stamp import message


# a list of Demons registration filters available in SimpleITK
DEMONS_FILTERS = {
    "demons": sitk.DemonsRegistrationFilter,
    "diffeomorphic": sitk.DiffeomorphicDemonsRegistrationFilter,
    "symmetric": sitk.SymmetricForcesDemonsRegistrationFilter,
    "fast_symmetric": sitk.FastSymmetricForcesDemonsRegistrationFilter
}
OutputType = Enum("OutputType", ["IMAGE", "TRANSFORM"])
IMAGE_EXTENSIONS = [".nii", ".nii.gz"]
TRANSFORM_EXTENSIONS = [".hdf", ".mat"]  # only allow the binary versions, no plain-text displacement fields


class MetricTrackingCallback:
    """
    A callback class for tracking the metric value of a registration filter. This class is intended to be used with
    the `AddCommand` method of a registration filter. The `__call__` method of this class will be called at each
    iteration of the registration filter, and will store the metric value in the `metric_history` property.
    """

    def __init__(self,
                 registration_filter: sitk.ImageFilter,
                 silent: bool = True,
                 demons: bool = True,
                 patience: int = 50,
                 rolling_average_window: int = 10
                 ):
        """
        Initialize the callback class.

        Parameters
        ----------
        registration_filter : sitk.ImageFilter
            The registration filter to track the metric value of.

        silent : bool
            Whether or not to print out the metric value at each iteration.

        demons : bool
            Whether or not the registration filter is a demons filter. If it is, then the metric value is accessed
            with the `GetMetric` method, otherwise it is accessed with the `GetMetricValue` method.

        patience : int
            The number of iterations to wait before checking for convergence.

        rolling_average_window : int
            The number of iterations to use for the rolling average when checking for convergence.
        """
        self._registration_filter = registration_filter
        self._silent = silent
        self._demons = demons
        self._patience = patience
        self._patience_counter = 0
        self._rolling_average_window = rolling_average_window
        self._metric_history = []

    @property
    def metric_history(self) -> List[float]:
        """
        The history of the metric values.

        Returns
        -------
        List[float]
            The history of the metric values.
        """
        return self._metric_history

    @property
    def silent(self) -> bool:
        """
        Whether or not to print out the metric value at each iteration.

        Returns
        -------
        bool
            Whether or not to print out the metric value at each iteration.
        """
        return self._silent

    @property
    def demons(self) -> bool:
        """
        Whether or not the registration filter is a demons filter. If it is, then the metric value is accessed
        with the `GetMetric` method, otherwise it is accessed with the `GetMetricValue` method.

        Returns
        -------
        bool
            Whether or not the registration filter is a demons filter.
        """
        return self._demons

    @property
    def registration_filter(self) -> sitk.ImageFilter:
        """
        The registration filter to track the metric value of.

        Returns
        -------
        sitk.ImageFilter
            The registration filter to track the metric value of.
        """
        return self._registration_filter

    @property
    def patience(self) -> int:
        """
        The number of iterations to wait before checking for convergence.

        Returns
        -------
        int
            The number of iterations to wait before checking for convergence.
        """
        return self._patience

    @property
    def rolling_average_window(self) -> int:
        """
        The number of iterations to use for the rolling average when checking for convergence.

        Returns
        -------
        int
            The number of iterations to use for the rolling average when checking for convergence.
        """
        return self._rolling_average_window

    @property
    def patience_counter(self) -> int:
        """
        The number of iterations since the registration began.

        Returns
        -------
        int
            The number of iterations since the registration began.
        """
        return self._patience_counter

    def reset_patience(self):
        """
        Reset the patience counter to zero.

        Returns
        -------
        None
        """
        self._patience_counter = 0

    def __call__(self):
        """
        The method called at each iteration of the registration filter. This method will store the metric value in the
        `metric_history` property, and will check for convergence.

        Returns
        -------
        None
        """
        # get the metric value
        if self._demons:
            metric = self._registration_filter.GetMetric()
        else:
            metric = self._registration_filter.GetMetricValue()
        self._metric_history.append(metric)
        # check for convergence
        is_converged = False
        if not(
                (self._patience_counter < self._patience)
                or (len(self._metric_history) < self._rolling_average_window)
        ):
            metric_window = np.asarray(self._metric_history[-self._rolling_average_window:])
            if metric > metric_window.mean():
                is_converged = True
        if is_converged:
            self._registration_filter.StopRegistration()

        # terminal messages
        if not self._silent:
            if self._demons:
                iteration = self._registration_filter.GetElapsedIterations()
            else:
                iteration = self._registration_filter.GetOptimizerIteration()
            message(f"Iter: {iteration:d}, Metric: {metric:0.5e}."
                    f" Converged: {is_converged}")

        self._patience_counter += 1


def smooth_and_resample(image: sitk.Image, shrink_factor: float, smoothing_sigma: float) -> sitk.Image:
    """
    This function can be used on its own to smooth and resample an image, but it is here mainly because it is used
    in the `multiscale_registration` function to get down-sampled images.

    Parameters
    ----------
    image : sitk.Image
        The image to resample at a lower resolution.

    shrink_factor : float
        The multiple by which to shrink the image.

    smoothing_sigma : float
        The sigma for the gaussian smoothing, in the same physical units as the image spacing.

    Returns
    -------
    sitk.Image
        The filtered and downsampled image.
    """
    # compute the size and spacing of the resampled image
    new_size = [int(sz / float(shrink_factor) + 0.5) for sz in image.GetSize()]
    new_spacing = [
        ((osz - 1) * osp) / (nsz - 1)
        for (osz, osp, nsz) in zip(image.GetSize(), image.GetSpacing(), new_size)
    ]

    # smooth and resample
    return sitk.Resample(
        sitk.SmoothingRecursiveGaussian(image, smoothing_sigma),
        new_size, sitk.Transform(), sitk.sitkLinear, image.GetOrigin(),
        new_spacing, image.GetDirection(), 0.0, image.GetPixelID()
    )


def multiscale_registration(
    registration_algorithm: sitk.ImageFilter,
    fixed_image: sitk.Image,
    moving_image: sitk.Image,
    initial_transform: Optional[sitk.Transform] = None,
    multiscale_progression: Optional[List[Tuple[float, float]]] = None,
    silent: bool = True
) -> sitk.DisplacementFieldTransform:
    """
    Perform a multiscale registration using a given registration algorithm and fixed/moving image pair. You can
    optionally pass in an initial transform and the multiscale progression.

    Parameters
    ----------
    registration_algorithm : sitk.ImageFilter
        Any registration image filter in SimpleITK that has a method called `Execute` that takes two SimpleITK images
        and a displacement field image as arguments and which returns a displacement field.

    fixed_image : sitk.Image
        A SimpleITK image. The resulting transformation will point from this image's coordinate system into the
        moving_image's coordinate system.

    moving_image : sitk.Image
        A SimpleITK image. The resulting transformation will point from the fixed_image's coordinate system into this
        image's coordinate system.

    initial_transform : Optional[sitk.Transform]
        A SimpleITK transform to initialize the registration with, if provided.

    multiscale_progression : Optional[List[Tuple[float, float]]]
        A list of tuples that each contain two floats: the first is a shrink factor and the second is a smoothing
        sigma. If this argument is provided, a series of registrations will be performed on resampled and smoothed
        images in the order that the shrink factor and smoothing sigma pairs are given, ending with a final registration
        at full resolution. If this argument is not given then only one registration is performed, at full resolution.

    silent : bool
        Suppress terminal output.

    Returns
    -------
    sitk.DisplacementFieldTransform
        The final transform output by the final registration at full resolution.
    """
    # Create initial displacement field
    # The pixel type is required to be sitkVectorFloat64 because of a constraint imposed by the Demons filters.
    if initial_transform:
        displacement_field = sitk.TransformToDisplacementField(
            initial_transform, sitk.sitkVectorFloat64, fixed_image.GetSize(),
            fixed_image.GetOrigin(), fixed_image.GetSpacing(), fixed_image.GetDirection()
        )
    else:
        displacement_field = sitk.Image(*fixed_image.GetSize(), sitk.sitkVectorFloat64)
        displacement_field.CopyInformation(fixed_image)

    # If we are doing this with a multiscale progression, work through this progression in order first
    if multiscale_progression is not None:
        if not silent:
            message(f"Multiscale progression starting | There will be {len(multiscale_progression):d} steps.")
        for (i, (shrink_factor, smoothing_sigma)) in enumerate(multiscale_progression):
            if not silent:
                message(f"Step {i+1:d} of {len(multiscale_progression):d} "
                        f"| Shrink factor: {shrink_factor:0.2f}, Sigma: {smoothing_sigma:0.2f} | Starting:")
            resampled_fixed_image = smooth_and_resample(fixed_image, shrink_factor, smoothing_sigma)
            resampled_moving_image = smooth_and_resample(moving_image, shrink_factor, smoothing_sigma)
            displacement_field = registration_algorithm.Execute(
                resampled_fixed_image, resampled_moving_image,
                sitk.Resample(displacement_field, resampled_fixed_image)
            )

    # Finish off by doing one registration at full resolution
    if not silent:
        message("Final registration at full resolution:")
    transform = registration_algorithm.Execute(
        fixed_image, moving_image,
        sitk.Resample(displacement_field, fixed_image)
    )
    return transform


def multiscale_demons(
    fixed_image: sitk.Image,
    moving_image: sitk.Image,
    demons_type: str = "demons",
    demons_iterations: int = 100,
    demons_displacement_field_smooth_std: Optional[float] = 1.0,
    demons_update_field_smooth_std: Optional[float] = 1.0,
    initial_transform: Optional[sitk.Transform] = None,
    multiscale_progression: Optional[List[Tuple[float, float]]] = None,
    silent: bool = True
) -> Tuple[sitk.Image, List[float]]:
    """
    Perform a multiscale registration using a given registration algorithm and fixed/moving image pair. You can
    optionally pass in an initial transform and the multiscale progression.

    Parameters
    ----------
    fixed_image : sitk.Image
        A SimpleITK image. The resulting transformation will point from this image's coordinate system into the
        moving_image's coordinate system.

    moving_image : sitk.Image
        A SimpleITK image. The resulting transformation will point from the fixed_image's coordinate system into this
        image's coordinate system.

    demons_type : str
        Specify what kind of Demons deformable registration filter to use. Default is "demons"
        Options:
            "demons": sitk.DemonsRegistrationFilter,
            "diffeomorphic": sitk.DiffeomorphicDemonsRegistrationFilter,
            "symmetric": sitk.SymmetricForcesDemonsRegistrationFilter,
            "fast_symmetric": sitk.FastSymmetricForcesDemonsRegistrationFilter

    demons_iterations : int
        Maximum number of iterations to run the demons algorithm each time it is called. Default: 100

    demons_displacement_field_smooth_std : Optional[float]
        The standard deviation of the gaussian applied to the displacement field in the Demons filter as regularization,
        in physical units. Set this argument to `None` to disable displacement field smoothing. Default: 1.0

    demons_update_field_smooth_std : Optional[float]
        The standard deviation of the gaussian applied to the update field in the Demons filter as regularization,
        in physical units. Set this argument to `None` to disable update field smoothing. Default: 1.0

    initial_transform : Optional[sitk.Transform]
        A SimpleITK transform to initialize the registration with, if provided.

    multiscale_progression : Optional[List[Tuple[float, float]]]
        A list of tuples that each contain two floats: the first is a shrink factor and the second is a smoothing
        sigma. If this argument is provided, a series of registrations will be performed on resampled and smoothed
        images in the order that the shrink factor and smoothing sigma pairs are given, ending with a final registration
        at full resolution. If this argument is not given then only one registration is performed, at full resolution.

    silent : bool
        Suppress terminal output.

    Returns
    -------
    sitk.DisplacementFieldTransform
        The final transform output by the final registration at full resolution.

    List[float]
        A list of floats containing the value of the metric at each iteration of the registration.
    """
    # create the registration filter
    demons = DEMONS_FILTERS[demons_type]()
    demons.SetNumberOfIterations(demons_iterations)
    if demons_displacement_field_smooth_std is not None:
        demons.SetSmoothDisplacementField(True)
        demons.SetStandardDeviations(demons_displacement_field_smooth_std)
    else:
        demons.SetSmoothDisplacementField(False)
    if demons_update_field_smooth_std is not None:
        demons.SetSmoothUpdateField(True)
        demons.SetUpdateFieldStandardDeviations(demons_update_field_smooth_std)
    else:
        demons.SetSmoothUpdateField(False)
    metric_callback = MetricTrackingCallback(demons, silent, True)
    demons.AddCommand(sitk.sitkIterationEvent, metric_callback)
    demons.AddCommand(sitk.sitkStartEvent, metric_callback.reset_patience)
    deformation_field = multiscale_registration(
        demons, fixed_image, moving_image, initial_transform, multiscale_progression, silent
    )
    demons.RemoveAllCommands()
    return deformation_field, metric_callback.metric_history


def demons_type_checker(s: str) -> str:
    """
    Check that the demons type is valid.

    Parameters
    ----------
    s : str
        The demons type to check.

    Returns
    -------
    str
        The demons type if it is valid.
    """
    s = str(s)
    if s in DEMONS_FILTERS.keys():
        return s
    else:
        return ValueError(f"Demons type {s}, not valid, please choose from: {list(DEMONS_FILTERS.keys())}")


def read_transform(initial_transform: Optional[str]) -> Optional[sitk.Transform]:
    """
    Read a transform from a file.

    Parameters
    ----------
    initial_transform : Optional[str]
        The path to the transform file to read.

    Returns
    -------
    Optional[sitk.Transform]
        The transform if it exists, otherwise None.
    """
    if initial_transform is not None:
        return sitk.ReadTransform(initial_transform)
    else:
        return None


def construct_multiscale_progression(
        shrink_factors: Optional[List[float]],
        smoothing_sigmas: Optional[List[float]],
        silent: bool
) -> Optional[List[Tuple[float]]]:
    """
    Construct a multiscale progression from the shrink factors and smoothing sigmas.

    Parameters
    ----------
    shrink_factors : Optional[List[float]]
        The shrink factors to use for the multiscale registration.

    smoothing_sigmas : Optional[List[float]]
        The smoothing sigmas to use for the multiscale registration.

    silent : bool
        Suppress terminal output.

    Returns
    -------
    Optional[List[Tuple[float]]]
        The multiscale progression.
    """
    if (shrink_factors is not None) and (smoothing_sigmas is not None):
        if len(shrink_factors) == len(smoothing_sigmas):
            if not silent:
                message(f"Performing multiscale registration with shrink factors: "
                        f"{', '.join([str(sf) for sf in shrink_factors])}; "
                        f"and smoothing sigmas: "
                        f"{', '.join([str(ss) for ss in smoothing_sigmas])}")
            return list(zip(shrink_factors, smoothing_sigmas))
        else:
            raise ValueError("`shrink-factors` and `smoothing-sigmas` must have same length")
    elif (shrink_factors is None) and (smoothing_sigmas is None):
        if not silent:
            message("Not performing multiscale registration.")
        return None
    else:
        raise ValueError("one of `shrink-factors` or `smoothing-sigmas` have not been specified. you must "
                         "either leave both as the default `None` or specify both (with equal length)")


def create_centering_transform(
        fixed_image: sitk.Image,
        moving_image: sitk.Image,
        centering_initialization: str,
        silent: bool
) -> sitk.Transform:
    """
    Create a centering transform.

    Parameters
    ----------
    fixed_image : sitk.Image
        The fixed image.

    moving_image : sitk.Image
        The moving image.

    centering_initialization : str
        The type of centering initialization to use.

    silent : bool
        Suppress terminal output.

    Returns
    -------
    sitk.Transform
        The centering transform.
    """
    if fixed_image.GetDimension() == 3:
        if not silent:
            message("Initializing a 3D rigid transform")
        transform_type = sitk.Euler3DTransform()
    elif fixed_image.GetDimension() == 2:
        if not silent:
            message("Initializing a 2D rigid transform")
        transform_type = sitk.Euler2DTransform()
    else:
        raise ValueError(f"`fixed_image` has dimension of {fixed_image.GetDimension()}, only 2 and 3 supported")
    if centering_initialization == "Geometry":
        if not silent:
            message("Centering the initial transform using geometry")
        centering_initialization = sitk.CenteredTransformInitializerFilter.GEOMETRY
    elif centering_initialization == "Moments":
        if not silent:
            message("Centering the initial transform using moments")
        centering_initialization = sitk.CenteredTransformInitializerFilter.MOMENTS
    else:
        raise ValueError("`centering_initialization` is invalid and was not caught")
    return sitk.CenteredTransformInitializer(
        fixed_image, moving_image,
        transform_type, centering_initialization
    )


def get_initial_transform(
        initial_transform: Optional[str],
        fixed_image: sitk.Image,
        moving_image: sitk.Image,
        centering_initialization: str,
        silent: bool
) -> sitk.Transform:
    """
    Get the initial transform.

    Parameters
    ----------
    initial_transform : str
        The path to the initial transform.

    fixed_image : sitk.Image
        The fixed image.

    moving_image : sitk.Image
        The moving image.

    centering_initialization : str
        The type of centering initialization to use.

    silent : bool
        Suppress terminal output.

    Returns
    -------
    sitk.Transform
        The initial transform.
    """
    if initial_transform is not None:
        if not silent:
            message("Reading initial transform.")
        return read_transform(initial_transform)
    else:
        return create_centering_transform(fixed_image, moving_image, centering_initialization, silent)


def add_initial_transform_to_displacement_field(
        field: sitk.Image,
        transform: sitk.Transform,
        silent: bool
) -> sitk.Image:
    """
    Add the initial transform to the displacement field.

    Parameters
    ----------
    field : sitk.Image
        The displacement field.

    transform : sitk.Transform
        The initial transform.

    silent : bool
        Suppress terminal output.

    Returns
    -------
    sitk.Image
        The displacement field with the initial transform added.
    """
    if not silent:
        message("Converting initial transform to displacement field and adding it to the Demons displacement field.")
    return sitk.Add(
        field,
        sitk.TransformToDisplacementField(
            transform,
            field.GetPixelID(),
            field.GetSize(),
            field.GetOrigin(),
            field.GetSpacing(),
            field.GetDirection()
        )
    )


def write_transform_or_field(fn: str, field: sitk.Image, silent: bool) -> None:
    """
    Write the transform or displacement field.

    Parameters
    ----------
    fn : str
        The path to the output file.

    field : sitk.Image
        The displacement field.

    silent : bool
        Suppress terminal output.

    Returns
    -------
    None
    """
    for ext in TRANSFORM_EXTENSIONS:
        if fn.lower().endswith(ext):
            if not silent:
                message(f"Writing transform to {fn}")
            sitk.WriteTransform(sitk.DisplacementFieldTransform(field), fn)
            return
    for ext in IMAGE_EXTENSIONS:
        if fn.lower().endswith(ext):
            if not silent:
                message(f"Writing displacement field to {fn}")
            sitk.WriteImage(field, fn)
            return
    raise ValueError(f"`output`, {fn}, does not have a valid extension and it was not caught.")


def write_displacement_visualization(
        fn: str,
        field: sitk.Image,
        grid_spacing: int,
        grid_sigma: float,
        silent: bool
) -> None:
    """
    Write the displacement field visualization.

    Parameters
    ----------
    fn : str
        The path to the output file.

    field : sitk.Image
        The displacement field.

    grid_spacing : int
        The grid spacing for the visualization.

    grid_sigma : float
        The grid sigma for the visualization.

    silent : bool
        Suppress terminal output.

    Returns
    -------
    None
    """
    if not silent:
        message(f"Writing displacement field visualization to {fn}")
    dim = field.GetDimension()
    grid_image = sitk.GridSource(
        size=field.GetSize(),
        sigma=tuple([grid_sigma] * dim),
        gridSpacing=tuple([grid_spacing] * dim),
        origin=field.GetOrigin(),
        spacing=field.GetSpacing(),
        direction=field.GetDirection()
    )
    sitk.WriteImage(sitk.Resample(grid_image, sitk.DisplacementFieldTransform(field)), fn)
