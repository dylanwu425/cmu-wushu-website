#!/usr/bin/env python3
"""
Turn member photos into the square, web-sized copies the About page uses.

  1. Drop each original photo into images/members/originals/, named after the
     person, e.g. jane-doe.jpg (lowercase, hyphens, no spaces). iPhone HEIC
     files are fine.
  2. Run:   python3 scripts/crop_members.py
  3. It writes images/members/jane-doe.jpg: a 480 x 480 square, cropped
     towards the top of the frame (where faces usually are), upright, and
     small enough for the web. Then point the member's <li> in about.html at
     that file.

Originals are never changed and never published. Re-running only redoes
photos whose original is newer than the copy.
"""

import os
import subprocess
import sys
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(HERE, "images", "members", "originals")
OUT = os.path.join(HERE, "images", "members")
SIZE = 480
QUALITY = 84
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".heic", ".heif"}


def heic_to_jpeg(src, dst):
    """macOS ships `sips`, which reads HEIC. Pillow usually cannot."""
    try:
        subprocess.run(["sips", "-s", "format", "jpeg", src, "--out", dst],
                       check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def square(im):
    """Crop to a square. Portrait photos keep the top (faces), landscape
    photos keep the middle."""
    w, h = im.size
    side = min(w, h)
    if h > w:
        top = int((h - side) * 0.18)
        box = (0, top, side, top + side)
    else:
        left = (w - side) // 2
        box = (left, 0, left + side, side)
    return im.crop(box)


def main():
    if not os.path.isdir(SRC):
        os.makedirs(SRC)
        sys.exit(f"Made {SRC}. Put the original photos in there and run this again.")

    files = sorted(f for f in os.listdir(SRC)
                   if os.path.splitext(f)[1].lower() in PHOTO_EXT)
    if not files:
        sys.exit(f"No photos in {SRC}.")

    for f in files:
        name, ext = os.path.splitext(f)
        slug = name.lower().replace(" ", "-")
        src = os.path.join(SRC, f)
        dst = os.path.join(OUT, slug + ".jpg")
        if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
            print(f"   {slug}.jpg  (already done)")
            continue

        tmp = None
        if ext.lower() in (".heic", ".heif"):
            tmp = dst + ".tmp.jpg"
            if not heic_to_jpeg(src, tmp):
                print(f"   FAILED to read {f} (HEIC needs macOS)")
                continue
            src = tmp
        try:
            im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
            im = square(im).resize((SIZE, SIZE), Image.LANCZOS)
            im.save(dst, "JPEG", quality=QUALITY, optimize=True, progressive=True)
            print(f"   {slug}.jpg  {os.path.getsize(dst) / 1e3:.0f} KB")
        finally:
            if tmp and os.path.exists(tmp):
                os.remove(tmp)

    print("\nSquare copies are in images/members/. Now add each person to about.html.")


if __name__ == "__main__":
    main()
