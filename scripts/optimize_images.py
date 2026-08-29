#!/usr/bin/env python3
"""
Turn the big photos you dropped into images/<event>/ into web-sized copies.

Run it after adding photos:      python3 scripts/optimize_images.py

For every image in images/<event>/ it writes a smaller version to
images/<event>/web/. Your originals are never modified and never uploaded to
the website. Only the web/ copies are.

Handles:
  * huge camera JPEGs  -> resized to WIDTH px and recompressed
  * iPhone .HEIC files -> converted to .jpg (browsers cannot show HEIC)
  * sideways photos    -> rotated upright using the EXIF orientation tag
Videos (.mp4/.mov) are skipped. Put those on YouTube instead.
"""

import os
import subprocess
import sys
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES = os.path.join(HERE, "images")

MAX_WIDTH = 1600      # long edge, in pixels
QUALITY = 82
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".heic", ".heif"}
VIDEO_EXT = {".mp4", ".mov", ".m4v"}


def heic_to_jpeg(src, dst):
    """macOS ships `sips`, which reads HEIC. Pillow usually cannot."""
    try:
        subprocess.run(["sips", "-s", "format", "jpeg", src, "--out", dst],
                       check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def process(src, out_dir):
    name, ext = os.path.splitext(os.path.basename(src))
    ext = ext.lower()
    dst = os.path.join(out_dir, name.lower().replace(" ", "-") + ".jpg")

    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
        return "skip", dst          # already up to date

    tmp = None
    if ext in (".heic", ".heif"):
        tmp = dst + ".tmp.jpg"
        if not heic_to_jpeg(src, tmp):
            return "fail-heic", dst
        src = tmp

    try:
        im = ImageOps.exif_transpose(Image.open(src))   # fix sideways photos
        im = im.convert("RGB")
        im.thumbnail((MAX_WIDTH, MAX_WIDTH), Image.LANCZOS)
        im.save(dst, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    except Exception as e:
        return f"fail ({e})", dst
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)
    return "ok", dst


def main():
    if not os.path.isdir(IMAGES):
        sys.exit("no images/ folder found")

    total_in = total_out = 0
    for event in sorted(os.listdir(IMAGES)):
        folder = os.path.join(IMAGES, event)
        if not os.path.isdir(folder):
            continue
        out_dir = os.path.join(folder, "web")
        os.makedirs(out_dir, exist_ok=True)

        files = [f for f in sorted(os.listdir(folder))
                 if os.path.isfile(os.path.join(folder, f))
                 and not f.lower().startswith("readme")]
        if not files:
            continue

        print(f"\n{event}/")
        for f in files:
            src = os.path.join(folder, f)
            ext = os.path.splitext(f)[1].lower()
            if ext in VIDEO_EXT:
                print(f"   skipped (video, put it on YouTube)  {f}")
                continue
            if ext not in PHOTO_EXT:
                print(f"   skipped (not an image)              {f}")
                continue

            status, dst = process(src, out_dir)
            if status.startswith("fail"):
                print(f"   FAILED {status}  {f}")
                continue
            si = os.path.getsize(src)
            so = os.path.getsize(dst)
            total_in += si
            total_out += so
            w, h = Image.open(dst).size
            note = "already done" if status == "skip" else ""
            print(f"   {f:34} {si/1e6:6.1f} MB -> {so/1e6:5.2f} MB  {w}x{h} {note}")

    if total_in:
        print(f"\nTotal: {total_in/1e6:.0f} MB -> {total_out/1e6:.1f} MB "
              f"({100 - total_out/total_in*100:.0f}% smaller)")
        print("Web copies are in images/<event>/web/")


if __name__ == "__main__":
    main()
