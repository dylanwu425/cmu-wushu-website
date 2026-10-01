#!/usr/bin/env python3
"""
Build the Members list on the About page from the sign-up form.

The form is "CMU Wushu Club — Member Profile" (a Google Form). Its answers
land in a Google Sheet, and its photo uploads land in a Drive folder. Once a
semester, or whenever new people sign up:

  1. In the Sheet: File -> Download -> Comma-separated values (.csv).
     Save it as   data/members.csv   (this file is never published: it holds
     email addresses).
  2. Photos. If Google Drive for Desktop is installed and signed in to the
     account that owns the form, there is nothing to do: the script reads the
     uploads straight from the form's "File responses" folder. Otherwise
     download that folder from Drive and put the photos in
     images/members/originals/   (HEIC fine). Google names each upload
     "<original name> - <Their name>.<ext>", which is how this script knows
     whose photo is whose.
  3. Run:   python3 scripts/build_members.py

Choosing and framing a photo: by default each person gets their "Photo 1",
cropped square around the middle (towards the top for tall photos). To use
their second photo, or to frame it differently, add them to
data/member-photos.json, keyed by the Full name they typed in the form:

    { "Jane Doe": { "photo": 2, "focus": [0.45, 0.6], "zoom": 1.3 } }

  photo   1 or 2: which upload to use
  focus   where the middle of the square should sit, as fractions of the
          photo's width and height (0,0 is the top left, 1,1 the bottom right)
  zoom    1 keeps as much as fits; 1.5 crops in by half again

It then:
  * keeps only people whose "Photo consent" answer says they consent,
  * crops each person's photo to a 480 x 480 square in images/members/
    (the originals are never published),
  * rewrites the list in about.html between the MEMBERS:START / MEMBERS:END
    markers. Everything outside those markers is left alone.

To take someone off: delete their row from the CSV (or ask them to re-submit
without consent), delete their photo, run this again.
"""

import csv
import glob
import html
import json
import os
import re
import subprocess
import sys
from PIL import Image, ImageOps

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(HERE, "data", "members.csv")
ORIGINALS = os.path.join(HERE, "images", "members", "originals")
OUT = os.path.join(HERE, "images", "members")
ABOUT = os.path.join(HERE, "about.html")
FRAMING = os.path.join(HERE, "data", "member-photos.json")
# Where Google Drive for Desktop shows the form's uploads, one folder per
# upload question ("Photo 1! (File responses)", "Photo 2! ...").
DRIVE_UPLOADS = os.path.join(
    os.path.expanduser("~"), "Library", "CloudStorage", "GoogleDrive-*", "My Drive",
    "CMU Wushu Club* Member Profile (File responses)", "Photo * (File responses)")
START, END = "<!-- MEMBERS:START -->", "<!-- MEMBERS:END -->"
SIZE = 480
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".webp"}

# Column headings in the sheet, matched loosely so small edits to the form
# don't break this. Each entry: our key -> words the heading must contain.
COLUMNS = {
    "full": ("full name",),
    "nick": ("preferred",),
    "year": ("year / class",),
    "major": ("major",),
    "bio": ("fun fact",),
    "insta": ("instagram",),
    "consent": ("consent",),
    "since": ("what year did you start",),
}


def find_columns(headings):
    found = {}
    for key, words in COLUMNS.items():
        for h in headings:
            low = h.lower()
            if all(w in low for w in words):
                found[key] = h
                break
    return found


def clean_name(nick, full):
    """The preferred name, minus any joke in brackets; the full name if blank."""
    name = (nick or "").strip()
    name = re.sub(r"\s*[\(\[].*$", "", name).strip()
    return name or full.strip()


def initials(name):
    parts = [p for p in re.split(r"\s+", name) if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def slug(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "member"


def tidy_meta(year, major):
    """'Social Work/Freshman/University of Pittsburgh' -> 'Freshman · Social Work · University of Pittsburgh'.
    The form's free-text field can hold anything, so this only tidies the
    separators; it does not try to be clever about order."""
    bits = [b.strip() for b in re.split(r"\s*[/·|,]\s*", major or "") if b.strip()]
    if year and year.strip() and year.strip().lower() not in [b.lower() for b in bits]:
        bits.insert(0, year.strip())
    return " · ".join(bits)


def heic_to_jpeg(src, dst):
    try:
        subprocess.run(["sips", "-s", "format", "jpeg", src, "--out", dst],
                       check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def square(im, focus=None, zoom=1.0):
    """Crop to a square. With no focus, tall photos keep the top (faces live
    there) and wide photos keep the middle. With a focus, the square is
    centred there, as close as the photo's edges allow."""
    w, h = im.size
    side = int(min(w, h) / max(zoom, 1.0))
    if focus:
        cx, cy = focus[0] * w, focus[1] * h
    elif h > w:
        cx, cy = w / 2, (h - side) * 0.18 + side / 2
    else:
        cx, cy = w / 2, h / 2
    left = int(min(max(cx - side / 2, 0), w - side))
    top = int(min(max(cy - side / 2, 0), h - side))
    return im.crop((left, top, left + side, top + side))


def upload_folders():
    """Folders to look for uploads in, in order: the form's own folders in
    Drive ("Photo 1!" before "Photo 2!"), then images/members/originals/."""
    folders = sorted(glob.glob(DRIVE_UPLOADS))
    if os.path.isdir(ORIGINALS):
        folders.append(ORIGINALS)
    return folders


def find_photos(full_name):
    """Every upload whose file name ends in ' - <name>', where the name's
    first and last words match the person's, in upload order. Google names
    uploads after the uploader's Google account, which may drop a middle
    name."""
    want = [w for w in re.split(r"\s+", full_name.strip().lower()) if w]
    if not want:
        return []
    found = []
    for folder in upload_folders():
        for f in sorted(os.listdir(folder)):
            stem, ext = os.path.splitext(f)
            if ext.lower() not in PHOTO_EXT:
                continue
            m = re.search(r" - (.+)$", stem)
            if not m:
                continue
            got = [w for w in re.split(r"\s+", m.group(1).strip().lower()) if w]
            if got and got[0] == want[0] and got[-1] == want[-1]:
                found.append(os.path.join(folder, f))
    return found


def load_framing():
    if not os.path.exists(FRAMING):
        return {}
    try:
        data = json.load(open(FRAMING, encoding="utf-8"))
    except ValueError as e:
        sys.exit(f"data/member-photos.json is not valid JSON: {e}")
    return {k.strip().lower(): v for k, v in data.items() if not k.startswith("_")}


def make_square(src, dst, focus=None, zoom=1.0):
    # Framed photos are always redone, so a change to member-photos.json
    # shows up; plain ones are skipped when the copy is already newer.
    plain = focus is None and zoom == 1.0
    if plain and os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
        return True
    tmp = None
    if os.path.splitext(src)[1].lower() in (".heic", ".heif"):
        tmp = dst + ".tmp.jpg"
        if not heic_to_jpeg(src, tmp):
            return False
        src = tmp
    try:
        im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
        square(im, focus, zoom).resize((SIZE, SIZE), Image.LANCZOS).save(
            dst, "JPEG", quality=84, optimize=True, progressive=True)
        return True
    except Exception as e:
        print(f"   could not read {os.path.basename(src)}: {e}")
        return False
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)


def esc(s):
    return html.escape((s or "").strip(), quote=True)


def card(person):
    name = esc(person["name"])
    lines = ["          <li class=\"member\">"]
    if person.get("photo"):
        lines.append(f"            <img class=\"member__photo\" src=\"images/members/{person['photo']}\"")
        lines.append(f"                 alt=\"\" loading=\"lazy\" width=\"{SIZE}\" height=\"{SIZE}\">")
    else:
        lines.append(f"            <span class=\"member__seal\" aria-hidden=\"true\">{esc(person['initials'])}</span>")
    lines.append(f"            <h3>{name}</h3>")
    if person.get("meta"):
        lines.append(f"            <p class=\"member__meta\">{esc(person['meta'])}</p>")
    if person.get("since"):
        lines.append(f"            <p class=\"member__since\">Since {esc(person['since'])}</p>")
    if person.get("bio"):
        lines.append(f"            <p class=\"member__bio\">{esc(person['bio'])}</p>")
    if person.get("insta"):
        handle = person["insta"].lstrip("@")
        lines.append(f"            <p class=\"member__insta\"><a href=\"https://www.instagram.com/{esc(handle)}/\" target=\"_blank\" rel=\"noopener\">@{esc(handle)}</a></p>")
    lines.append("          </li>")
    return "\n".join(lines)


def main():
    if not os.path.exists(CSV):
        sys.exit(f"No {CSV}. Download the responses sheet as CSV and save it there first.")

    with open(CSV, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        sys.exit("The CSV has no rows.")
    cols = find_columns(rows[0].keys())
    for need in ("full", "consent"):
        if need not in cols:
            sys.exit(f"Could not find the '{COLUMNS[need][0]}' column in the CSV.")

    framing = load_framing()
    people, skipped = [], []
    seen = set()
    for row in reversed(rows):           # newest answer wins if someone resubmits
        full = (row.get(cols["full"]) or "").strip()
        if not full or full.lower() in seen:
            continue
        seen.add(full.lower())
        if "consent" not in (row.get(cols["consent"]) or "").lower() or \
           "do not" in (row.get(cols["consent"]) or "").lower() or \
           "don't" in (row.get(cols["consent"]) or "").lower():
            skipped.append(full)
            continue
        name = clean_name(row.get(cols.get("nick", ""), ""), full)
        person = {
            "name": name,
            "initials": initials(name),
            "meta": tidy_meta(row.get(cols.get("year", ""), ""), row.get(cols.get("major", ""), "")),
            "since": re.sub(r"\D", "", row.get(cols.get("since", ""), "") or "")[:4],
            "bio": (row.get(cols.get("bio", ""), "") or "").strip(),
            "insta": (row.get(cols.get("insta", ""), "") or "").strip(),
        }
        photos = find_photos(full)
        if photos:
            frame = framing.get(full.lower(), {})
            pick = min(max(int(frame.get("photo", 1)), 1), len(photos)) - 1
            dst = os.path.join(OUT, slug(name) + ".jpg")
            if make_square(photos[pick], dst, frame.get("focus"), float(frame.get("zoom", 1.0))):
                person["photo"] = os.path.basename(dst)
        people.append(person)
    people.sort(key=lambda p: p["name"].lower())

    page = open(ABOUT, encoding="utf-8").read()
    if START not in page or END not in page:
        sys.exit("about.html is missing the MEMBERS:START / MEMBERS:END markers.")
    body = "\n".join(card(p) for p in people) if people else \
        "          <!-- nobody yet: the list fills in as members sign up -->"
    before = page[:page.index(START) + len(START)]
    after = page[page.index(END):]
    new = before + "\n" + body + "\n          " + after
    if new != page:
        open(ABOUT, "w", encoding="utf-8").write(new)
        print(f"about.html updated: {len(people)} member(s) listed.")
    else:
        print(f"No change: {len(people)} member(s) already listed.")
    with_photo = sum(1 for p in people if p.get("photo"))
    print(f"   {with_photo} with a photo, {len(people) - with_photo} with a seal.")
    if skipped:
        print(f"   Left off (no consent): {', '.join(skipped)}")


if __name__ == "__main__":
    main()
