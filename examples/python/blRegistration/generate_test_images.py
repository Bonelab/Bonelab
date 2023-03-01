import numpy as np
import SimpleITK as sitk
import matplotlib.pyplot as plt
import os
from scipy.ndimage import affine_transform, rotate


def main():
    working_directory = "."

    mask_opacity = 0.6

    obj_shape = (10, 10, 10)
    obj_intercept = 100.0
    obj_coeffs = (50.0, 50.0, 50.0)

    noise_magnitude = 100.0

    # create the folders
    try:
        os.mkdir(os.path.join(working_directory, "data"))
    except FileExistsError:
        print("data folder already exists")

    try:
        os.mkdir(os.path.join(working_directory, "registration"))
    except FileExistsError:
        print("registration folder already exists")

    try:
        os.mkdir(os.path.join(working_directory, "transformed_masks"))
    except FileExistsError:
        print("transformed_masks folder already exists")

    try:
        os.mkdir(os.path.join(working_directory, "overlap_metrics"))
    except FileExistsError:
        print("overlap_metrics folder already exists")

    xyz = np.meshgrid(*[np.arange(s) for s in obj_shape])
    obj_arr = obj_intercept
    for (x, coeff) in zip(xyz, obj_coeffs):
        obj_arr += coeff * x

    img_dict = {}

    # for the base image we will just pad by 10 around the object and add some noise
    img_dict["base"] = np.pad(obj_arr, 10, "constant")

    # for the translated image, just pad unevenly
    img_dict["translated"] = np.pad(obj_arr, (15, 5), "constant")

    # for rotated image, use the scipy ndimage rotate function after padding
    img_dict["rotated"] = rotate(img_dict["base"], 45, reshape=False, order=2)

    # for squashed and stretched images, use scipy ndimage affine_transform function after padding
    img_dict["squashed"] = affine_transform(img_dict["base"], [1.0, 2.0, 1.0], offset=(0, -10, 0))
    img_dict["stretched"] = affine_transform(img_dict["base"], [1.0, 0.5, 1.0], offset=(0, 7, 0))

    # create the masks
    mask_dict = {}
    for (k, v) in img_dict.items():
        mask_dict[k] = (v >= obj_intercept).astype(float)

    # add noise to all images
    for v in img_dict.values():
        v += noise_magnitude * np.random.rand(*v.shape)

    # convert to simple itk, write to disk
    for (k, v) in img_dict.items():
        m = mask_dict[k]
        img = sitk.GetImageFromArray(v)
        sitk.WriteImage(img, os.path.join(working_directory, "data", f"{k}.nii"))
        mask = sitk.GetImageFromArray(m)
        sitk.WriteImage(mask, os.path.join(working_directory, "data", f"{k}_mask.nii"))

    fig, axs = plt.subplots(1, len(img_dict))
    for (i, (k, v)) in enumerate(img_dict.items()):
        m = mask_dict[k]
        if len(img_dict) > 1:
            ax = axs[i]
        else:
            ax = axs
        ax.set_title(k)
        ax.imshow(v[:, :, v.shape[-1] // 2], cmap="gray")
        ax.imshow(m[:, :, v.shape[-1] // 2], cmap="Reds", alpha=mask_opacity*m[:, :, v.shape[-1] // 2])
        ax.axis("off")
    plt.show()


if __name__ == "__main__":
    main()
