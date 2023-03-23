from __future__ import annotations

# external imports
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Namespace

# internal imports
from bonelab.cli.registration import (
    read_image, check_inputs_exist, check_for_output_overwrite, write_args_to_yaml,
    create_file_extension_checker, create_string_argument_checker, read_and_downsample_images
)
from bonelab.util.time_stamp import message
from bonelab.util.multiscale_registration import multiscale_demons


# functions
def create_atlas(args: Namespace) -> None:
    # going to follow the method prescribed in appendix A of DOI: 10.1016/j.neuroimage.2003.11.010.
    # also published in DOI: 10.1109/MMBIA.2001.991733
    # step 1: randomly pick one image as reference, affine register all other images to this one
    # step 2: compute the average image using all the affinely transformed images
    # step 3: deformably register all images to this average image
    # step 4: compute the average image using all the deformably registered images
    # step 5: check if converged, if not then go back to step 3 and use the current average image as the reference
    # step 6: use the converged transformations to transform all segmentations to the atlas
    # step 7: use STAPLE to generate the final atlas segmentation
    # step 8: write the atlas image and segmentation to file

    pass


# parser
def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="This tool generates a segmented atlas image from a list of images with segmentations. "
                    "The atlas generation procedure was originally published in (1) and was evaluated in (2). "
                    "The steps of the procedure are: (1) Select the first image given in the list as the atlas "
                    "image, (2) affinely register all other images to the atlas image, (3) transform all images "
                    "to the space of the atlas image, compute the average image, and set this as the new atlas "
                    "image, (4) deformably register all images to the atlas image, (5) transform all images to the "
                    "space of the atlas image, re-compute the average image, and set this as the new atlas "
                    "image, (6) repeat steps 4 and 5 until the atlas image has converged, (7) deformably register "
                    "all images to the final atlas image, (8) transform all segmentations to the atlas space "
                    "using nearest neighbour interpolation, (9) use STAPLE to generate the atlas segmentation, "
                    "(10) write the average-atlas and atlas segmentation to file. "
                    "The user is given all of of the necessary command line options to configure both the affine and "
                    "deformable registration parameters so that the method of atlas generation can be consistent with "
                    "the method of atlas-based segmentation using the atlas.",
        epilog="(1) DOI: 10.1109/MMBIA.2001.991733, (2) DOI: 10.1016/j.neuroimage.2003.11.010 ",
        formatter_class=ArgumentDefaultsHelpFormatter
    )

    return parser


# main
def main():
    create_atlas(create_parser().parse_args())


if __name__ == "__main__":
    main()
