from __future__ import annotations

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import SimpleITK as sitk


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description='blRegistration: SimpleITK Registration Tool',
        formatter_class=ArgumentDefaultsHelpFormatter
    )

    return parser


def main():
    args = create_parser().parse_args()


if __name__ == "__main__":
    pass