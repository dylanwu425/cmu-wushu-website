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

It then:
  * keeps only people whose "Photo consent" answer says they consent,
  * leaves out anyone who already has an officer card on the page,
  * crops each person's photos to 600 x 800 (the officer cards' shape) in
    images/members/ (the originals are never published),
  * rewrites the list in about.html between the MEMBERS:START / MEMBERS:END
    markers. Everything outside those markers is left alone.

Two photos per person. Each card shows a FORMAL photo, and swaps to an
INFORMAL one when you hover over it (or tap it on a phone). By default the
formal photo is their "Photo 1" and the informal one their "Photo 2"; someone
with one upload just gets the one photo, and someone with none gets a red
seal with their initials.

To swap the two, or frame either one differently, add the person to
data/member-photos.json, keyed by the Full name they typed in the form:

    { "Jane Doe": {
        "formal":   { "photo": 2, "focus": [0.45, 0.6], "zoom": 1.2 },
        "informal": { "photo": 1 }
    } }

  photo   1 or 2: which upload to use
  focus   where the middle of the crop should sit, as fractions of the
          photo's width and height (0,0 is the top left, 1,1 the bottom right)
  zoom    1 keeps as much as fits; 1.5 crops in by half again

To take someone off: delete their row from the CSV (or ask them to re-submit
without consent), run this again, and push.
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
WIDTH, HEIGHT = 600, 800          # the officer cards' 3:4 portrait
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
    for key, needed in COLUMNS.items():
        for h in headings:
            low = h.lower()
            if all(w in low for w in needed):
                found[key] = h
                break
    return found


def words(name):
    return [w for w in re.split(r"\s+", (name or "").strip().lower()) if w]


def same_person(a, b):
    """First and last words match: 'Kaden Dan Wong' is 'Kaden Wong'."""
    a, b = words(a), words(b)
    return bool(a and b and a[0] == b[0] and a[-1] == b[-1])


def clean_name(nick, full):
    """The preferred name, minus any joke in brackets; the full name if blank."""
    name = (nick or "").strip()
    name = re.sub(r"\s*[\(\[].*$", "", name).strip()
    return name or full.strip()


def initials(name):
    parts = words(name)
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def slug(name):
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "member"


def tidy_meta(year, major):
    """'Social Work/Freshman/University of Pittsburgh' ->
    'Social Work · Freshman · University of Pittsburgh'. The form's free-text
    field can hold anything, so this only tidies the separators."""
    bits = [b.strip() for b in re.split(r"\s*[/·|,]\s*", major or "") if b.strip()]
    if year and year.strip() and year.strip().lower() not in [b.lower() for b in bits]:
        bits.insert(0, year.strip())
    return " · ".join(bits)


def heic_to_jpeg(src, dst):
    """macOS ships `sips`, which reads HEIC. Pillow usually cannot."""
    try:
        subprocess.run(["sips", "-s", "format", "jpeg", src, "--out", dst],
                       check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def portrait(im, focus=None, zoom=1.0):
    """Crop to the cards' 3:4 shape. With no focus the crop sits in the
    middle, a little above centre for tall photos (faces live there). With a
    focus it is centred there, as close as the photo's edges allow."""
    w, h = im.size
    ratio = WIDTH / HEIGHT
    cw = min(w, h * ratio) / max(zoom, 1.0)
    ch = cw / ratio
    if focus:
        cx, cy = focus[0] * w, focus[1] * h
    else:
        cx, cy = w / 2, ch / 2 + (h - ch) * (0.3 if h / w > 1 / ratio else 0.5)
    left = int(min(max(cx - cw / 2, 0), w - cw))
    top = int(min(max(cy - ch / 2, 0), h - ch))
    return im.crop((left, top, left + int(cw), top + int(ch)))


def upload_folders():
    """Folders to look for uploads in, in order: the form's own folders in
    Drive ("Photo 1!" before "Photo 2!"), then images/members/originals/."""
    folders = sorted(glob.glob(DRIVE_UPLOADS))
    if os.path.isdir(ORIGINALS):
        folders.append(ORIGINALS)
    return folders


def find_photos(full_name):
    """Every upload named ' - <their name>', in upload order. Google names
    uploads after the uploader's Google account, which may drop a middle
    name, so only the first and last words have to match."""
    found = []
    for folder in upload_folders():
        for f in sorted(os.listdir(folder)):
            stem, ext = os.path.splitext(f)
            if ext.lower() not in PHOTO_EXT:
                continue
            m = re.search(r" - (.+)$", stem)
            if m and same_person(m.group(1), full_name):
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


def make_portrait(src, dst, focus=None, zoom=1.0):
    tmp = None
    if os.path.splitext(src)[1].lower() in (".heic", ".heif"):
        tmp = dst + ".tmp.jpg"
        if not heic_to_jpeg(src, tmp):
            return False
        src = tmp
    try:
        im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
        portrait(im, focus, zoom).resize((WIDTH, HEIGHT), Image.LANCZOS).save(
            dst, "JPEG", quality=84, optimize=True, progressive=True)
        return True
    except Exception as e:
        print(f"   could not read {os.path.basename(src)}: {e}")
        return False
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)


def officer_names(page):
    """Names on the officer cards, so officers aren't listed twice."""
    head = page[:page.index(START)] if START in page else page
    return re.findall(r'<article class="card officer"[^>]*>.*?<h3>(.*?)</h3>', head, flags=re.S)


def esc(s):
    return html.escape((s or "").strip(), quote=True)


def card(person):
    name = esc(person["name"])
    out = ['          <li class="card officer member">']
    formal, informal = person.get("formal"), person.get("informal")
    if formal and informal:
        out.append('            <button class="member__photos" type="button" aria-pressed="false"')
        out.append(f'                    aria-label="Show {name}&rsquo;s other photo">')
        out.append(f'              <img class="member__photo" src="images/members/{formal}"')
        out.append(f'                   alt="{name}" loading="lazy" width="{WIDTH}" height="{HEIGHT}">')
        out.append(f'              <img class="member__photo member__photo--informal" src="images/members/{informal}"')
        out.append(f'                   alt="" loading="lazy" width="{WIDTH}" height="{HEIGHT}">')
        out.append('            </button>')
    elif formal:
        out.append(f'            <img class="member__photo" src="images/members/{formal}"')
        out.append(f'                 alt="{name}" loading="lazy" width="{WIDTH}" height="{HEIGHT}">')
    else:
        out.append(f'            <span class="member__seal" aria-hidden="true">{esc(person["initials"])}</span>')
    out.append(f'            <h3>{name}</h3>')
    if person.get("since"):
        out.append(f'            <p><strong>Member since {esc(person["since"])}</strong></p>')
    else:
        out.append('            <p><strong>Member</strong></p>')
    if person.get("meta"):
        out.append(f'            <p class="card__meta">{esc(person["meta"])}</p>')
    if person.get("bio"):
        out.append(f'            <p>{esc(person["bio"])}</p>')
    if person.get("insta"):
        handle = esc(person["insta"].lstrip("@"))
        out.append(f'            <p class="member__insta"><a href="https://www.instagram.com/{handle}/" target="_blank" rel="noopener">@{handle}</a></p>')
    out.append('          </li>')
    return "\n".join(out)


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

    page = open(ABOUT, encoding="utf-8").read()
    if START not in page or END not in page:
        sys.exit("about.html is missing the MEMBERS:START / MEMBERS:END markers.")
    officers = officer_names(page)
    framing = load_framing()

    def cell(row, key):
        return (row.get(cols.get(key, ""), "") or "").strip()

    people, no_consent, are_officers = [], [], []
    seen = []
    for row in reversed(rows):           # newest answer wins if someone resubmits
        full = cell(row, "full")
        if not full or any(same_person(full, s) for s in seen):
            continue
        seen.append(full)
        consent = cell(row, "consent").lower()
        if "consent" not in consent or "do not" in consent or "don't" in consent:
            no_consent.append(full)
            continue
        name = clean_name(cell(row, "nick"), full)
        if any(same_person(full, o) or same_person(name, o) for o in officers):
            are_officers.append(full)
            continue

        person = {
            "name": name,
            "initials": initials(name),
            "meta": tidy_meta(cell(row, "year"), cell(row, "major")),
            "since": re.sub(r"\D", "", cell(row, "since"))[:4],
            "bio": cell(row, "bio"),
            "insta": cell(row, "insta"),
        }
        photos = find_photos(full)
        frame = framing.get(full.lower(), {})
        defaults = {"formal": 1, "informal": 2}
        used = set()
        for kind in ("formal", "informal"):
            want = frame.get(kind, {})
            pick = int(want.get("photo", defaults[kind]))
            if pick < 1 or pick > len(photos) or pick in used:
                continue
            used.add(pick)
            dst = os.path.join(OUT, f"{slug(name)}-{kind}.jpg")
            if make_portrait(photos[pick - 1], dst, want.get("focus"), float(want.get("zoom", 1.0))):
                person[kind] = os.path.basename(dst)
        if person.get("informal") and not person.get("formal"):
            person["formal"] = person.pop("informal")
        people.append(person)
    people.sort(key=lambda p: p["name"].lower())

    body = "\n".join(card(p) for p in people) if people else \
        "          <!-- nobody yet: the list fills in as members sign up -->"
    before = page[:page.index(START) + len(START)]
    after = page[page.index(END):]
    new = before + "\n" + body + "\n          " + after
    if new != page:
        open(ABOUT, "w", encoding="utf-8").write(new)
        print(f"about.html updated: {len(people)} member(s) listed.")
    else:
        print(f"No change to about.html: {len(people)} member(s) listed.")
    two = sum(1 for p in people if p.get("informal"))
    one = sum(1 for p in people if p.get("formal") and not p.get("informal"))
    print(f"   {two} with two photos, {one} with one, {len(people) - two - one} with a seal.")
    if no_consent:
        print(f"   Left off (no consent): {', '.join(no_consent)}")
    if are_officers:
        print(f"   Left off (already an officer card): {', '.join(are_officers)}")


if __name__ == "__main__":
    main()
