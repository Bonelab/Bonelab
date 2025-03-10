from __future__ import annotations

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace, ArgumentTypeError
import os

import numpy as np
import SimpleITK as sitk


def create_sample_data(args: Namespace):
    x, y, z = np.meshgrid(
        np.linspace(-args.img_size//2, args.img_size//2, args.img_size),
        np.linspace(-args.img_size//2, args.img_size//2, args.img_size),
        np.linspace(-args.img_size//2, args.img_size//2, args.img_size)
    )

    img = args.soft_tissue_intensity * np.ones_like(x)
    cortical = (
        ((x**2 + y**2 + z**2) < args.outer_radius**2)
        & ((x**2 + y**2 + z**2) > args.inner_radius**2)
    )
    interior = (x**2 + y**2 + z**2) < args.inner_radius**2
    img[cortical] = args.cortical_bone_intensity
    img[interior] = args.interior_bone_intensity

    mask = ((x**2 + y**2 + z**2) < args.outer_radius**2).astype(int)
    sub_mask = mask.copy()
    sub_mask[~((x>0)&(y>0)&(z>0))] = 0

    img = sitk.GetImageFromArray(img)
    mask = sitk.GetImageFromArray(mask)
    sub_mask = sitk.GetImageFromArray(sub_mask)

    img = sitk.RecursiveGaussian(img, sigma=args.smoothing_sigma)
    img = sitk.AdditiveGaussianNoise(img, args.noise)

    try:
        os.makedirs(args.dir)
    except FileExistsError:
        pass

    sitk.WriteImage(img, os.path.join(args.dir, f"{args.name}.nii.gz"))
    sitk.WriteImage(mask, os.path.join(args.dir, f"{args.name}_mask.nii.gz"))
    sitk.WriteImage(sub_mask, os.path.join(args.dir, f"{args.name}_sub_mask.nii.gz"))


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Create sample data for testing.",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "dir", type=str, metavar="DIR",
        help="The directory in which to create the sample data."
    )
    parser.add_argument(
        "name", type=str, metavar="NAME",
        help="The name for the sample data."
    )
    parser.add_argument(
        "--img-size", "-is", type=int, default=50, metavar="SIZE",
        help="The size of the sample data."
    )
    parser.add_argument(
        "--inner-radius", "-ir", type=int, default=15, metavar="INNER_RADIUS",
        help="The inner radius of the fake bone in the sample data."
    )
    parser.add_argument(
        "--outer-radius", "-or", type=int, default=20, metavar="OUTER_RADIUS",
        help="The outer radius of the fake bone in the sample data."
    )
    parser.add_argument(
        "--soft-tissue-intensity", "-sti", type=float, default=100, metavar="SOFT_TISSUE_INTENSITY",
        help="The intensity of the soft tissue in the sample data."
    )
    parser.add_argument(
        "--cortical-bone-intensity", "-cbi", type=float, default=1000, metavar="CORTICAL_BONE_INTENSITY",
        help="The intensity of the cortical bone in the sample data."
    )
    parser.add_argument(
        "--interior-bone-intensity", "-ibi", type=float, default=400, metavar="INTERIOR_BONE_INTENSITY",
        help="The intensity of the interior bone in the sample data."
    )
    parser.add_argument(
        "--smoothing-sigma", "-ss", type=float, default=1, metavar="SMOOTHING_SIGMA",
        help="The sigma for the gaussian smoothing filter to apply before adding noise."
    )
    parser.add_argument(
        "--noise", "-n", type=float, default=100, metavar="NOISE",
        help="The variance of the gaussian noise to add to the sample data."
    )
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    create_sample_data(args)


if __name__ == "__main__":
    main()
