#!/usr/bin/env python3
"""
Build the Members list on the About page from the sign-up form.

The form is "CMU Wushu Club — Member Profile" (a Google Form). Its answers
land in a Google Sheet, and its photo uploads land in a Drive folder. Once a
semester, or whenever new people sign up:

  1. In the Sheet: File -> Download -> Comma-separated values (.csv).
     Save it as   data/members.csv   (this file is never published: it holds
     email addresses).
  2. In Drive, open the form's "File responses" folder, download it, and put
     the photos in   images/members/originals/   (any names, HEIC fine).
     Google names each upload "<original name> - <Their name>.<ext>", which
     is how this script knows whose photo is whose.
  3. Run:   python3 scripts/build_members.py

It then:
  * keeps only people whose "Photo consent" answer says they consent,
  * crops each person's first photo to a 480 x 480 square in images/members/
    (the originals stay on your computer only),
  * rewrites the list in about.html between the MEMBERS:START / MEMBERS:END
    markers. Everything outside those markers is left alone.

To take someone off: delete their row from the CSV (or ask them to re-submit
without consent), delete their photo, run this again.
"""

import csv
import html
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


def square(im):
    w, h = im.size
    side = min(w, h)
    if h > w:
        top = int((h - side) * 0.18)   # keep the top: faces live there
        return im.crop((0, top, side, top + side))
    left = (w - side) // 2
    return im.crop((left, 0, left + side, side))


def find_photo(full_name):
    """The first upload whose file name ends in ' - <name>', where the name's
    first and last words match the person's. Google names uploads after the
    uploader's Google account, which may drop a middle name."""
    if not os.path.isdir(ORIGINALS):
        return None
    want = [w for w in re.split(r"\s+", full_name.strip().lower()) if w]
    if not want:
        return None
    for f in sorted(os.listdir(ORIGINALS)):
        stem, ext = os.path.splitext(f)
        if ext.lower() not in PHOTO_EXT:
            continue
        m = re.search(r" - (.+)$", stem)
        if not m:
            continue
        got = [w for w in re.split(r"\s+", m.group(1).strip().lower()) if w]
        if got and got[0] == want[0] and got[-1] == want[-1]:
            return os.path.join(ORIGINALS, f)
    return None


def make_square(src, dst):
    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
        return True
    tmp = None
    if os.path.splitext(src)[1].lower() in (".heic", ".heif"):
        tmp = dst + ".tmp.jpg"
        if not heic_to_jpeg(src, tmp):
            return False
        src = tmp
    try:
        im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
        square(im).resize((SIZE, SIZE), Image.LANCZOS).save(
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
    os.makedirs(ORIGINALS, exist_ok=True)

    with open(CSV, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        sys.exit("The CSV has no rows.")
    cols = find_columns(rows[0].keys())
    for need in ("full", "consent"):
        if need not in cols:
            sys.exit(f"Could not find the '{COLUMNS[need][0]}' column in the CSV.")

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
        src = find_photo(full)
        if src:
            dst = os.path.join(OUT, slug(name) + ".jpg")
            if make_square(src, dst):
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
