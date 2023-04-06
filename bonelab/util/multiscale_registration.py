"""
code source: https://simpleitk.org/SPIE2019_COURSE/05_advanced_registration.html

Modified slightly but mechanically the same as the source. Also some extra stuff added to make using it easier.
"""

from __future__ import annotations

import SimpleITK as sitk
from typing import Callable, Optional, List
from memory_profiler import profile
from copy import deepcopy

from bonelab.util.time_stamp import message


# a list of Demons registration filters available in SimpleITK
DEMONS_FILTERS = {
    "demons": sitk.DemonsRegistrationFilter,
    "diffeomorphic": sitk.DiffeomorphicDemonsRegistrationFilter,
    "symmetric": sitk.SymmetricForcesDemonsRegistrationFilter,
    "fast_symmetric": sitk.FastSymmetricForcesDemonsRegistrationFilter
}


class MetricTrackingCallback:

    def __init__(self, registration_filter: sitk.ImageFilter, silent: bool = True, demons: bool = True):
        self._registration_filter = registration_filter
        self._silent = silent
        self._demons = demons
        self._metric_history = []

    @property
    def metric_history(self) -> List[float]:
        return self._metric_history

    @property
    def silent(self) -> bool:
        return self._silent

    @property
    def demons(self) -> bool:
        return self._demons

    @property
    def registration_filter(self) -> sitk.ImageFilter:
        return self._registration_filter

    def __call__(self):
        if self._demons:
            metric = self._registration_filter.GetMetric()
        else:
            metric = self._registration_filter.GetMetricValue()
        self._metric_history.append(metric)
        if not self._silent:
            if self._demons:
                iteration = self._registration_filter.GetElapsedIterations()
            else:
                iteration = self._registration_filter.GetOptimizerIteration()
            message(f"Iteration: {iteration:d}, Metric: {metric:0.5e}")


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


@profile()
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


@profile()
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
    deformation_field = multiscale_registration(
        demons, fixed_image, moving_image, initial_transform, multiscale_progression, silent
    )
    demons.RemoveAllCommands()
    return deformation_field, metric_callback.metric_history
