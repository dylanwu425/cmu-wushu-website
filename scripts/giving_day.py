#!/usr/bin/env python3
"""
Build the Giving Day page from data/giving-day.json, and put it live or take
it down again.

Everything on giving-day.html that mentions a date, a dollar figure, a donor
count or the donation URL is generated here, between the <!-- GD:NAME start -->
and <!-- GD:NAME end --> markers. Hand-editing inside those markers is
pointless: the next run overwrites it. Edit data/giving-day.json instead.

    python3 scripts/giving_day.py                 rebuild the page
    python3 scripts/giving_day.py --dry-run       show what would change
    python3 scripts/giving_day.py --publish       link it from the whole site
    python3 scripts/giving_day.py --unpublish     unlink it again
    python3 scripts/giving_day.py --close         keep it up, stop the asking

Publishing is the only step that touches any other page. It adds a banner
strip and a footer link to all six, adds the page to the sitemap, and drops
the noindex tag. Unpublishing removes every one of those again, so the site
goes back exactly to how it was.
"""

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CONFIG = os.path.join(ROOT, "data", "giving-day.json")
PAGE = os.path.join(ROOT, "giving-day.html")
SITEMAP = os.path.join(ROOT, "sitemap.xml")

# The six pages that carry the shared header and footer.
SITE_PAGES = ["index.html", "about.html", "schedule.html", "events.html",
              "booking.html", "contact.html"]

PAGE_URL = "https://cmuwushu.org/giving-day"
STATUSES = ("draft", "live", "closed")


# ---------------------------------------------------------------- helpers

def die(msg):
    sys.exit("ERROR: " + msg)


def load():
    with open(CONFIG, encoding="utf-8") as fh:
        cfg = json.load(fh)

    if cfg.get("status") not in STATUSES:
        die("status must be one of %s, not %r" % ("/".join(STATUSES), cfg.get("status")))

    for key in ("opensAt", "closesAt"):
        try:
            cfg[key + "_dt"] = dt.datetime.fromisoformat(cfg[key])
        except (KeyError, ValueError):
            die("%s is not an ISO timestamp like 2026-12-01T00:00:00-05:00" % key)

    if cfg["closesAt_dt"] <= cfg["opensAt_dt"]:
        die("closesAt is not after opensAt")

    return cfg


def esc(text):
    """
    Escape for text content. Quotes are left alone and a straight apostrophe
    becomes &rsquo;, so a line generated from the JSON is indistinguishable
    from the hand-written copy on every other page.
    """
    return html.escape(str(text), quote=False).replace("'", "&rsquo;")


def attr(text):
    """Escape for an attribute value, where the quotes do matter."""
    return html.escape(str(text), quote=True)


def money(n):
    """1500 -> $1,500. Whole dollars only; nobody pledges cents."""
    return "$%s" % format(int(round(n)), ",d")


def long_date(when):
    # "December 1, 2026" — no leading zero, which strftime gives us on neither
    # platform consistently, so strip it by hand.
    return "%s %d, %d" % (when.strftime("%B"), when.day, when.year)


def donate_url(cfg, placement, amount=None):
    """
    The donation URL with the placement tagged on, so the platform's own
    referral report shows whether the film or the tiers did the work.
    Returns None when there is no URL yet, which is what makes every button
    on the page render as a dead-but-honest 'coming soon' chip.
    """
    base = (cfg.get("donateUrl") or "").strip()
    if not base:
        return None

    parts = urlparse(base)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.update({
        "utm_source": "cmuwushu.org",
        "utm_medium": "website",
        "utm_campaign": "giving-day-%d" % cfg["opensAt_dt"].year,
        "utm_content": placement,
    })

    param = (cfg.get("amountParam") or "").strip()
    if amount and param:
        query[param] = str(int(amount))

    return urlunparse(parts._replace(query=urlencode(query)))


def put(page, name, body):
    """Replace one marked region. The markers themselves always survive."""
    pattern = re.compile(
        r"(<!-- %s start -->)(.*?)(<!-- %s end -->)" % (re.escape(name), re.escape(name)),
        re.S)
    if not pattern.search(page):
        die("marker %s is missing from giving-day.html" % name)
    return pattern.sub(lambda m: m.group(1) + body + m.group(3), page, count=1)


def pad(body, spaces):
    """Shift every non-blank line right, for dropping a fragment inside another."""
    prefix = " " * spaces
    return "\n".join(prefix + ln if ln.strip() else ln for ln in body.split("\n"))


def indent(body, spaces):
    """
    Lay a generated block between its markers at the right depth: the block's
    own relative indentation is kept, the whole thing is shifted in by
    `spaces`, and the closing marker is left sitting at that same depth.
    """
    return "\n" + pad(body.strip("\n"), spaces) + "\n" + " " * spaces


# ---------------------------------------------------------------- the weapons

# One drawing per tier, sitting behind the card like a watermark. They are
# hand-built paths rather than photographs so they take the page's ink colour,
# cost nothing to load, and stay sharp at any size. viewBox is 0 0 100 100 for
# all four, so the CSS can place them identically. fill/stroke are
# currentColor, which the stylesheet sets per card.
WEAPON_ART = {
    # A folding fan, open.
    "fan": """<g transform="translate(-3.51 -19.38) scale(1.07)">
  <g>
    <mask id="gd-fan-crease">
      <rect width="100" height="100" fill="#fff"/>
      <g stroke="#000" stroke-width="0.9" fill="none">
      <path d="M33.6 70.1 L14.53 53.93"/>
      <path d="M35.77 67.88 L19.23 49.14"/>
      <path d="M38.25 66 L24.58 45.07"/>
      <path d="M40.96 64.49 L30.45 41.81"/>
      <path d="M43.87 63.39 L36.74 39.43"/>
      <path d="M46.9 62.72 L43.3 37.99"/>
      <path d="M50 62.5 L50 37.5"/>
      <path d="M53.1 62.72 L56.7 37.99"/>
      <path d="M56.13 63.39 L63.26 39.43"/>
      <path d="M59.04 64.49 L69.55 41.81"/>
      <path d="M61.75 66 L75.42 45.07"/>
      <path d="M64.23 67.88 L80.77 49.14"/>
      <path d="M66.4 70.1 L85.47 53.93"/>
      </g>
    </mask>
    <path mask="url(#gd-fan-crease)" d="M10.99 59.62 A46 46 0 0 1 89.01 59.62 L68.66 72.34 A22 22 0 0 0 31.34 72.34 Z"/>
    <g fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round">
      <path d="M33.6 70.1 L48.86 83.03"/>
      <path d="M35.77 67.88 L49.01 82.88"/>
      <path d="M38.25 66 L49.18 82.74"/>
      <path d="M40.96 64.49 L49.37 82.64"/>
      <path d="M43.87 63.39 L49.57 82.56"/>
      <path d="M46.9 62.72 L49.78 82.52"/>
      <path d="M50 62.5 L50 82.5"/>
      <path d="M53.1 62.72 L50.22 82.52"/>
      <path d="M56.13 63.39 L50.43 82.56"/>
      <path d="M59.04 64.49 L50.63 82.64"/>
      <path d="M61.75 66 L50.82 82.74"/>
      <path d="M64.23 67.88 L50.99 82.88"/>
      <path d="M66.4 70.1 L51.14 83.03"/>
    </g>
    <path d="M51.38 81.8 L12.26 57.59 L9.72 61.66 L48.62 86.2 Z"/>
    <path d="M51.38 86.2 L90.28 61.66 L87.74 57.59 L48.62 81.8 Z"/>
    <path d="M46.6 83 L47.6 91.5 L52.4 91.5 L53.4 83 Z"/>
    <circle cx="50" cy="84" r="2.4" fill="#fff" fill-opacity="0.001"/>
  </g>
</g>""",

    # A nine-section chain whip, mid-swing: handle, links, dart.
    "chainwhip": """<g transform="translate(7 5.43) scale(0.92)">
  <g fill="none" stroke="currentColor" stroke-linecap="round">
    <path d="M5.9 58.59 L10.57 67.78" stroke-width="5"/>
    <path d="M10.57 67.78 L20.31 77" stroke-width="2.8"/>
    <path d="M20.31 77 L33.35 79.43" stroke-width="2.8"/>
    <path d="M33.35 79.43 L45.34 73.48" stroke-width="2.8"/>
    <path d="M45.34 73.48 L51.61 66.04" stroke-width="2.8"/>
    <path d="M51.61 66.04 L52.76 52.6" stroke-width="2.8"/>
    <path d="M52.76 52.6 L51.82 39.1" stroke-width="2.8"/>
    <path d="M51.82 39.1 L57.02 26.94" stroke-width="2.8"/>
    <path d="M57.02 26.94 L68.71 20.42" stroke-width="2.8"/>
    <path d="M68.71 20.42 L81.9 17.28" stroke-width="2.8"/>
  </g>
  <g>
    <circle cx="10.57" cy="67.78" r="3.3"/>
    <circle cx="20.31" cy="77" r="3.3"/>
    <circle cx="33.35" cy="79.43" r="3.3"/>
    <circle cx="45.34" cy="73.48" r="3.3"/>
    <circle cx="51.61" cy="66.04" r="3.3"/>
    <circle cx="52.76" cy="52.6" r="3.3"/>
    <circle cx="51.82" cy="39.1" r="3.3"/>
    <circle cx="57.02" cy="26.94" r="3.3"/>
    <circle cx="68.71" cy="20.42" r="3.3"/>
    <circle cx="81.9" cy="17.28" r="3.3"/>
  </g>
  <circle cx="4.63" cy="54.86" r="3.6" fill="none" stroke="currentColor" stroke-width="2"/>
  <path d="M81.9 17.28 L86.45 18.76 L93.56 14.47 L85.28 13.9 Z"/>
  <path d="M78.71 19.42 L79.29 21.04 L79.78 22.57 L80.16 24.05 L80.4 25.53 L80.48 27.07 L80.41 28.7 L80.16 30.46 L79.77 32.32 L79.27 34.28 L78.71 36.31 L78.16 38.39 L77.69 40.49 L77.36 42.6 L77.2 44.65 L80.78 45.02 L81.15 43.29 L81.68 41.53 L82.34 39.7 L83.1 37.8 L83.9 35.84 L84.69 33.83 L85.4 31.77 L85.98 29.66 L86.38 27.52 L86.57 25.38 L86.54 23.27 L86.33 21.23 L86.01 19.29 L85.65 17.48 Z"/>
</g>""",

    # A tasselled spear: shaft, leaf blade, horsehair.
    "spear": """<g transform="translate(3.85 -0.64) scale(0.96)">
  <path d="M10.33 98.2 L71.58 32.09 L68.09 28.79 L5.67 93.8 Z"/>
  <path d="M72.31 32.77 L75.37 27.34 L72.6 24.74 L67.36 28.11 Z"/>
  <ellipse cx="70.18" cy="30.08" rx="3.12" ry="2.28" transform="rotate(-46.67 70.18 30.08)"/>
  <g fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
    <path d="M68.78 28.76 Q62.64 33.13 55.14 38.46"/>
    <path d="M69.48 29.42 Q62.89 35.33 54.84 42.56"/>
    <path d="M70.18 30.08 Q63.14 37.54 54.53 46.66"/>
    <path d="M70.88 30.73 Q65.36 37.66 58.61 46.12"/>
    <path d="M71.57 31.39 Q67.57 37.78 62.69 45.58"/>
  </g>
  <path d="M73.64 26.4 C78.56 27.39 86.68 17.14 91 8 C82.13 12.85 74.72 19.07 73.64 26.4 Z"/>
</g>""",

    # Jian and dao, crossed: straight sword left, curved sabre right.
    "swords": """<g transform="translate(4.34 -4.24) scale(0.99)">
  <mask id="gd-dao-m">
    <rect width="100" height="100" fill="#fff"/>
    <path stroke="#000" stroke-width="0.8" fill="none" d="M71.78 66.75 L70.16 62.53 L68.32 58.4 L66.27 54.37 L64 50.45 L61.54 46.66 L58.87 42.99 L56.01 39.47 L52.98 36.1 L49.76 32.9 L46.38 29.86 L42.85 27.01 L39.17 24.34"/>
    <path stroke="#000" stroke-width="4" stroke-linejoin="round" fill="#000" d="M31.9 76.64 L35.69 71.25 L39.48 65.86 L43.26 60.47 L47.05 55.08 L50.83 49.69 L54.61 44.3 L58.38 38.9 L62.12 33.48 L65.81 28.02 L69.4 22.49 L72.83 16.84 L76 11 L76 11 L71.38 15.78 L67.02 20.74 L62.81 25.82 L58.71 30.98 L54.66 36.17 L50.63 41.38 L46.62 46.6 L42.61 51.83 L38.61 57.05 L34.6 62.28 L30.59 67.51 L26.58 72.73 Z"/>
  </mask>
  <mask id="gd-jian-m">
    <rect width="100" height="100" fill="#fff"/>
    <path stroke="#000" stroke-width="0.8" fill="none" d="M30.43 73.07 L70.67 18.25"/>
  </mask>
  <g mask="url(#gd-dao-m)">
    <path d="M75.81 72.87 L73.88 66.54 L71.53 60.35 L68.73 54.33 L65.51 48.51 L61.86 42.93 L57.81 37.62 L53.37 32.6 L48.57 27.91 L43.41 23.57 L37.94 19.62 L31.44 17.48 L24 18 L23.88 18.28 L28.77 22.69 L33.71 26.53 L38.78 30 L43.58 33.84 L48.06 38.03 L52.22 42.53 L56.02 47.33 L59.45 52.4 L62.48 57.71 L65.1 63.22 L67.3 68.91 L69.07 74.74 Z"/>
    <ellipse cx="74" cy="78" rx="8" ry="2.6" transform="rotate(-103.55 74 78)"/>
    <path d="M71.76 78.54 L74.87 90.13 L78.76 89.2 L76.24 77.46 Z"/>
    <circle cx="77.56" cy="92.78" r="3.4" fill="none" stroke="currentColor" stroke-width="1.8"/>
  </g>
  <g mask="url(#gd-jian-m)">
    <ellipse cx="18" cy="90" rx="4" ry="2.4" transform="rotate(-53.71 18 90)"/>
    <path d="M20.5 89.97 L29.08 78.29 L25.86 75.92 L17.28 87.61 Z"/>
    <path d="M34.72 82.43 Q32.9 79.1 29.01 75.01 Q23.94 72.52 20.21 71.78 Q22.04 75.11 25.93 79.2 Q31 81.69 34.72 82.43 Z"/>
    <path d="M31.9 76.64 L35.69 71.25 L39.48 65.86 L43.26 60.47 L47.05 55.08 L50.83 49.69 L54.61 44.3 L58.38 38.9 L62.12 33.48 L65.81 28.02 L69.4 22.49 L72.83 16.84 L76 11 L76 11 L71.38 15.78 L67.02 20.74 L62.81 25.82 L58.71 30.98 L54.66 36.17 L50.63 41.38 L46.62 46.6 L42.61 51.83 L38.61 57.05 L34.6 62.28 L30.59 67.51 L26.58 72.73 Z"/>
    <ellipse cx="16.82" cy="91.61" rx="2.21" ry="1.61" transform="rotate(-53.71 16.82 91.61)"/>
    <g fill="none" stroke="currentColor" stroke-width="1.27" stroke-linecap="round">
      <path d="M16.13 91.11 Q14.09 92.86 11.59 94.99"/>
      <path d="M16.82 91.61 Q14.67 94.54 12.04 98.12"/>
      <path d="M17.5 92.12 Q16.45 94.59 15.16 97.61"/>
    </g>
  </g>
</g>""",
}


# Measured ink coverage of each drawing, inverted, so that coverage times
# opacity comes out the same for all four: the solid fan must not shout while
# the thin chain whip looks like art that failed to load.
#   fan 22.7%   chain whip 6.4%   spear 6.4%   jian+dao 9.7%
# The fan is nudged up from the 0.052 the arithmetic gives, because it is the
# one drawn in seal red, and red on paper reads lighter than ink.
WEAPON_WEIGHT = {"fan": 0.065, "chainwhip": 0.185, "spear": 0.185, "swords": 0.122}


def weapon_svg(key):
    """The watermark behind a tier card. Unknown key -> nothing at all.

    preserveAspectRatio is left at "meet" on purpose. "slice" fills the card
    and bleeds off it consistently, which looks tidier, but it crops the
    weapon — the chain whip loses its wrist loop and the spear its point,
    which are exactly the parts that say what the thing is.
    """
    key = (key or "").strip()
    body = WEAPON_ART.get(key)
    if not body:
        return ""
    return ('<svg class="gd-tier__art" viewBox="0 0 100 100" fill="currentColor"\n'
            '     style="opacity: %s"\n'
            '     aria-hidden="true" focusable="false">\n%s\n</svg>'
            % (WEAPON_WEIGHT.get(key, 0.12), pad(body, 2)))

# ---------------------------------------------------------------- the regions

def build(cfg):
    with open(PAGE, encoding="utf-8") as fh:
        page = fh.read()

    opens = cfg["opensAt_dt"]
    date_text = long_date(opens)
    name = esc(cfg.get("name") or "Giving Day")
    closed = cfg["status"] == "closed"
    challenge = cfg.get("challenge") or {}
    on = bool(challenge.get("on")) and not closed
    # Two different numbers, and the page is careful about which is which:
    # min_gift is CMU's floor for a gift to be counted at all ($5), ask is what
    # the buttons actually ask for ($10).
    min_gift = int(challenge.get("minGift") or 5)
    ask = int(cfg.get("askAmount") or min_gift)

    # ---- the date, in the three places it appears
    # GD:DATE is the only standalone date marker. The countdown and the closing
    # band print the date too, but they regenerate wholesale, so a marker
    # nested inside either one would be wiped out by its own parent's rebuild.
    page = put(page, "GD:DATE",
               '<span class="gd-date">%s &middot; %s</span>' % (name, esc(date_text)))

    # ---- the opening paragraph. The argument is the free practice, not the
    #      university's prize pool: there are hundreds of clubs in that race
    #      and we are not going to win it. The challenge gets one clause at
    #      the end, and only to explain why a small gift is a real gift.
    if closed:
        lede = (
            "Thank you. The weapons on the loaner rack, the mats, the costumes "
            "&mdash; this year they came from the people who gave on %s. Practice "
            "stays free because of you."
            % esc(date_text))
    elif on:
        lede = (
            "Anyone can walk into our practice without paying a cent, and we have never "
            "wanted that to change. The mats, the loaner weapons, the costumes: it all "
            "comes from gifts the size of the ones on this page. Anything from %s up is a "
            "real contribution here &mdash; CMU scores the day by how many people give, "
            "not how much, so a %s gift counts for every bit as much as a $500 one."
            % (money(min_gift), money(ask)))
    else:
        lede = (
            "Anyone can walk into our practice without paying a cent, and we have never "
            "wanted that to change. Every broadsword on the loaner rack, every mat, every "
            "costume has come from somewhere. For one day in %s, it comes from you."
            % opens.strftime("%B"))
    page = put(page, "GD:LEDE",
               indent('<p class="gd-lede">\n  %s\n</p>' % lede, 10))

    # ---- the countdown
    if closed:
        page = put(page, "GD:COUNTDOWN", "\n          ")
    else:
        page = put(page, "GD:COUNTDOWN", indent("""
<div class="gd-countdown" data-gd-countdown
     data-opens="%s"
     data-closes="%s">
  <p class="gd-countdown__label">%s opens in</p>
  <div class="gd-countdown__clock" role="timer">
    <span class="gd-unit"><b data-gd-days>--</b><i>days</i></span>
    <span class="gd-unit"><b data-gd-hours>--</b><i>hours</i></span>
    <span class="gd-unit"><b data-gd-mins>--</b><i>min</i></span>
  </div>
  <p class="gd-countdown__fallback">
    Mark your calendar for %s.
  </p>
</div>""" % (attr(cfg["opensAt"]), attr(cfg["closesAt"]), name, esc(date_text)), 10))

    # ---- donate buttons. One helper, because the pending state has to look
    #      the same everywhere or the page looks half-finished.
    def cta(placement, label, amount=None, cls="gd-btn"):
        url = donate_url(cfg, placement, amount)
        if url:
            return '<a class="%s" href="%s" target="_blank" rel="noopener">%s</a>' % (
                cls, attr(url), label)
        pending = "Soon" if cls != "gd-btn" else "Donation page coming soon"
        extra = " gd-btn--pending" if cls == "gd-btn" else " gd-btn--pending"
        return '<span class="%s%s" aria-disabled="true">%s</span>' % (cls, extra, pending)

    have_url = donate_url(cfg, "x") is not None

    if closed:
        # A span, not a p: this sits inside the .gd-cta-row paragraph, and a
        # nested <p> would be closed by the parser before it ever rendered.
        hero_cta = ('<span class="gd-cta-note">%s %d is over. Thank you to everyone '
                    'who gave.</span>' % (name, opens.year))
    elif have_url:
        hero_cta = (cta("hero", "Give %s" % money(ask), ask) +
                    '\n  <span class="gd-cta-note">Takes about two minutes.</span>')
    else:
        hero_cta = cta("hero", "")
    page = put(page, "GD:CTA-HERO",
               indent('<p class="gd-cta-row">\n  %s\n</p>' % hero_cta, 10))

    # ---- the film. Three states: a YouTube ID (lazy facade, nothing loads
    #      from Google until someone clicks), a file in the repo (played
    #      straight from the site), or neither (a "coming soon" panel).
    #      YouTube wins when both are set, because it is shareable and it is
    #      not 14 MB down somebody's phone data.
    video = cfg.get("video") or {}
    vid = (video.get("youtubeId") or "").strip()
    vfile = (video.get("file") or "").strip()
    poster = attr(video.get("poster") or "images/ds-2026/web/dscf6345.jpg")
    vtitle = attr(video.get("title") or "%s film" % name)
    vlen = (video.get("length") or "").strip()
    autoplay = bool(video.get("autoplay"))
    loop = bool(video.get("loop"))
    play_label = "Watch the film" + (" &middot; %s" % esc(vlen) if vlen else "")
    if autoplay:
        # It can only autoplay muted — every browser requires that — so the
        # caption has to tell people there is sound to turn on.
        play_label = "Playing silently &middot; press for sound"
        if vlen:
            play_label += " &middot; %s" % esc(vlen)

    if vid:
        page = put(page, "GD:VIDEO", indent("""
<div class="gd-film">
  <div class="gd-film__frame">
    <img class="gd-film__poster" src="%s" alt="" width="1200" height="675">
    <button class="gd-film__play" type="button"
            data-gd-play="%s" data-gd-title="%s"
            aria-label="Play the %s">
      <span class="gd-film__play-mark" aria-hidden="true"></span>
      <span class="gd-film__play-label">%s</span>
    </button>
  </div>
</div>
<noscript>
  <p class="gd-cta-note">
    <a href="https://www.youtube.com/watch?v=%s" target="_blank" rel="noopener">Watch the film on YouTube</a>
  </p>
</noscript>""" % (poster, attr(vid), vtitle, vtitle, play_label, attr(vid)), 10))
    elif vfile:
        # preload="none" so the file is not pulled down until it is asked for.
        # preload="none" even when it autoplays: the script turns preloading
        # on only once it has checked that autoplay is wanted here, so a
        # visitor on a metered connection is never handed 14 MB unasked.
        page = put(page, "GD:VIDEO", indent("""
<div class="gd-film">
  <div class="gd-film__frame">
    <video class="gd-film__video" controls playsinline preload="none"%s%s%s
           poster="%s" title="%s" width="1920" height="1080">
      <source src="%s" type="video/mp4">
      <p class="gd-cta-note"><a href="%s">Download the film</a></p>
    </video>
  </div>
</div>
<p class="gd-film__caption">%s</p>""" % (
            " muted" if autoplay else "",
            " loop" if loop else "",
            " data-gd-autoplay" if autoplay else "",
            poster, vtitle, attr(vfile), attr(vfile), play_label), 10))
    else:
        page = put(page, "GD:VIDEO", indent("""
<div class="gd-film gd-film--pending">
  <div class="gd-film__frame">
    <img class="gd-film__poster" src="%s" alt="" width="1200" height="675">
    <div class="gd-film__pending-note">
      <span class="gd-film__pending-mark" aria-hidden="true">片</span>
      <p>The Giving Day film lands here.</p>
    </div>
  </div>
</div>""" % poster, 10))

    # ---- the donate line under the film, which only exists once both the
    #      film and the donation page do
    if (vid or vfile) and not closed:
        page = put(page, "GD:CTA-VIDEO", indent("""
<div class="gd-film-cta">
  %s
  <p>That is the pitch. The rest is up to you.</p>
</div>""" % cta("video", "Give %s" % money(ask), ask), 10))
    else:
        page = put(page, "GD:CTA-VIDEO", "\n          ")

    # ---- the count
    goal_donors = int(cfg.get("goalDonors") or 0)
    donors = int(cfg.get("donors") or 0)
    goal_dollars = int(cfg.get("goalDollars") or 0)
    raised = int(cfg.get("raised") or 0)
    # The counter is on the page from the start: before the day it reads
    # "$0 of $2,000", which is the point of a goal.
    show_bar = goal_dollars > 0 or goal_donors > 0

    # Dollars lead and people follow. The challenge is scored on people, but
    # we are not going to win it, so the honest headline is the money.
    if goal_dollars:
        pct = min(100.0, raised / goal_dollars * 100.0)
        heading = ('<b data-gd-count="%d">%s</b> of <span>%s</span>'
                   % (raised, money(raised), money(goal_dollars)))
    else:
        pct = min(100.0, (donors / goal_donors * 100.0) if goal_donors else 0.0)
        heading = ('<b data-gd-count="%d">%d</b> of <span>%d</span> donors'
                   % (donors, donors, goal_donors))

    def people(n):
        return "from %d %s" % (n, "person" if n == 1 else "people")

    if closed:
        heading = '<b data-gd-count="%d">%s</b> raised' % (raised, money(raised))
        read = people(donors) if donors else ""
    elif donors:
        read = people(donors)
    elif raised:
        read = ""
    else:
        read = "Giving opens %s" % esc(date_text)

    people_line = ('\n      <p class="gd-bar__read">%s</p>' % read) if read else ""

    page = put(page, "GD:BAR", indent("""
<section class="gd-bar-band"%s>
  <div class="container">
    <div class="gd-bar" data-gd-bar style="--gd-pct: %.1f%%">
      <p class="gd-bar__heading">%s</p>
      <div class="gd-bar__track"><span class="gd-bar__fill"></span></div>%s
    </div>
  </div>
</section>""" % ("" if show_bar else " hidden", pct, heading, people_line), 4))

    # ---- the challenge
    if on:
        prizes = [money(p) for p in (challenge.get("prizes") or [])]
        if len(prizes) > 1:
            prize_text = (" win <b>" + "</b>, <b>".join(prizes[:-1]) +
                          "</b> and <b>" + prizes[-1] + "</b> on top of whatever they raise")
        elif prizes:
            prize_text = " win <b>%s</b> on top of whatever they raise" % prizes[0]
        else:
            # CMU does not tell the clubs the amounts until mid-November, so
            # until then the page describes the rule without naming a figure.
            prize_text = " win a share of a prize pool on top of whatever they raise"

        page = put(page, "GD:CHALLENGE", indent("""
<section class="section gd-challenge-section">
  <div class="container">
    <div class="gd-challenge">
      <p class="gd-challenge__kicker">Why a small gift is not a token gift</p>
      <p class="gd-challenge__body">
        Alongside %s, CMU runs matches and challenges for student organizations: the clubs
        that bring in the most <em>individual donors</em> giving %s or more%s. Hundreds of
        orgs are in that race and we are not counting on winning it. We mention it for what
        it says about the scoring &mdash; the day is counted by people, not by dollars.
      </p>
      <p class="gd-challenge__punch">
        So your %s lands on the board exactly as hard as somebody else&rsquo;s $500.
      </p>
      <p class="gd-challenge__fine">
        One gift per person: CMU counts donors by card and email address, and audits them
        afterwards. Please don&rsquo;t give on somebody else&rsquo;s behalf &mdash; ask them
        to give instead, which is worth more to us anyway.
      </p>
    </div>
  </div>
</section>""" % (name, money(min_gift), prize_text, money(ask)), 4))
    else:
        page = put(page, "GD:CHALLENGE", "\n    ")

    # ---- the tiers. Each one is named for a weapon and carries that weapon
    #      drawn behind it; the name does the work the old "what this buys"
    #      line used to do, and the sub-line is optional.
    rows = []
    for tier in (cfg.get("tiers") or []):
        amount = int(tier["amount"])
        flagged = bool(tier.get("flag")) and on
        art = weapon_svg(tier.get("art"))
        hanzi = (tier.get("hanzi") or "").strip()
        weapon = (tier.get("weapon") or "").strip()
        label = (tier.get("label") or "").strip()

        body = ""
        if weapon:
            body += ('  <p class="gd-tier__weapon">%s%s</p>\n' % (
                ('<span class="gd-tier__hanzi" lang="zh-Hans" aria-hidden="true">%s</span>'
                 % esc(hanzi)) if hanzi else "",
                esc(weapon)))
        if label:
            body += '  <p class="gd-tier__label">%s</p>\n' % esc(label)

        rows.append(
            '<li class="gd-tier%s">\n'
            '%s'
            '%s'
            '  <span class="gd-tier__amount">%s</span>\n'
            '  <div class="gd-tier__body">\n%s  </div>\n'
            '  %s\n'
            '</li>' % (
                " gd-tier--flagged" if flagged else "",
                ('  <span class="gd-tier__flag">%s</span>\n' % esc(tier["flag"])) if flagged else "",
                (pad(art, 2) + "\n") if art else "",
                money(amount),
                pad(body, 2),
                cta("tier-%d" % amount, "Give %s" % money(amount), amount, cls="gd-tier__btn"),
            ))
    page = put(page, "GD:TIERS",
               indent('<ul class="gd-tiers">\n%s\n</ul>'
                      % pad("\n".join(rows), 2), 8))

    # ---- where it goes
    items = "\n".join("  <li>%s</li>" % esc(line) for line in (cfg.get("whereItGoes") or []))
    page = put(page, "GD:WHERE",
               indent('<ul class="gd-where">\n%s\n</ul>' % items, 8))

    # ---- the closing band
    if closed:
        foot = ("""
<section class="cta-band gd-cta-band">
  <div class="container">
    <h2>Thank you</h2>
    <p>%d people kept wushu free this year. Come and see what you paid for.</p>
    <a class="btn btn--ghost" href="/schedule">See Practice Times</a>
  </div>
</section>""" % donors)
    elif have_url:
        foot = ("""
<section class="cta-band gd-cta-band">
  <div class="container">
    <h2>%s is %s</h2>
    <p>Two minutes, %s, and practice stays free for everybody who walks in.</p>
    %s
  </div>
</section>""" % (name, esc(date_text), money(ask),
                 cta("footer", "Give %s" % money(ask), ask)))
    else:
        foot = ("""
<section class="cta-band gd-cta-band">
  <div class="container">
    <h2>%s is %s</h2>
    <p>The donation page opens that morning. Until then, the best thing you can do is come train with us.</p>
    <a class="btn btn--ghost" href="/schedule">See Practice Times</a>
  </div>
</section>""" % (name, esc(date_text)))
    page = put(page, "GD:CTA-FOOT", indent(foot, 4))

    # ---- the sticky bar: only worth having when there is somewhere to send
    if have_url and not closed:
        page = put(page, "GD:STICKY", indent("""
<div class="gd-sticky">
  <p class="gd-sticky__read">%s</p>
  %s
</div>""" % ("Giving CMU Day &middot; %s" % esc(date_text),
             cta("sticky", "Give %s" % money(ask), ask)), 2))
    else:
        page = put(page, "GD:STICKY", "\n  ")

    # ---- noindex: on while in draft, off once live
    if cfg["status"] == "draft":
        if 'name="robots"' not in page:
            page = page.replace(
                '  <title>',
                '  <meta name="robots" content="noindex, nofollow">\n\n  <title>', 1)
    else:
        page = re.sub(r'  <meta name="robots" content="noindex, nofollow">\n\n?', "", page)

    return page


# ---------------------------------------------------------------- publishing

STRIP_START = "  <!-- GD:STRIP start -->"
STRIP_END = "  <!-- GD:STRIP end -->"


def strip_markup(cfg):
    """
    The site-wide banner. Its styles ride along inline so that putting the
    campaign up and taking it down never touches styles.css, and so the other
    five pages do not pay for a stylesheet they need for one day.
    """
    name = esc(cfg.get("name") or "Giving Day")
    date_text = esc(long_date(cfg["opensAt_dt"]))
    challenge = cfg.get("challenge") or {}
    ask = money(int(cfg.get("askAmount") or challenge.get("minGift") or 5))
    if cfg["status"] == "closed":
        line = "Thank you to everyone who gave on %s." % date_text
        action = "See where it went"
    elif challenge.get("on"):
        line = "%s is %s. %s counts as much as $500." % (name, date_text, ask)
        action = "Here's why"
    else:
        line = "%s is %s." % (name, date_text)
        action = "Read more"

    return "\n".join([
        STRIP_START,
        '  <style>',
        '    .gd-strip{background:var(--seal);background-image:var(--grain);'
        'font-family:var(--font-body);font-size:.84rem;line-height:1.4}',
        '    .gd-strip__in{display:flex;flex-wrap:wrap;align-items:center;justify-content:center;'
        'gap:.3rem .8rem;padding:.6rem 1rem;text-align:center}',
        '    .gd-strip p{margin:0;color:var(--paper)}',
        '    .gd-strip a{color:var(--paper);text-decoration:underline;'
        'text-underline-offset:3px;font-weight:600;white-space:nowrap}',
        '    .gd-strip a:hover,.gd-strip a:focus-visible{color:var(--paper);text-decoration:none}',
        '  </style>',
        '  <aside class="gd-strip">',
        '    <div class="gd-strip__in">',
        '      <p>%s</p>' % line,
        '      <a href="/giving-day">%s</a>' % action,
        '    </div>',
        '  </aside>',
        STRIP_END,
    ])


FOOTER_LINK = '            <li><a href="/giving-day">Giving Day</a></li>\n'
FOOTER_ANCHOR = '            <li><a href="/contact">Contact / Join</a></li>\n'


def set_published(cfg, want_live, dry_run=False):
    """Add or remove the strip, the footer link and the sitemap entry."""
    changed = []

    for name in SITE_PAGES:
        path = os.path.join(ROOT, name)
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        out = src

        # The strip, immediately after <body>. The removal pattern is the exact
        # inverse of the insertion, down to the surrounding newlines, so that
        # publishing and unpublishing leaves the file byte-for-byte as it was.
        out = re.sub(r"\n%s.*?%s\n" % (re.escape(STRIP_START), re.escape(STRIP_END)),
                     "", out, flags=re.S)
        if want_live:
            out = out.replace("<body>\n", "<body>\n\n" + strip_markup(cfg) + "\n", 1)

        # the footer link
        out = out.replace(FOOTER_LINK, "")
        if want_live:
            if FOOTER_ANCHOR not in out:
                die("%s has an unexpected footer; cannot add the Giving Day link" % name)
            out = out.replace(FOOTER_ANCHOR, FOOTER_ANCHOR + FOOTER_LINK, 1)

        if out != src:
            changed.append(name)
            if not dry_run:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(out)

    # the sitemap
    with open(SITEMAP, encoding="utf-8") as fh:
        src = fh.read()
    out = re.sub(r"  <url>\s*<loc>%s</loc>.*?</url>\n" % re.escape(PAGE_URL),
                 "", src, flags=re.S)
    if want_live:
        entry = ("  <url>\n"
                 "    <loc>%s</loc>\n"
                 "    <changefreq>daily</changefreq>\n"
                 "    <priority>0.9</priority>\n"
                 "  </url>\n" % PAGE_URL)
        out = out.replace("</urlset>", entry + "</urlset>", 1)
    if out != src:
        changed.append("sitemap.xml")
        if not dry_run:
            with open(SITEMAP, "w", encoding="utf-8") as fh:
                fh.write(out)

    return changed


def set_status(status, dry_run=False):
    with open(CONFIG, encoding="utf-8") as fh:
        src = fh.read()
    out = re.sub(r'("status":\s*)"[a-z]+"', r'\1"%s"' % status, src, count=1)
    if out == src:
        die("could not find the status field in data/giving-day.json")
    if not dry_run:
        with open(CONFIG, "w", encoding="utf-8") as fh:
            fh.write(out)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--publish", action="store_true",
                   help="link the page from the whole site and let Google index it")
    g.add_argument("--unpublish", action="store_true",
                   help="remove every link to it and hide it from Google again")
    g.add_argument("--close", action="store_true",
                   help="keep the page up, but stop asking and say thank you")
    ap.add_argument("--dry-run", action="store_true", help="change nothing, just report")
    args = ap.parse_args()

    cfg = load()

    if args.publish:
        if not (cfg.get("donateUrl") or "").strip():
            die("donateUrl in data/giving-day.json is still empty.\n"
                "       Publishing now would put donate buttons on every page with\n"
                "       nowhere to send people. Paste the donation URL in first.")
        now = dt.datetime.now(dt.timezone.utc)
        if cfg["closesAt_dt"] < now:
            die("closesAt (%s) is in the past. Check the date before publishing."
                % long_date(cfg["closesAt_dt"]))
        set_status("live", args.dry_run)
        cfg["status"] = "live"
    elif args.unpublish:
        set_status("draft", args.dry_run)
        cfg["status"] = "draft"
    elif args.close:
        set_status("closed", args.dry_run)
        cfg["status"] = "closed"

    # the page itself
    page = build(cfg)
    with open(PAGE, encoding="utf-8") as fh:
        before = fh.read()
    page_changed = page != before
    if page_changed and not args.dry_run:
        with open(PAGE, "w", encoding="utf-8") as fh:
            fh.write(page)

    # the rest of the site, only when the live/draft state is being set
    others = []
    if args.publish or args.unpublish or args.close:
        others = set_published(cfg, want_live=(cfg["status"] != "draft"),
                               dry_run=args.dry_run)

    verb = "Would update" if args.dry_run else "Updated"
    print("%s giving-day.html" % verb if page_changed else "No change to giving-day.html")
    if others:
        print("%s %s" % (verb, ", ".join(others)))

    print("\nstatus      %s" % cfg["status"])
    print("date        %s" % long_date(cfg["opensAt_dt"]))
    url = donate_url(cfg, "hero")
    print("donate url  %s" % (url if url else "NOT SET — buttons show 'coming soon'"))
    video = cfg.get("video") or {}
    vid = (video.get("youtubeId") or "").strip()
    vfile = (video.get("file") or "").strip()
    if vid:
        print("film        YouTube %s" % vid)
    elif vfile:
        size = ""
        path = os.path.join(ROOT, vfile)
        if os.path.exists(path):
            size = " (%.1f MB)" % (os.path.getsize(path) / 1048576.0)
        else:
            size = "  *** MISSING — check the path in data/giving-day.json ***"
        print("film        %s%s" % (vfile, size))
    else:
        print("film        NOT SET — player shows a placeholder")
    if cfg["status"] == "draft":
        print("\nThis page is not linked from anywhere and carries noindex.")
        print("When you are ready:  python3 scripts/giving_day.py --publish")


if __name__ == "__main__":
    main()
