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

Someone who never filled the form in, but told an officer their details and
said yes to being listed, goes in data/members-extra.json instead. Both lists
are merged; if a person is in both, their own form answers win.

It then:
  * keeps only people whose "Photo consent" answer says they consent,
  * leaves out anyone who already has an officer card on the page,
  * crops each person's photos to 600 x 800 (the officer cards' shape) in
    images/members/ (the originals are never published),
  * rewrites the list in about.html between the MEMBERS:START / MEMBERS:END
    markers, longest-standing members first. Everything outside those markers
    is left alone.

Two photos per person. Each card shows their INFORMAL photo, and swaps to
the FORMAL one when you hover over it (or tap it on a phone). By default the
formal photo is their "Photo 1" and the informal one their "Photo 2"; someone
with one upload just gets the one photo, and someone with none gets a red
seal with their initials.

A member can also hide a photo behind one word of their bio, the way the
word "beans" works on Preston's officer card: give them a "secret" block in
members-extra.json with the word, the photo's file name in
images/members/originals/, and its description.

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
EXTRA = os.path.join(HERE, "data", "members-extra.json")
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
    """First and last words match: 'Kaden Dan Wong' is 'Kaden Wong'. A surname
    given as an initial counts too, because Google names an upload after the
    account that sent it: 'Austin L.' is 'Austin Lin'."""
    a, b = words(a), words(b)
    if not a or not b or a[0] != b[0]:
        return False
    last_a, last_b = a[-1].rstrip("."), b[-1].rstrip(".")
    if last_a == last_b:
        return True
    if len(last_a) == 1 or len(last_b) == 1:
        return last_a[:1] == last_b[:1]
    return False


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


# Nearly everyone is at CMU, so saying so on every card is noise. Anyone
# from anywhere else keeps their school.
HOME_SCHOOL = re.compile(r"^(cmu|carnegie\s*mellon(\s+university)?)$", re.I)

# How far through school someone is. The officer cards all read year first
# ("Sophomore · ECE"), so members match them, and the list puts the most
# senior first among people who joined the club in the same year. The
# patterns are tried in this order, so "1st year master's" counts as a
# master's rather than a first year.
SCHOOL_YEARS = [
    (re.compile(r"\balum(ni|nus|na)?\b", re.I), 8),
    (re.compile(r"\b(phd|doctoral)\b", re.I), 7),
    (re.compile(r"\b(master'?s?|grad(uate)?)\b", re.I), 6),
    (re.compile(r"\b(fifth|5th)[\s-]*year\b", re.I), 5),
    (re.compile(r"\b(senior|fourth[\s-]*year|4th[\s-]*year)\b", re.I), 4),
    (re.compile(r"\b(junior|third[\s-]*year|3rd[\s-]*year)\b", re.I), 3),
    (re.compile(r"\b(sophomore|second[\s-]*year|2nd[\s-]*year)\b", re.I), 2),
    (re.compile(r"\b(freshman|frosh|first[\s-]*year|1st[\s-]*year)\b", re.I), 1),
]


# A year said first and then the rest, with nothing between them:
# "Freshman Lion dance" is a freshman who does lion dance.
LEADING_YEAR = re.compile(
    r"^((?:first|second|third|fourth|fifth|1st|2nd|3rd|4th|5th)[\s-]*year(?:\s+master'?s?)?"
    r"|freshman|frosh|sophomore|junior|senior|master'?s?|grad(?:uate)?|phd)\s+(.+)$", re.I)


def school_year(text):
    """How far through school a line like 'Freshman · Social Work' says they
    are, as a number. 0 when it does not say."""
    for pattern, rank in SCHOOL_YEARS:
        if pattern.search(text or ""):
            return rank
    return 0


def tidy_meta(*parts):
    """Join whatever the form or members-extra.json gives into one line:
    'Social Work/Freshman/University of Pittsburgh' becomes
    'Social Work · Freshman · University of Pittsburgh', and 'Junior', 'BXA',
    'CMU' becomes 'Junior · BXA'. Only separators are tidied; nothing is
    reordered, because the free-text field can hold anything."""
    bits = []
    for part in parts:
        text = (part or "").strip()
        if not text:
            continue
        if re.search(r"[/·|,]", text):
            pieces = re.split(r"\s*[/·|,]\s*", text)
        else:
            # Written as a sentence: "Senior in Electrical and Computer
            # Engineering at Carnegie Mellon University".
            school = None
            at = re.search(r"\s+at\s+(.+)$", text, re.I)
            if at:
                school, text = at.group(1).strip(), text[:at.start()].strip()
            isin = re.match(r"^(.+?)\s+in\s+(.+)$", text, re.I)
            if isin:
                pieces = [isin.group(1), isin.group(2)]
            else:
                lead = LEADING_YEAR.match(text)
                pieces = [lead.group(1), lead.group(2)] if lead else [text]
            if school:
                pieces.append(school)
        for bit in pieces:
            bit = bit.strip()
            if bit and not HOME_SCHOOL.match(bit) and \
               bit.lower() not in [b.lower() for b in bits]:
                bits.append(bit)
    # Year first, whatever order they wrote it in, so every card reads the
    # same way: "Freshman · Social Work · University of Pittsburgh".
    for i, bit in enumerate(bits):
        if school_year(bit):
            bits.insert(0, bits.pop(i))
            break
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


def load_extra():
    """Members who never filled the form in. The officer who added them is
    saying they consented, so there is no consent column to check here."""
    if not os.path.exists(EXTRA):
        return []
    try:
        data = json.load(open(EXTRA, encoding="utf-8"))
    except ValueError as e:
        sys.exit(f"data/members-extra.json is not valid JSON: {e}")
    return [m for m in data.get("members", []) if m.get("name")]


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


def make_web(src, dst, max_side=1200):
    """A photo kept whole, only made small enough for the web. Used for the
    secret photo behind a word in someone's bio, which is shown full-size in
    the viewer rather than cropped to a card."""
    tmp = None
    if os.path.splitext(src)[1].lower() in (".heic", ".heif"):
        tmp = dst + ".tmp.jpg"
        if not heic_to_jpeg(src, tmp):
            return False
        src = tmp
    try:
        im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
        im.thumbnail((max_side, max_side), Image.LANCZOS)
        im.save(dst, "JPEG", quality=84, optimize=True, progressive=True)
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


def bio_html(person):
    """Their bio, escaped, with the secret word (if they have one) turned into
    a button. The button is styled to read as ordinary text, so the only way
    to find it is to click the word."""
    bio = esc(person["bio"])
    secret = person.get("secret") or {}
    word = (secret.get("word") or "").strip()
    if not word or not secret.get("file"):
        return bio
    pattern = re.compile(r"\b(" + re.escape(esc(word)) + r")\b", re.I)
    swapped, hits = pattern.subn(
        '<button class="secret-trigger" type="button">\\1</button>', bio, count=1)
    if not hits:
        print(f"   {person['name']}: \"{word}\" is not in their bio, so nothing is hidden there")
        return bio
    secret["found"] = True
    return swapped


def card(person):
    name = esc(person["name"])
    out = ['          <li class="card officer member">']
    # The informal photo is the one that shows; the formal one is behind it.
    first = person.get("informal") or person.get("formal")
    second = person.get("formal") if person.get("informal") else None
    if first and second:
        out.append('            <button class="photo-swap" type="button" aria-pressed="false"')
        out.append(f'                    aria-label="Show {name}&rsquo;s other photo">')
        out.append(f'              <img class="photo-swap__img" src="images/members/{first}"')
        out.append(f'                   alt="{name}" loading="lazy" width="{WIDTH}" height="{HEIGHT}">')
        out.append(f'              <img class="photo-swap__img photo-swap__img--alt" src="images/members/{second}"')
        out.append(f'                   alt="" loading="lazy" width="{WIDTH}" height="{HEIGHT}">')
        out.append('            </button>')
    elif first:
        out.append(f'            <img class="member__photo" src="images/members/{first}"')
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
        out.append(f'            <p>{bio_html(person)}</p>')
        secret = person.get("secret")
        if secret and secret.get("file") and secret.get("found"):
            out.append(f'            <img class="secret-photo" src="images/members/{secret["file"]}"')
            out.append(f'                 alt="{esc(secret.get("alt", ""))}" loading="lazy" hidden>')
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

    people, no_consent, are_officers, in_form = [], [], [], []
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
        # The card shows the informal photo, and people upload that one first.
        defaults = {"informal": 1, "formal": 2}
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
        people.append(person)

    # Anyone who never filled the form in, added by an officer instead. Their
    # photos are named outright rather than picked out of the form's uploads.
    for entry in load_extra():
        full = entry["name"].strip()
        if any(same_person(full, p["name"]) for p in people):
            in_form.append(full)
            continue
        if any(same_person(full, o) for o in officers):
            are_officers.append(full)
            continue
        name = clean_name(entry.get("preferred", ""), full)
        person = {
            "name": name,
            "initials": initials(name),
            "meta": tidy_meta(entry.get("year"), entry.get("major"), entry.get("school")),
            "since": re.sub(r"\D", "", str(entry.get("since", "")))[:4],
            "bio": (entry.get("bio") or "").strip(),
            "insta": (entry.get("insta") or "").strip(),
        }
        secret = entry.get("secret") or {}
        if secret.get("word") and secret.get("photo"):
            src = os.path.join(ORIGINALS, secret["photo"])
            if os.path.exists(src):
                dst = os.path.join(OUT, f"{slug(name)}-secret.jpg")
                if make_web(src, dst):
                    person["secret"] = {"word": secret["word"],
                                        "alt": secret.get("alt", ""),
                                        "file": os.path.basename(dst)}
            else:
                print(f"   {full}: no secret photo at images/members/originals/{secret['photo']}")
        frame = framing.get(full.lower(), {})
        for kind, filename in (entry.get("photos") or {}).items():
            if kind not in ("formal", "informal") or not filename:
                continue
            src = os.path.join(ORIGINALS, filename)
            if not os.path.exists(src):
                print(f"   {full}: no {kind} photo at images/members/originals/{filename}")
                continue
            want = frame.get(kind, {})
            dst = os.path.join(OUT, f"{slug(name)}-{kind}.jpg")
            if make_portrait(src, dst, want.get("focus"), float(want.get("zoom", 1.0))):
                person[kind] = os.path.basename(dst)
        people.append(person)

    # Longest-standing members first; anyone without a joining year goes
    # last. Within a year the most senior at school comes first, and people
    # at the same point are listed alphabetically.
    people.sort(key=lambda p: (int(p["since"]) if p["since"] else 9999,
                               -school_year(p["meta"]),
                               p["name"].lower()))

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
    two = sum(1 for p in people if p.get("informal") and p.get("formal"))
    one = sum(1 for p in people if bool(p.get("informal")) != bool(p.get("formal")))
    print(f"   {two} with two photos, {one} with one, {len(people) - two - one} with a seal.")
    if no_consent:
        print(f"   Left off (no consent): {', '.join(no_consent)}")
    if are_officers:
        print(f"   Left off (already an officer card): {', '.join(are_officers)}")
    if in_form:
        print(f"   In members-extra.json but also in the form, so the form won: "
              f"{', '.join(in_form)}. You can delete them from members-extra.json.")


if __name__ == "__main__":
    main()
