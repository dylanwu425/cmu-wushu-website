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

It also writes data/live.json, which the site reads in the browser for the
"Next practice" strip and the numbers band: every practice in the current
weekly series (expanded from the calendar's repeat rules), the next few
public events, and a few club statistics. The member count comes from
event-extras.json ("stats"), so it survives regeneration.

Two deliberate safety rules:
  1. Calendar DESCRIPTION fields are NEVER published. They contain call
     times, Google Meet links, and phone PINs. Blurbs come from
     event-notes.json instead.
  2. Internal logistics (rehearsals, board meetings, elections, rides)
     are filtered out. See SKIP below.
"""

import html
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone, date
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
LIVE = os.path.join(HERE, "data", "live.json")

MAX_UPCOMING = 6      # cards shown under "Upcoming events"
LIVE_EVENTS = 3       # upcoming public events listed in data/live.json
LIVE_HORIZON = 200    # days ahead a repeating practice is expanded, at most

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
    """Return [{start: datetime, title, location, recurring: bool, ...}] in Eastern.

    The extra keys (end, uid, rrule, exdates, recurrence_id, all_day) only
    matter for data/live.json; the Events page ignores them.
    """
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
            end = to_eastern(*field("DTEND"))
            # A skipped date can come as several EXDATE lines, or one line
            # with several dates separated by commas.
            exdates = []
            for eprop, evals in re.findall(r"^(EXDATE[^:\n]*):(.*)$", block, re.M):
                for ev in evals.split(","):
                    d = to_eastern(eprop, ev.strip())
                    if d:
                        exdates.append(d)
            rid = to_eastern(*field("RECURRENCE-ID"))
            out.append({"start": start, "title": title,
                        "location": loc, "recurring": bool(rrule),
                        "end": end, "uid": field("UID")[1], "rrule": rrule,
                        "exdates": exdates, "recurrence_id": rid,
                        "all_day": "VALUE=DATE" in prop})
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
    m = re.match(r"^CUC\s*-?\s*(.+)$", loc, re.I)
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
        place = nice_place(e["location"]) or "&mdash;"
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


# --- data/live.json ---------------------------------------------------------
WEEKDAYS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
PRACTICE = re.compile(r"practice", re.I)
CANCELLED = re.compile(r"cancel", re.I)


def rule_of(e):
    return dict(kv.split("=", 1) for kv in e["rrule"].split(";") if "=" in kv)


def series_until(e):
    """When a repeating event stops, or None if it never says."""
    u = rule_of(e).get("UNTIL")
    if not u:
        return None
    if len(u) == 8:                           # a bare date: valid all that day
        return datetime.strptime(u, "%Y%m%d").replace(
            hour=23, minute=59, second=59, tzinfo=TZ)
    return to_eastern("", u)


def expand_weekly(e, overrides, horizon):
    """Turn one repeating event into its dated occurrences, in Eastern time.

    Google's feed only uses FREQ=WEEKLY for practices, with BYDAY, UNTIL and
    the odd COUNT or INTERVAL, so that is all this handles. Dates listed in
    EXDATE are skipped, and an occurrence Google exported separately (a
    RECURRENCE-ID entry, meaning someone edited that one date) takes the
    edited time, room and title instead. A cancelled one is dropped.
    """
    rule = rule_of(e)
    if rule.get("FREQ") != "WEEKLY":
        return []
    first = e["start"]
    length = (e["end"] - first) if e["end"] else None
    interval = max(1, int(rule.get("INTERVAL", "1")))
    days = [d for d in rule.get("BYDAY", "").split(",") if d in WEEKDAYS] \
        or [WEEKDAYS[first.weekday()]]
    count = int(rule["COUNT"]) if rule.get("COUNT", "").isdigit() else None

    until = series_until(e)

    skipped = {d for d in e["exdates"]}
    week = first - timedelta(days=first.weekday())   # Monday of the first week
    out, made = [], 0
    while True:
        for i, name in enumerate(WEEKDAYS):
            if name not in days:
                continue
            when = week + timedelta(days=i)
            if when < first:
                continue
            if until and when > until:
                return out
            if when > horizon or (count and made >= count):
                return out
            made += 1
            if when in skipped:
                continue
            occ = overrides.get((e["uid"], when))
            if occ is None:
                occ = {"start": when, "end": when + length if length else None,
                       "title": e["title"], "location": e["location"]}
            elif CANCELLED.search(occ["title"]):
                continue
            out.append(occ)
        week += timedelta(weeks=interval)


def live_item(e):
    place = nice_place(e.get("location", ""))
    return {
        "title": nice_title(e["title"]),
        "start": e["start"].isoformat(),
        "end": e["end"].isoformat() if e.get("end") else None,
        "allDay": bool(e.get("all_day")) or bool(e.get("extra")),
        "location": html.unescape(place) if place else None,
    }


def build_live(events, upcoming, past, extras_stats, today):
    """Everything the browser needs for the live strip and the numbers band."""
    horizon = datetime.combine(today, datetime.min.time(), TZ) + timedelta(days=LIVE_HORIZON)
    overrides = {(e["uid"], e["recurrence_id"]): e
                 for e in events if e["recurrence_id"]}

    practices = []
    for e in events:
        if not PRACTICE.search(e["title"]) or CANCELLED.search(e["title"]):
            continue
        if e["recurring"]:
            # Every date in a still-running series, not just the next few, so
            # the file only changes when the calendar does, not every morning.
            until = series_until(e)
            if until and until.date() < today - timedelta(days=1):
                continue
            practices += expand_weekly(e, overrides, horizon)
        elif not e["recurrence_id"] and e["start"].date() >= today:
            practices.append(e)          # a one-off practice
    practices.sort(key=lambda x: x["start"])
    seen, keep = set(), []
    for o in practices:
        key = (o["start"], o.get("location", ""))
        if key in seen:
            continue
        seen.add(key)
        keep.append(o)
    live_practices = [live_item(o) for o in keep]

    performances = sum(1 for e in past if tag_for(e["title"], e.get("type"))[1] == "Performance")
    founded = extras_stats.get("founded")
    if not founded and past:
        founded = min(e["start"] for e in past).year
    years = (today.year - founded + 1) if founded else None

    return {
        "_comment": "Written by scripts/update_events.py from the club calendar. "
                    "Do not edit by hand: change the calendar, or the stats in "
                    "event-extras.json, and it will be regenerated.",
        "practices": live_practices,
        "events": [live_item(e) for e in upcoming[:LIVE_EVENTS]],
        "stats": {
            "years": years,
            "performances": performances,
            "members": extras_stats.get("members"),
        },
    }


# --- Main -------------------------------------------------------------------
def load_extras():
    """Events kept in event-extras.json because they are not on the calendar,
    plus the hand-kept numbers under "stats"."""
    if not os.path.exists(EXTRAS):
        return [], {}
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
    return out, data.get("stats", {})


def main():
    dry = "--dry-run" in sys.argv
    notes = {}
    if os.path.exists(NOTES):
        with open(NOTES, encoding="utf-8") as f:
            notes = json.load(f)

    events = parse_events(fetch_ics(ICS_URL))
    extras, extras_stats = load_extras()
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

    live = build_live(events, upcoming, past, extras_stats, today)
    live_text = json.dumps(live, indent=2, ensure_ascii=False) + "\n"
    old_live = open(LIVE, encoding="utf-8").read() if os.path.exists(LIVE) else None
    print(f"{len(live['practices'])} practice dates in the current series")

    if new == html and live_text == old_live:
        print("No change.")
        return 0
    if dry:
        print("Would update events.html and/or data/live.json (dry run).")
        return 0
    if new != html:
        open(PAGE, "w", encoding="utf-8").write(new)
        print("Updated events.html")
    if live_text != old_live:
        os.makedirs(os.path.dirname(LIVE), exist_ok=True)
        open(LIVE, "w", encoding="utf-8").write(live_text)
        print("Updated data/live.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
