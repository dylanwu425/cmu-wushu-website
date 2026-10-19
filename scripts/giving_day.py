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
    play_label = "Watch the film" + (" &middot; %s" % esc(vlen) if vlen else "")

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
        page = put(page, "GD:VIDEO", indent("""
<div class="gd-film">
  <div class="gd-film__frame">
    <video class="gd-film__video" controls playsinline preload="none"
           poster="%s" title="%s" width="1920" height="1080">
      <source src="%s" type="video/mp4">
      <p class="gd-cta-note"><a href="%s">Download the film</a></p>
    </video>
  </div>
</div>
<p class="gd-film__caption">%s</p>""" % (poster, vtitle, attr(vfile), attr(vfile), play_label), 10))
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
    show_bar = cfg["status"] in ("live", "closed") and (goal_dollars > 0 or goal_donors > 0)

    # Dollars lead and people follow. The challenge is scored on people, but
    # we are not going to win it, so the honest headline is the money.
    if goal_dollars:
        pct = min(100.0, raised / goal_dollars * 100.0)
        heading = "<b>%s</b> of <span>%s</span>" % (money(raised), money(goal_dollars))
    else:
        pct = min(100.0, (donors / goal_donors * 100.0) if goal_donors else 0.0)
        heading = "<b>%d</b> of <span>%d</span> donors" % (donors, goal_donors)

    people_line = ""
    if goal_donors and donors:
        people_line = '\n      <p class="gd-bar__read">from %d %s</p>' % (
            donors, "person" if donors == 1 else "people")
    elif goal_donors:
        people_line = '\n      <p class="gd-bar__read">Every gift counts once, whatever its size.</p>'

    if closed:
        heading = "<b>%s</b> raised" % money(raised)
        people_line = ('\n      <p class="gd-bar__read">from %d %s</p>'
                       % (donors, "person" if donors == 1 else "people")) if donors else ""

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

    # ---- the tiers
    rows = []
    for tier in (cfg.get("tiers") or []):
        amount = int(tier["amount"])
        flagged = bool(tier.get("flag")) and on
        rows.append(
            '<li class="gd-tier%s">\n'
            '%s'
            '  <span class="gd-tier__amount">%s</span>\n'
            '  <p class="gd-tier__label">%s</p>\n'
            '  %s\n'
            '</li>' % (
                " gd-tier--flagged" if flagged else "",
                ('  <span class="gd-tier__flag">%s</span>\n' % esc(tier["flag"])) if flagged else "",
                money(amount),
                esc(tier.get("label") or ""),
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
