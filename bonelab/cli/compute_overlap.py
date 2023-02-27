from __future__ import annotations

# external imports
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace, ArgumentTypeError
import SimpleITK as sitk
from matplotlib import pyplot as plt
import csv
import yaml
from typing import List, Callable

# internal imports
from bonelab.cli.registration import read_image


def compute_dice_and_jaccard(x: sitk.Image, y: sitk.Image, class_labels: List[int]) -> Tuple[List[float]]:
    overlap = sitk.LabelOverlapMeasuresImageFilter()
    dice = []
    jaccard = []
    for cl in class_labels:
        overlap.Execute(x == cl, y == cl)
        dice.append(overlap.GetDiceCoefficient())
        jaccard.append(overlap.GetJaccardCoefficient())
    return dice, jaccard


def write_output(fn: str, mask1: str, mask2: str, metrics: List[Tuple[int, float, float]]) -> None:
    with open(fn, "w") as f:
        csv_writer = csv.writer(f)
        header = ["mask1", "mask2"]
        entries = [mask1, mask2]
        for (i, dice, jaccard) in metrics:
            header += [f"dice_{i}", f"jaccard_{i}"]
            entries += [dice, jaccard]
        csv_writer.writerow(header)
        csv_writer.writerow(entries)


def compute_overlap(args: Namespace):
    class_labels = set(args.class_labels) if args.class_labels is not None else [1]
    mask1 = read_image(args.mask1, "mask1", args.silent)
    mask2 = read_image(args.mask2, "mask2", args.silent)
    # resample mask2 onto mask1 so they share the same physical space
    # use nearest neighbour because we do not want to "smear out" labels
    mask2 = sitk.Resample(mask2, mask1, sitk.Transform(), sitk.sitkNearestNeighbor)
    if args.class_labels is None:
        mask1 = sitk.Cast(mask1 > 0, sitk.sitkInt16)
        mask2 = sitk.Cast(mask2 > 0, sitk.sitkInt16)
    dice, jaccard = compute_dice_and_jaccard(mask1, mask2, class_labels)
    write_output(args.output, args.mask1, args.mask2, list(zip(class_labels, dice, jaccard)))


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="blComputeOverlap: SimpleITK Overlap Computing Tool.",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "mask1", type=str, metavar="MASK1",
        help="path to the first mask (don't use DICOMs; AIM  or NIfTI should work). Should contain either a binary "
             "mask or an integer image where the values at each voxel are class labels. NOTE: MASK2 will be resampled "
             "onto MASK1 so be aware of how that might affect your metrics if your two masks do not share the same "
             "physical space"
    )
    parser.add_argument(
        "mask2", type=str, metavar="MASK1",
        help="path to the first mask (don't use DICOMs; AIM  or NIfTI should work). Should contain either a binary "
             "mask or an integer image where the values at each voxel are class labels. NOTE: MASK2 will be resampled "
             "onto MASK1 so be aware of how that might affect your metrics if your two masks do not share the same "
             "physical space"
    )
    parser.add_argument(
        "output", type=str, metavar="OUTPUT",
        help="path to the file to save the output to, should end with *.csv"
    )
    parser.add_argument(
        "--class-labels", "-cl", default=None, type=int, nargs="+", metavar="N",
        help="the class labels to calculate overlap metrics for. If nothing is provided then the images will be"
             "binarized and only a single value for each metric will be calculated."
    )
    parser.add_argument(
        "--silent", "-s", default=False, action="store_true",
        help="enable this flag to suppress terminal output about how the registration is proceeding"
    )
    return parser


def main():
    compute_overlap(create_parser().parse_args())


if __name__ == "__main__":
    main()
