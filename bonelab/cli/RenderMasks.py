import pyvista as pv
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from glob import glob
from bonelab.io.vtk_helpers import get_vtk_reader


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="RenderMasks - Utility for rendering a mask image isometrically and volumetrically.",
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    screen_subparsers = parser.add_subparsers(help="on- or off-screen rendering")
    onscreen_parser = screen_subparsers.add_parser("onscreen", help="render on-screen")
    return parser


def main():
    pass


if __name__ == "__main__":
    main()
