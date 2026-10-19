/* ==========================================================================
   GIVING DAY  —  page behaviour

   Loaded only by giving-day.html. Everything here is an enhancement: with
   JavaScript off the page still reads, the date still shows as plain text,
   the donate buttons are still real links, and the film is still a link to
   YouTube. Nothing below is load-bearing.

   The numbers and URLs come from data/giving-day.json, stamped into the HTML
   by scripts/giving_day.py. This file reads them off the markup, never from
   a fetch, so the page works offline and from a file:// URL.
   ========================================================================== */

(function () {
  "use strict";

  if (!document.querySelector(".gd-hero")) return;

  function ready(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  /* ------------------------------------------------------------------
     1. The countdown

     Both timestamps carry Pittsburgh's UTC offset, so Date parses them
     to the right instant and the clock is correct for a visitor in any
     timezone without us doing any timezone maths.
     ------------------------------------------------------------------ */

  function countdown(box) {
    var opens = new Date(box.getAttribute("data-opens")).getTime();
    var closes = new Date(box.getAttribute("data-closes")).getTime();
    if (!opens || !closes) return;          // unparseable: leave the plain date

    var clock = box.querySelector(".gd-countdown__clock");
    var label = box.querySelector(".gd-countdown__label");
    var out = {
      days: box.querySelector("[data-gd-days]"),
      hours: box.querySelector("[data-gd-hours]"),
      mins: box.querySelector("[data-gd-mins]")
    };
    if (!clock || !out.days) return;

    function tick() {
      var now = Date.now();
      var target, phase;

      if (now < opens) {
        target = opens;
        phase = "before";
      } else if (now <= closes) {
        target = closes;
        phase = "live";
      } else {
        // The day is over. Hide the clock and let the stamped copy on the
        // page do the talking.
        box.hidden = true;
        return false;
      }

      var left = Math.max(0, target - now);
      var mins = Math.floor(left / 60000);
      var d = Math.floor(mins / 1440);
      var h = Math.floor((mins % 1440) / 60);
      var m = mins % 60;

      if (out.days.textContent !== String(d)) out.days.textContent = d;
      if (out.hours.textContent !== String(h)) out.hours.textContent = h;
      if (out.mins.textContent !== String(m)) out.mins.textContent = m;

      // On the day itself there are no days left to show, and a "0 days"
      // chit next to a live counter reads like a bug.
      var daysUnit = out.days.parentNode;
      if (daysUnit) daysUnit.hidden = (d === 0);

      if (phase === "live" && !box.classList.contains("is-live")) {
        box.classList.add("is-live");
        if (label) label.textContent = "Giving CMU Day ends in";
      }

      clock.classList.add("is-running");
      return true;
    }

    if (tick() === false) return;
    var timer = setInterval(function () {
      if (tick() === false) clearInterval(timer);
    }, 1000);
  }

  /* ------------------------------------------------------------------
     2. The film

     The poster is a still until someone asks for the video, so arriving
     at this page costs no YouTube request and sets no third-party
     cookie. The click is the user gesture that lets it autoplay.
     ------------------------------------------------------------------ */

  function film(btn) {
    var id = btn.getAttribute("data-gd-play");
    var frame = btn.closest(".gd-film__frame");
    if (!id || !frame) return;

    var title = btn.getAttribute("data-gd-title") || "Giving Day film";
    var iframe = document.createElement("iframe");
    iframe.src = "https://www.youtube-nocookie.com/embed/" + encodeURIComponent(id) +
                 "?autoplay=1&rel=0&modestbranding=1";
    iframe.title = title;
    iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; " +
                   "gyroscope; picture-in-picture; web-share";
    iframe.setAttribute("allowfullscreen", "");
    iframe.setAttribute("loading", "lazy");

    frame.innerHTML = "";
    frame.appendChild(iframe);
    iframe.focus({ preventScroll: true });
  }

  /* ------------------------------------------------------------------
     3. The stroke that fills

     The width is already in the markup as a custom property, so the bar
     is correct before this runs. All we do is hold it at zero until it
     scrolls into view, so the ink appears to run across the page.
     ------------------------------------------------------------------ */

  function bar(el) {
    var target = el.style.getPropertyValue("--gd-pct").trim() || "0%";
    if (!("IntersectionObserver" in window) ||
        matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return;                                // leave it at its final width
    }

    el.style.setProperty("--gd-pct", "0%");
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        el.style.setProperty("--gd-pct", target);
        io.disconnect();
      });
    }, { threshold: 0.4 });
    io.observe(el);
  }

  /* ------------------------------------------------------------------
     4. The sticky donate bar, phones only

     It slides up once the hero's own donate button has scrolled away,
     so there are never two of the same button on screen at once.
     ------------------------------------------------------------------ */

  function sticky(el) {
    var anchor = document.querySelector(".gd-hero__ask .gd-cta-row") ||
                 document.querySelector(".gd-hero");
    if (!anchor || !("IntersectionObserver" in window)) {
      el.classList.add("is-up");
      return;
    }

    var io = new IntersectionObserver(function (entries) {
      el.classList.toggle("is-up", !entries[0].isIntersecting);
    }, { threshold: 0 });
    io.observe(anchor);
  }

  /* ------------------------------------------------------------------
     5. Share

     Shown only where it can actually do something, so nobody gets a
     button that silently fails.
     ------------------------------------------------------------------ */

  function share(wrap) {
    var btn = wrap.querySelector("[data-gd-share-btn]");
    if (!btn) return;

    var canShare = !!(navigator.share);
    var canCopy = !!(navigator.clipboard && navigator.clipboard.writeText);
    if (!canShare && !canCopy) return;

    wrap.hidden = false;

    var payload = {
      title: document.title,
      text: "CMU Wushu is raising money on Giving CMU Day. Ten dollars counts as much as a thousand.",
      url: location.href
    };

    btn.addEventListener("click", function () {
      if (canShare) {
        navigator.share(payload).catch(function () { /* dismissed; nothing to do */ });
        return;
      }
      navigator.clipboard.writeText(payload.url).then(function () {
        var was = btn.textContent;
        btn.textContent = "Link copied";
        setTimeout(function () { btn.textContent = was; }, 2000);
      }).catch(function () {
        btn.textContent = "Copy failed — use your browser's share button";
      });
    });
  }

  /* ---------------------------------- wire it all up ---------------- */

  ready(function () {
    var box = document.querySelector("[data-gd-countdown]");
    if (box) countdown(box);

    document.addEventListener("click", function (e) {
      var play = e.target.closest ? e.target.closest("[data-gd-play]") : null;
      if (play) {
        e.preventDefault();
        film(play);
      }
    });

    var b = document.querySelector("[data-gd-bar]");
    if (b) bar(b);

    var s = document.querySelector(".gd-sticky");
    if (s) sticky(s);

    var sh = document.querySelector("[data-gd-share]");
    if (sh) share(sh);
  });
})();
