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

  function reducedMotion() {
    return !!(window.matchMedia &&
              matchMedia("(prefers-reduced-motion: reduce)").matches);
  }

  /* Someone on a metered or slow connection should not be handed a 14 MB
     film they did not ask for. Both properties are optional and only Chrome
     and friends have them, so an undefined answer means "go ahead". */
  function dataSaver() {
    var c = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    if (!c) return false;
    if (c.saveData) return true;
    return /^(slow-2g|2g)$/.test(c.effectiveType || "");
  }

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
    if (!("IntersectionObserver" in window) || reducedMotion()) {
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
     3b. The film that starts itself

     The markup ships with preload="none" and no autoplay attribute, so
     nothing downloads until this function decides it should. A browser
     will only ever autoplay a muted video, so the caption under the
     player says there is sound to turn on.

     The markup also ships WITH the native control bar, because without
     this script nothing could start the film at all. The bar comes off
     the moment this runs — unconditionally, in every branch — and the two
     small buttons in the corner take over: one to stop it, one to hear
     it. Everything else the bar offered — scrubbing, speed, fullscreen,
     download — is still one right-click away and was only ever chrome
     across the picture.

     Unconditionally matters. The bar used to survive three ways: a
     visitor who asks for reduced motion, a phone in data-saver mode, and
     a browser that refuses the autoplay anyway. All three are common —
     "Reduce motion" is a single switch in macOS Accessibility — and all
     three left the film looking exactly as if the change had never been
     made. Those visitors now get the same bare picture as everyone else,
     paused on its poster, with our own play button to start it.
     ------------------------------------------------------------------ */

  function autoplayFilm(video) {
    video.controls = false;                        // the bar comes off, always
    filmButtons(video);

    // Nothing has been downloaded yet: the markup says preload="none" and
    // only the branch that actually plays the film changes that. A visitor
    // who never presses play never pays for 14 MB.
    if (reducedMotion() || dataSaver()) {
      quietCaption(video);
      return;
    }

    video.muted = true;                            // required, and belt-and-braces
    video.setAttribute("muted", "");
    video.preload = "auto";

    var started = false;
    function go() {
      if (started) return;
      started = true;
      var p = video.play();
      if (p && p.catch) {
        p.catch(function () {
          // Autoplay refused anyway — an iOS low-power screen, say. Leave
          // the picture bare and let our own play button offer the film;
          // handing back the control bar here is what put it on screen
          // for a good share of visitors.
          quietCaption(video);
        });
      }
    }

    // Only once it is actually on screen, so a visitor who never scrolls
    // past the hero on a phone does not pay for the download twice over.
    if (!("IntersectionObserver" in window)) { go(); return; }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          go();
        } else if (started && !video.paused && video.dataset.gdTouched !== "1") {
          video.pause();                           // out of sight, out of mind
        }
      });
    }, { threshold: 0.3 });
    io.observe(video);

    // Hands off once the viewer takes over. Our own two buttons do not
    // count as taking over — they set gdSelf for the one tick it takes the
    // event to arrive — or pausing the film would also stop it ever
    // resuming when it scrolls back into view.
    ["play", "pause", "volumechange", "seeking"].forEach(function (ev) {
      video.addEventListener(ev, function (e) {
        if (e.isTrusted && video.dataset.gdSelf !== "1") {
          video.dataset.gdTouched = "1";
        }
      });
    });
  }

  /* ------------------------------------------------------------------
     3b-i. The caption, for a film that is sitting still

     The stamped caption reads "Playing silently · press for sound",
     which is a lie to anyone whose film never started. The generator
     leaves the alternative on the element for us to swap in.
     ------------------------------------------------------------------ */

  function quietCaption(video) {
    var cap = document.querySelector("[data-gd-caption-quiet]");
    if (cap) cap.textContent = cap.getAttribute("data-gd-caption-quiet");
  }

  /* ------------------------------------------------------------------
     3b-ii. The two buttons that stand in for the control bar
     ------------------------------------------------------------------ */

  function filmButtons(video) {
    var strip = video.parentNode.querySelector("[data-gd-controls]");
    if (!strip) return;
    strip.hidden = false;

    var playBtn  = strip.querySelector('[data-gd-toggle="play"]');
    var soundBtn = strip.querySelector('[data-gd-toggle="sound"]');

    function paint() {
      if (playBtn) {
        var paused = video.paused;
        playBtn.setAttribute("aria-label", paused ? "Play the film" : "Pause the film");
        playBtn.firstElementChild.className =
          "gd-film__icon gd-film__icon--" + (paused ? "play" : "pause");
      }
      if (soundBtn) {
        var off = video.muted;
        soundBtn.setAttribute("aria-pressed", off ? "false" : "true");
        soundBtn.setAttribute("aria-label", off ? "Turn the sound on" : "Turn the sound off");
        soundBtn.firstElementChild.className =
          "gd-film__icon gd-film__icon--" + (off ? "sound" : "sound-on");
      }
    }
    // The markup is stamped for the autoplaying case, so a film that is
    // sitting still would otherwise show a pause button over a still frame.
    paint();

    function self(fn) {                  // mark the next event as ours
      video.dataset.gdSelf = "1";
      fn();
      setTimeout(function () { video.dataset.gdSelf = "0"; }, 0);
    }

    // play() hands back a promise that rejects if the browser says no.
    // Unhandled, that prints a red error in the console of anyone whose
    // browser declined; there is nothing to do about it but keep the
    // button showing the truth.
    function play() {
      var p = video.play();
      if (p && p.catch) p.catch(paint);
    }

    if (playBtn) {
      playBtn.addEventListener("click", function () {
        // For a visitor who never got the autoplay, this press is the
        // first time the file is wanted at all.
        if (video.preload === "none") video.preload = "auto";
        self(function () {
          if (video.paused) { play(); } else { video.pause(); }
        });
      });
      ["play", "pause"].forEach(function (ev) {
        video.addEventListener(ev, paint);
      });
    }

    if (soundBtn) {
      soundBtn.addEventListener("click", function () {
        if (video.preload === "none") video.preload = "auto";
        self(function () { video.muted = !video.muted; });
        // An unmute is also the moment to make sure it is running.
        if (!video.muted && video.paused) self(play);
      });
      video.addEventListener("volumechange", paint);
    }
  }

  /* ------------------------------------------------------------------
     3c. The money counter

     Counts from zero up to the stamped figure when the bar scrolls in,
     in step with the stroke filling underneath it. The element already
     holds the final text, so if any of this fails the right number is
     what stays on screen.
     ------------------------------------------------------------------ */

  function counter(el) {
    var target = parseInt(el.getAttribute("data-gd-count"), 10);
    if (!(target > 0) || reducedMotion() || !("IntersectionObserver" in window)) return;

    var text = el.textContent;                     // "$1,090" or "31"
    var money = text.indexOf("$") === 0;

    function render(n) {
      el.textContent = (money ? "$" : "") + n.toLocaleString("en-US");
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        io.disconnect();
        var started = null;
        var span = 1100;                           // the bar's own fill time
        (function step(now) {
          if (started === null) started = now;
          var t = Math.min(1, (now - started) / span);
          var eased = 1 - Math.pow(1 - t, 3);      // same ease as the stroke
          render(Math.round(target * eased));
          if (t < 1) requestAnimationFrame(step);
          else el.textContent = text;              // land on the stamped text
        })(performance.now());
      });
    }, { threshold: 0.6 });

    render(0);
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

    // Not named `film`: that is the YouTube facade function, and the click
    // handler just below calls it from inside this same scope.
    var selfHosted = document.querySelector("[data-gd-autoplay]");
    if (selfHosted) autoplayFilm(selfHosted);

    var b = document.querySelector("[data-gd-bar]");
    if (b) bar(b);

    var c = document.querySelector("[data-gd-count]");
    if (c) counter(c);

    var s = document.querySelector(".gd-sticky");
    if (s) sticky(s);

    var sh = document.querySelector("[data-gd-share]");
    if (sh) share(sh);
  });
})();
