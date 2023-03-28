from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import SimpleITK as sitk
from scipy.interpolate import Rbf
import os


def generate_random_deformation_field(field_shape: Tuple[int], scale: float, num_grid_points: int) -> np.ndarray:
    dim = len(field_shape)
    if (dim < 2) or (dim > 3):
        raise ValueError(f"length of `field_shape` should be 2 or 3, got {dim}")
    low_res_points = np.meshgrid(*[np.linspace(0, s-1, num_grid_points) for s in field_shape])
    # low_res_field = np.random.normal(loc=0, scale=scale, size=(*tuple(reversed(low_res_points[0].shape)), dim))
    low_res_points = [lrp.flatten() for lrp in low_res_points]
    low_res_field = np.random.normal(loc=0, scale=scale, size=(low_res_points[0].shape[0], dim))

    interpolator = Rbf(*low_res_points, low_res_field, mode="N-D")

    field_points = np.meshgrid(*[np.arange(0, s) for s in field_shape])
    return interpolator(*field_points)


def main():

    # parameters

    working_directory = "."

    mask_opacity = 0.6

    obj_shape = (15, 15, 15)
    obj_intercept = 100.0
    obj_coeffs = (50.0, 50.0, 50.0)

    pad_amount = 6

    noise_magnitude = 100.0

    num_images = 5

    deformation_scale = 2
    deformation_grid_points = 3

    # create the folders
    try:
        os.mkdir(os.path.join(working_directory, "data"))
    except FileExistsError:
        print("data folder already exists")

    try:
        os.mkdir(os.path.join(working_directory, "atlas"))
    except FileExistsError:
        print("data folder already exists")

    xyz = np.meshgrid(*[np.arange(s) for s in obj_shape])
    obj_arr = obj_intercept
    for (x, coeff) in zip(xyz, obj_coeffs):
        obj_arr += coeff * x

    img_list = []
    mask_list = []

    for i in range(num_images):
        img = np.pad(obj_arr, pad_amount, "constant")
        mask = (img >= obj_intercept).astype(float)
        img += noise_magnitude * np.random.rand(*img.shape)
        img, mask = sitk.GetImageFromArray(img), sitk.GetImageFromArray(mask)
        transform = sitk.DisplacementFieldTransform(sitk.GetImageFromArray(
            generate_random_deformation_field(img.GetSize(), deformation_scale, deformation_grid_points)
        ))
        if i > 0:
            img = sitk.Resample(img, transform, sitk.sitkLinear)
            mask = sitk.Resample(mask, transform, sitk.sitkNearestNeighbor)
        img_list.append(sitk.GetArrayFromImage(img))
        mask_list.append(sitk.GetArrayFromImage(mask))
        sitk.WriteImage(img, os.path.join(".", "data", f"image_{i}.nii"))
        sitk.WriteImage(mask, os.path.join(".", "data", f"mask_{i}.nii.gz"))

    fig, axs = plt.subplots(1, len(img_list))
    for (i, (img, mask)) in enumerate(zip(img_list, mask_list)):
        if len(img_list) > 1:
            ax = axs[i]
        else:
            ax = axs
        ax.imshow(img[:, :, img.shape[-1] // 2], cmap="gray")
        ax.imshow(mask[:, :, mask.shape[-1] // 2], cmap="Reds", alpha=mask_opacity * mask[:, :, mask.shape[-1] // 2])
        ax.axis("off")
    plt.show()



if __name__ == "__main__":
    main()
