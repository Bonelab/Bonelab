from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from bonelab.io.vtk_helpers import get_vtk_reader
from bonelab.util.aim_calibration_header import get_aim_density_equation
from bonelab.util.vtk_util import vtkImageData_to_numpy
from pathlib import Path
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description='2D Panning Video Creation Script',
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "filename", type=str, metavar="FILENAME",
        help="Filename of image to make video from. NOTE: If your image is in a directory, put one of the individual "
             "files here and then set the `-dir` flag, so a proper reader can be selected."
    )
    parser.add_argument(
        "video_name", type=str, metavar="VIDEO_NAME",
        help="Filename to save the video to, without an extension (.mp4 or .gif will be appended)."
    )
    parser.add_argument(
        "--directory", "-dir", action="store_true", default=False,
        help="Set this flag if your image is contained within a directory, such as a DICOM"
    )
    parser.add_argument(
        "--scanco-aim", "-aim", action="store_true", default=False,
        help="Set this flag if your image is a Scanco AIM and you want the intensities converted to densities."
    )
    parser.add_argument(
        "--intensity-bounds", "-ib", nargs=2, type=int, default=None, metavar="N",
        help="Lower and upper limit of intensities to display. If `None`, use maximum range."
    )
    parser.add_argument(
        "--x-bounds", "-xb", nargs=2, type=int, default=None, metavar="N",
        help="Lower and upper bound of x values to plot. If `None`, use maximum range."
    )
    parser.add_argument(
        "--y-bounds", "-yb", nargs=2, type=int, default=None, metavar="N",
        help="Lower and upper bound of y values to plot. If `None`, use maximum range."
    )
    parser.add_argument(
        "--z-bounds", "-zb", nargs=2, type=int, default=None, metavar="N",
        help="Lower and upper bound of z values to plot. If `None`, use maximum range."
    )
    parser.add_argument(
        "--panning-dimension", "-pd", type=int, default=2, metavar="N",
        help="Dimension to pan over. Must be between 0 and 2 - if another value is given, 2 will be used."
    )
    parser.add_argument(
        "--animation-interval", "-ai", type=int, default=20, metavar="N",
        help="Interval between frames in the animation, in milliseconds."
    )
    parser.add_argument(
        "--mp4-fps", "-fps", type=int, default=60, metavar="N",
        help="Frames per second for the mp4 video."
    )
    parser.add_argument(
        "--preview", "-p", action="store_true", default=False,
        help="Enable this flag to see your animation in a pyplot window before it's saved to file."
    )
    return parser


def main() -> None:
    args = create_parser().parse_args()
    if args.panning_dimension not in [0, 1, 2]:
        args.panning_dimension = 2
    reader = get_vtk_reader(args.filename)
    if args.directory:
        reader.SetDirectory(Path(args.filename).parents[0])
    else:
        reader.SetFileName(args.filename)
    reader.Update()
    image = vtkImageData_to_numpy(reader.GetOutput())
    # this will be used in the future to set figure sizing so there's the correct aspect ratio
    image_spacing = reader.GetOutput().GetSpacing()
    if args.scanco_aim:
        calib_m, calib_b = get_aim_density_equation(reader.GetProcessingLog())
        image = calib_m * image + calib_b
    if args.intensity_bounds is None:
        args.intensity_bounds = [image.min(), image.max()]
    if args.x_bounds is None:
        args.x_bounds = [0, image.shape[0]]
    else:
        args.x_bounds[0] = max(args.x_bounds[0], 0)
        args.x_bounds[1] = min(args.x_bounds[1], image.shape[0])
    if args.y_bounds is None:
        args.y_bounds = [0, image.shape[1]]
    else:
        args.y_bounds[0] = max(args.y_bounds[0], 0)
        args.y_bounds[1] = min(args.y_bounds[1], image.shape[1])
    if args.z_bounds is None:
        args.z_bounds = [0, image.shape[2]]
    else:
        args.z_bounds[0] = max(args.z_bounds[0], 0)
        args.z_bounds[1] = min(args.z_bounds[1], image.shape[2])

    fig = plt.figure()
    ax = plt.axes()

    def animate(i: int) -> None:
        slicing_list = [slice(*args.x_bounds), slice(*args.y_bounds), slice(*args.z_bounds)]
        slicing_list[args.panning_dimension] = i
        ax.clear()
        ax.imshow(
            image[tuple(slicing_list)], cmap="gray",
            vmin=args.intensity_bounds[0], vmax=args.intensity_bounds[1]
        )
        ax.set_frame_on(False)
        ax.axes.get_xaxis().set_visible(False)
        ax.axes.get_yaxis().set_visible(False)

    if args.panning_dimension == 0:
        animation_frames = np.arange(*args.x_bounds)
    elif args.panning_dimension == 1:
        animation_frames = np.arange(*args.y_bounds)
    elif args.panning_dimension == 2:
        animation_frames = np.arange(*args.z_bounds)
    else:
        raise ValueError("panning_dimension arg is somehow a value it cannot be")

    anim = FuncAnimation(fig, animate, frames=animation_frames, interval=args.animation_interval)
    if args.preview:
        plt.show()
    try:
        ffmpeg_writer = FFMpegWriter(fps=args.mp4_fps)
        anim.save(f"{args.video_name}.mp4", writer=ffmpeg_writer)
    except FileNotFoundError:
        print("`ffmpeg` not found, saving as a gif. Run `conda install ffmpeg` if you want an mp4.")
        anim.save(f"{args.video_name}.gif", writer="imagemagick")


if __name__ == '__main__':
    main()
