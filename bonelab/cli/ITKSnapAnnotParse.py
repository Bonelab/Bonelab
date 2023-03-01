from __future__ import annotations

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from glob import glob
from pathlib import Path

import xml.etree.ElementTree as ET
import numpy as np


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description='ITK-Snap Annotation File Parsing Script',
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "annot_pattern", type=str, metavar="ANNOT_PATTERN",
        help="glob pattern of the annot files you want to parse"
    )
    parser.add_argument(
        "--spacing", "-s", type=float, nargs=3, metavar="X", default=[1.0, 1.0, 1.0],
        help="spatial resolution of the image"
    )

    return parser


def main() -> None:
    args = create_parser().parse_args()
    fns = glob(args.annot_pattern)
    for fn in fns:
        print(fn)
        tree = ET.parse(fn)
        root = tree.getroot()

        distances = []

        p1, p2 = None, None

        for element in root.findall("./folder/folder/entry"):
            if element.attrib["key"] == "Point1":
                p1 = np.asarray([float(s) for s in element.attrib["value"].split(" ")])
                print("P1:", p1)
            elif element.attrib["key"] == "Point2":
                p2 = np.asarray([float(s) for s in element.attrib["value"].split(" ")])
                print("P2:", p2)
                distances.append(np.linalg.norm((p1 - p2) * np.asarray(args.spacing)))
                print("Distance:", distances[-1])
                p1, p2 = None, None

        np.savetxt(f"{Path(fn).with_suffix('')}_annot_parsed_distances.txt", distances, delimiter=",")


if __name__ == "__main__":
    main()
