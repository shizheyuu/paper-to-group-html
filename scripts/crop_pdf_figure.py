#!/usr/bin/env python3
"""Crop a figure from a rendered PDF page using pixel coordinates."""

import argparse
from pathlib import Path

from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="Rendered PDF page image")
    parser.add_argument("output", type=Path, help="Output PNG/JPEG")
    parser.add_argument("--box", required=True, help="left,top,right,bottom in pixels")
    args = parser.parse_args()

    box = tuple(int(v.strip()) for v in args.box.split(","))
    if len(box) != 4:
        raise SystemExit("--box must contain four integers")
    with Image.open(args.input) as image:
        width, height = image.size
        left, top, right, bottom = box
        if not (0 <= left < right <= width and 0 <= top < bottom <= height):
            raise SystemExit(f"Crop {box} exceeds image bounds {(width, height)}")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        image.crop(box).save(args.output, quality=94)
    print(args.output)


if __name__ == "__main__":
    main()
