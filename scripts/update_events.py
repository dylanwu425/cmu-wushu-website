#!/usr/bin/env python3
"""
Regenerate the Events page from the club's Google Calendar.

Run it by hand:      python3 scripts/update_events.py
Check without saving: python3 scripts/update_events.py --dry-run

It rewrites ONLY the two regions of events.html marked with
    <!-- AUTO:UPCOMING:START -->  ...  <!-- AUTO:UPCOMING:END -->
    <!-- AUTO:PAST:START -->      ...  <!-- AUTO:PAST:END -->
Anything outside those markers is left alone, so it is safe to hand-edit
the rest of the page.

Two deliberate safety rules:
  1. Calendar DESCRIPTION fields are NEVER published. They contain call
     times, Google Meet links, and phone PINs. Blurbs come from
     event-notes.json instead.
  2. Internal logistics (rehearsals, board meetings, elections, rides)
     are filtered out. See SKIP below.
"""

import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone, date
from zoneinfo import ZoneInfo

# --- Settings ---------------------------------------------------------------
CALENDAR_ID = ("c_8aa0bdc408d466c07426d4b7d5e539cf241c08fd655c2d4a1017ea10b79f820c"
               "%40group.calendar.google.com")
ICS_URL = f"https://calendar.google.com/calendar/ical/{CALENDAR_ID}/public/basic.ics"
TZ = ZoneInfo("America/New_York")

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(HERE, "events.html")
NOTES = os.path.join(HERE, "event-notes.json")
EXTRAS = os.path.join(HERE, "event-extras.json")

MAX_UPCOMING = 6      # cards shown under "Upcoming events"

# Events we never publish: internal logistics, not public happenings.
SKIP = re.compile(r"rehearsal|stage blocking|pickup and drive|arrive and meet"
                  r"|prepare \(|board meeting|elections|practice|tricking", re.I)

# Word -> tag class + label shown on the card.
TAGS = [
    (re.compile(r"fair|orientation", re.I),          ("tag--social", "Outreach")),
    (re.compile(r"movie|avatar night|dinner|social", re.I), ("tag--social", "Social")),
    (re.compile(r"belt test|gbm|meeting", re.I),     ("tag--social", "Club")),
    (re.compile(r"sampler|workshop", re.I),          ("tag--social", "Workshop")),
    (re.compile(r"competition|tournament|collegiate", re.I),
                                                     ("tag--competition", "Competition")),
]
DEFAULT_TAG = ("tag--performance", "Performance")

ROOMS = {"KENNER": "Kenner", "KEELER": "Keeler", "ACTIVITIES": "Activities Room",
         "RANGOS": "Rangos", "MCCONOMY": "McConomy Auditorium",
         "WIEGAND": "Wiegand Gym", "STUDIO THEATER": "Studio Theater"}


# --- Parsing ----------------------------------------------------------------
def fetch_ics(url):
    req = urllib.request.Request(url, headers={"User-Agent": "cmu-wushu-site/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def parse_events(raw):
    """Return [{start: datetime, title, location, recurring: bool}] in Eastern."""
    raw = re.sub(r"\r?\n[ \t]", "", raw)        # unfold wrapped lines
    out = []
    for block in raw.split("BEGIN:VEVENT")[1:]:
        block = block.split("END:VEVENT")[0]

        def field(key):
            m = re.search(rf"^({key}[^:\n]*):(.*)$", block, re.M)
            return (m.group(1), m.group(2).strip()) if m else ("", "")

        prop, val = field("DTSTART")
        title = field("SUMMARY")[1]
        loc = field("LOCATION")[1]
        rrule = field("RRULE")[1]
        start = to_eastern(prop, val)
        if start and title:
            out.append({"start": start, "title": title,
                        "location": loc, "recurring": bool(rrule)})
    return out


def to_eastern(prop, val):
    """The calendar mixes UTC (trailing Z) and local times. Handle both."""
    if "VALUE=DATE" in prop:
        return datetime.strptime(val[:8], "%Y%m%d").replace(tzinfo=TZ)
    m = re.match(r"^(\d{8})T(\d{6})(Z?)$", val)
    if not m:
        return None
    dt = datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")
    if m.group(3) == "Z":
        return dt.replace(tzinfo=timezone.utc).astimezone(TZ)
    return dt.replace(tzinfo=TZ)


# --- Formatting -------------------------------------------------------------
def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def nice_title(s):
    s = s.strip().rstrip("!")
    if s.isupper():
        s = s.title()
    for a, b in [("Cmu Wushu", "CMU Wushu"), ("Arcc", "ARCC"), ("Oca", "OCA"),
                 ("Tsa", "TSA"), ("Cssa", "CSSA"), ("Csa", "CSA"),
                 ("Soul", "SOUL"), ("Gbm", "GBM"), ("Pc ", "PC ")]:
        s = s.replace(a, b)
    return s


def nice_place(loc):
    if not loc:
        return None
    loc = loc.replace("\\,", ",").strip()
    loc = re.sub(r"\s*TABLE\s*\d+", "", loc, flags=re.I)
    loc = re.sub(r",\s*Pittsburgh,\s*PA[^,]*(,\s*USA)?\s*$", "", loc)
    m = re.match(r"^CUC-?\s*(.+)$", loc, re.I)
    if m:
        key = m.group(1).strip().upper()
        return "Cohon Center, " + ROOMS.get(key, m.group(1).strip().title())
    m = re.match(r"^DH-?\s*(\d+)$", loc, re.I)
    if m:
        return "Doherty Hall " + m.group(1)
    return esc(loc[:70])


def clock(dt):
    return f"{dt.hour % 12 or 12}:{dt.minute:02d} {'AM' if dt.hour < 12 else 'PM'}"


def tag_for(title, override=None):
    if override:
        for rx, pair in TAGS:
            if pair[1].lower() == override.lower():
                return pair
        if override.lower() == "performance":
            return DEFAULT_TAG
        return ("tag--social", override)
    for rx, pair in TAGS:
        if rx.search(title):
            return pair
    return DEFAULT_TAG


# --- HTML builders ----------------------------------------------------------
def build_cards(events, notes):
    if not events:
        return ("""          <article class="event-card">
            <div class="event-card__body">
              <span class="tag">Nothing scheduled</span>
              <h3>No upcoming events right now</h3>
              <p>
                Check back soon, or follow us on Instagram. New events are added to our
                calendar throughout the semester.
              </p>
            </div>
          </article>""")
    out = []
    for e in events:
        cls, label = tag_for(e["title"], e.get("type"))
        title = nice_title(e["title"])
        place = nice_place(e["location"])
        note = e.get("note") or notes.get(e["title"].strip()) or notes.get(title)
        out.append(f"""          <article class="event-card">
            <div class="event-card__body">
              <span class="tag {cls}">{label}</span>
              <p class="event-card__date">{e['start'].strftime('%A, %B %-d, %Y')}</p>
              <h3>{esc(title)}</h3>""")
        if note:
            out.append(f"              <p>\n                {esc(note)}\n              </p>")
        out.append('              <p class="event-card__meta">')
        out.append(f'                <span><strong>Where:</strong> '
                   f'{place or "See the club calendar"}</span>')
        if not e.get("extra"):
            out.append(f'                <span><strong>Time:</strong> {clock(e["start"])}</span>')
        out.append("              </p>\n            </div>\n          </article>")
    return "\n".join(out)


def build_rows(events):
    out = []
    for e in events:
        _, label = tag_for(e["title"], e.get("type"))
        place = nice_place(e["location"]) or "Not listed"
        out.append(f"""              <tr>
                <th scope="row">{e['start'].strftime('%b %-d, %Y')}</th>
                <td>{esc(nice_title(e['title']))}</td>
                <td>{label}</td>
                <td>{place}</td>
              </tr>""")
    return "\n".join(out)


def replace_region(html, name, body):
    start, end = f"<!-- AUTO:{name}:START -->", f"<!-- AUTO:{name}:END -->"
    if start not in html or end not in html:
        sys.exit(f"ERROR: markers for {name} not found in events.html")
    pre = html.split(start)[0]
    post = html.split(end)[1]
    return f"{pre}{start}\n{body}\n{' ' * 10}{end}{post}"


# --- Main -------------------------------------------------------------------
def load_extras():
    """Events kept in event-extras.json because they are not on the calendar."""
    if not os.path.exists(EXTRAS):
        return []
    with open(EXTRAS, encoding="utf-8") as f:
        data = json.load(f)
    out = []
    for e in data.get("events", []):
        try:
            d = datetime.strptime(e["date"], "%Y-%m-%d").replace(tzinfo=TZ)
        except (KeyError, ValueError):
            print(f"  skipping malformed extra: {e.get('title', '?')}")
            continue
        out.append({"start": d, "title": e.get("title", "Untitled"),
                    "location": e.get("location", ""), "recurring": False,
                    "extra": True, "type": e.get("type"), "note": e.get("note", "")})
    return out


def main():
    dry = "--dry-run" in sys.argv
    notes = {}
    if os.path.exists(NOTES):
        with open(NOTES, encoding="utf-8") as f:
            notes = json.load(f)

    events = parse_events(fetch_ics(ICS_URL))
    extras = load_extras()
    today = datetime.now(TZ).date()

    singles = [e for e in events if not e["recurring"] and not SKIP.search(e["title"])]
    singles += extras          # hand-maintained events merge in here
    upcoming = sorted([e for e in singles if e["start"].date() >= today],
                      key=lambda e: e["start"])[:MAX_UPCOMING]
    past = sorted([e for e in singles if e["start"].date() < today],
                  key=lambda e: e["start"], reverse=True)

    html = open(PAGE, encoding="utf-8").read()
    new = replace_region(html, "UPCOMING", build_cards(upcoming, notes))
    new = replace_region(new, "PAST", build_rows(past))

    print(f"{len(upcoming)} upcoming, {len(past)} past events "
          f"({len(extras)} from event-extras.json)")
    if new == html:
        print("No change.")
        return 0
    if dry:
        print("Would update events.html (dry run).")
        return 0
    open(PAGE, "w", encoding="utf-8").write(new)
    print("Updated events.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
