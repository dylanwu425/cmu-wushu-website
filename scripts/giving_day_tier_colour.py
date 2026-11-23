#!/usr/bin/env python3
"""
Rebuild the colour twins of the Giving Day tier pictures.

The four cards print in the page's two colours, and the duotone is baked
into tier-N.jpg -- there is no colour left in those files to bring back.
So each one has a twin, tier-N-color.jpg, cut from the same region of the
same original at the same size, which the card fades up on hover.

The two files MUST line up pixel for pixel or the picture jumps under the
cursor. That is what this script is for: it cuts both from one set of
numbers, and then checks itself by duotoning what it just made and
comparing it against the file that shipped. Run it after touching any
crop box and read the diff it prints -- under about 10/255 means the
geometry still matches.

    /usr/local/bin/python3 scripts/giving_day_tier_colour.py

Needs Pillow and numpy, and the camera originals, which are gitignored.
Without them it exits saying which one is missing and changes nothing.
"""
import os
import sys

try:
    import numpy as np
    from PIL import Image, ImageEnhance
except ImportError:
    sys.exit("needs Pillow and numpy: /usr/local/bin/python3 -m pip install pillow numpy")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "images", "giving-day")

INK = np.array((0x1B, 0x1A, 0x17), np.float32)      # --ink
PAPER = np.array((0xEF, 0xE7, 0xD8), np.float32)    # --paper

# name: (source, crop x/y/w/h, ceiling, sharpen, gamma)
SIMPLE = {
    "tier-10":  ("images/mid-autumn-2025/PXL_20251001_231714393.jpg",
                 (850, 1285, 800, 1000), 0.86, 0.70, 1.00),
    "tier-25":  ("images/ds-2026/wushu-31.jpg",
                 (1767, 714, 940, 1175), 1.00, 0.35, 1.00),
    "tier-100": ("images/penguins-2026/DSCF6131.JPG",
                 (613, 1879, 1680, 2100), 1.00, 0.00, 0.92),
}

# The $50 is two people joined down the middle of the face: a sister on the
# left, her brother on the right, from one frame of one group doing one move.
#
# These boxes are NOT the ones in images/giving-day/README.txt. That file's
# left box was 275px off and its right box the wrong size, and a colour twin
# cut to them slid sideways under the cursor. The real ones were recovered by
# matching each half of the shipped card back against the original frame --
# correlation 0.991 for the left half and 0.985 for the right, which is as
# certain as this gets.
PAIR = ("images/penguins-2026/DSCF6013.JPG",
        (1794, 1240, 608, 1520),        # her half  -> the left 360px
        (3385,  867, 946, 2365),        # his half  -> the right 360px
        0.87, 1.18)                     # gamma, contrast
FADE = 10                               # pixels the two halves cross over


def duotone(img, ceiling=1.0, gamma=1.0, contrast=1.18):
    g = np.asarray(img.convert("L"), np.float32)
    lo, hi = np.percentile(g, 1), np.percentile(g, 99)
    g = np.clip((g - lo) / max(hi - lo, 1e-6), 0, 1) * 255.0
    g = np.clip((g - 128.0) * contrast + 128.0, 0, 255)
    if gamma != 1.0:
        g = 255.0 * (g / 255.0) ** gamma
    t = np.clip(g * ceiling / 255.0, 0, 1)[..., None]
    return Image.fromarray(np.clip(INK + (PAPER - INK) * t, 0, 255).astype(np.uint8))


def check(colour, shipped_path, **kw):
    if not os.path.exists(shipped_path):
        return "no shipped file to check against"
    a = np.asarray(duotone(colour, **kw).convert("RGB"), np.float32)
    b = np.asarray(Image.open(shipped_path).convert("RGB"), np.float32)
    return "%.1f/255" % float(np.mean(np.abs(a - b)))


def need(rel):
    p = os.path.join(HERE, rel)
    if not os.path.exists(p):
        sys.exit("missing original: %s\n(the camera files are gitignored; "
                 "nothing was written)" % rel)
    return p


def save(img, name):
    path = os.path.join(OUT, name + "-color.jpg")
    img.save(path, "JPEG", quality=82, progressive=True, optimize=True)
    return path


def main():
    for name, (src, (x, y, w, h), ceiling, sharpen, gamma) in sorted(SIMPLE.items()):
        im = Image.open(need(src)).convert("RGB")
        cut = im.crop((x, y, x + w, y + h)).resize((720, 900), Image.LANCZOS)
        if sharpen:
            cut = ImageEnhance.Sharpness(cut).enhance(1.0 + sharpen)
        save(cut, name)
        print("%-9s  drift %s" % (name, check(
            cut, os.path.join(OUT, name + ".jpg"), ceiling=ceiling, gamma=gamma)))

    src, lbox, rbox, gamma, contrast = PAIR
    im = Image.open(need(src)).convert("RGB")
    lx, ly, lw, lh = lbox
    rx, ry, rw, rh = rbox
    left = im.crop((lx, ly, lx + lw, ly + lh)).resize((360, 900), Image.LANCZOS)
    right = im.crop((rx, ry, rx + rw, ry + rh)).resize((360, 900), Image.LANCZOS)

    canvas = Image.new("RGB", (720, 900))
    canvas.paste(left, (0, 0))
    canvas.paste(right, (360, 0))
    a = np.asarray(canvas, np.float32).copy()
    la, ra = np.asarray(left, np.float32), np.asarray(right, np.float32)
    for i in range(FADE):
        col = 360 - FADE // 2 + i
        t = (i + 0.5) / FADE
        l = la[:, min(col, 359)]
        r = ra[:, max(col - 360, 0)]
        a[:, col] = l * (1 - t) + r * t
    canvas = Image.fromarray(a.astype(np.uint8))
    save(canvas, "tier-50")
    print("%-9s  drift %s" % ("tier-50", check(
        canvas, os.path.join(OUT, "tier-50.jpg"), gamma=gamma, contrast=contrast)))


if __name__ == "__main__":
    main()
