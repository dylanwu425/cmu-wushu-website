/* ==========================================================================
   CMU Wushu Club — site JavaScript
   Opens the mobile menu, runs the photo carousels and Preston's easter egg,
   adds the Ink Night theme's calligraphy and scroll fades, and then the
   motion and live details (paint-in rules, ink bloom, lightbox, next
   practice line), each in its own block at the end.
   You should not need to edit it to update page content.
   ========================================================================== */

(function () {
  "use strict";

  var toggle = document.querySelector(".nav__toggle");
  var menu = document.getElementById("nav-links");

  if (!toggle || !menu) return; // Nothing to do if the nav isn't on this page.

  function closeMenu() {
    menu.classList.remove("is-open");
    toggle.setAttribute("aria-expanded", "false");
  }

  // Tapping the hamburger opens/closes the menu.
  toggle.addEventListener("click", function () {
    var isOpen = menu.classList.toggle("is-open");
    toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
  });

  // Tapping any link closes the menu so the new page isn't hidden behind it.
  menu.addEventListener("click", function (event) {
    if (event.target.closest("a")) closeMenu();
  });

  // Pressing Escape closes the menu and returns focus to the button.
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && menu.classList.contains("is-open")) {
      closeMenu();
      toggle.focus();
    }
  });

  // If the window is widened back to desktop, reset the menu state.
  window.addEventListener("resize", function () {
    if (window.innerWidth > 820) closeMenu();
  });
})();


/* ==========================================================================
   Event photo carousels
   The track already scrolls and snaps on its own via CSS, so this only adds
   the arrow buttons. If JavaScript fails, swiping and scrolling still work.
   ========================================================================== */

(function () {
  "use strict";

  var carousels = document.querySelectorAll(".carousel");

  Array.prototype.forEach.call(carousels, function (carousel) {
    var track = carousel.querySelector(".carousel__track");
    var prev = carousel.querySelector(".carousel__btn--prev");
    var next = carousel.querySelector(".carousel__btn--next");
    if (!track || !prev || !next) return;

    // Nothing to page through if everything already fits on screen.
    function overflows() {
      return track.scrollWidth > track.clientWidth + 4;
    }

    function step() {
      var slide = track.querySelector(".carousel__slide");
      return slide ? slide.getBoundingClientRect().width + 16 : track.clientWidth * 0.8;
    }

    function refresh() {
      if (!overflows()) {
        carousel.classList.remove("is-ready");
        return;
      }
      carousel.classList.add("is-ready");
      // 2px of slack so the last slide reliably counts as "the end"
      prev.disabled = track.scrollLeft <= 2;
      next.disabled = track.scrollLeft >= track.scrollWidth - track.clientWidth - 2;
    }

    prev.addEventListener("click", function () {
      track.scrollBy({ left: -step(), behavior: "smooth" });
    });
    next.addEventListener("click", function () {
      track.scrollBy({ left: step(), behavior: "smooth" });
    });

    track.addEventListener("scroll", refresh, { passive: true });
    window.addEventListener("resize", refresh);
    refresh();

    // Images arriving late change scrollWidth, so re-check as they load.
    Array.prototype.forEach.call(track.querySelectorAll("img"), function (img) {
      if (!img.complete) img.addEventListener("load", refresh, { once: true });
    });
  });
})();


/* ==========================================================================
   Preston's birthday easter egg (About page)
   Year round: clicking the word "beans" in his bio rains beans down his card.
   On his birthday the card wears the party hat photo instead of his portrait,
   the whole card becomes the trigger, the third click turns the photo over to
   the lion dance picture, and the card gets a cake beside his name, a greeting
   line and a shimmer, with the beans falling once by themselves on page load.

   The date lives in data-birthday on his card in about.html, as MM-DD. Edit it
   there; you never need to touch this file. An empty or malformed value simply
   leaves the birthday half switched off. Add ?birthday to the page URL to
   preview the birthday state on any other day.
   ========================================================================== */

(function () {
  "use strict";

  var card = document.querySelector(".officer[data-birthday]");
  if (!card) return; // Not the About page.

  // The rest of the site honours this, so the beans and the shimmer do too.
  var calm = window.matchMedia &&
             window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var CLICKS_TO_TURN = 3; // how many birthday clicks before the photo changes

  function pad(n) {
    return (n < 10 ? "0" : "") + n;
  }

  function isBirthdayToday(value) {
    if (!/^\d{2}-\d{2}$/.test(value)) return false; // blank date: stay quiet
    var now = new Date();
    return value === pad(now.getMonth() + 1) + "-" + pad(now.getDate());
  }

  // Beans remove themselves once they land, so repeated clicks never pile up.
  function shower(count, faces) {
    if (calm) return;

    var stage = card.querySelector(".officer__beans");
    if (!stage) {
      stage = document.createElement("div");
      stage.className = "officer__beans";
      stage.setAttribute("aria-hidden", "true");
      card.appendChild(stage);
    }

    // A ceiling, so a run of impatient clicks can't flood the card.
    if (stage.childElementCount > 120) return;

    for (var i = 0; i < count; i++) {
      var bean = document.createElement("span");
      bean.className = "bean";
      bean.textContent = faces[Math.floor(Math.random() * faces.length)];
      bean.style.left = Math.round(Math.random() * 88) + "%";
      bean.style.animationDelay = (Math.random() * 0.6).toFixed(2) + "s";
      bean.style.animationDuration = (1.8 + Math.random() * 1.2).toFixed(2) + "s";
      bean.style.setProperty("--bean-distance", (card.offsetHeight + 40) + "px");
      bean.style.setProperty("--bean-spin", Math.round(180 + Math.random() * 540) + "deg");
      bean.addEventListener("animationend", function () {
        this.parentNode.removeChild(this);
      });
      stage.appendChild(bean);
    }
  }

  var birthday = isBirthdayToday(card.getAttribute("data-birthday")) ||
                 /[?&]birthday(&|=|$)/.test(window.location.search);
  // The wolf is for his middle name. Beans are listed twice so they stay the
  // most common thing falling even on his birthday — it is still his bio.
  var faces = birthday
    ? ["🫘", "🫘", "🎂", "🎉", "🐺"]  // beans, cake, party, wolf
    : ["🫘"];                     // just beans

  // Put a different picture on the card. Both birthday photos live in data
  // attributes in about.html, so changing either never means editing this file.
  // fade is off for the one applied on load, which has nothing to fade from.
  function setPhoto(pathAttr, altAttr, fade) {
    var photo = card.querySelector(".officer__photo");
    var next = card.getAttribute(pathAttr);
    if (!photo || !next) return;

    function apply() {
      photo.src = next;
      var alt = card.getAttribute(altAttr);
      if (alt) photo.alt = alt;
      photo.classList.remove("is-turning");
    }

    if (!fade || calm) {
      apply(); // no fade on load, or for anyone who asked for less motion
      return;
    }
    photo.classList.add("is-turning");
    window.setTimeout(apply, 320); // matches the CSS fade
  }

  // Off-season, the word "beans" in his bio is the only way in. On his birthday
  // the whole card is live, so tapping his photo works as well. That listener
  // sits on the card and catches the word too as the click bubbles up, so a
  // birthday click fires the shower once rather than twice.
  if (birthday) {
    var clicks = 0;
    var lastTap = 0;
    var fromX = 0;
    var fromY = 0;
    var startedAt = 0;

    function tapped() {
      // A touch is followed by a synthetic click, so the same tap arrives
      // twice. Anything inside 400ms is that echo, not a second tap.
      var now = Date.now();
      if (now - lastTap < 400) return;
      lastTap = now;

      shower(18, faces);
      clicks++;
      if (clicks === CLICKS_TO_TURN) {
        setPhoto("data-birthday-reveal", "data-birthday-reveal-alt", true);
      }
    }

    card.addEventListener("click", tapped);

    // Safari on a phone will not reliably fire a click on a plain <article>,
    // so the card watches the touch itself. It only counts as a tap if the
    // finger barely moved and lifted quickly — otherwise scrolling past his
    // card would set the beans off.
    card.addEventListener("touchstart", function (event) {
      var touch = event.changedTouches[0];
      fromX = touch.clientX;
      fromY = touch.clientY;
      startedAt = Date.now();
    }, { passive: true });

    card.addEventListener("touchend", function (event) {
      var touch = event.changedTouches[0];
      var drift = Math.abs(touch.clientX - fromX) + Math.abs(touch.clientY - fromY);
      if (drift < 12 && Date.now() - startedAt < 500) tapped();
    }, { passive: true });
  } else {
    var trigger = card.querySelector(".bean-trigger");
    if (trigger) {
      trigger.addEventListener("click", function () {
        shower(9, faces);
      });
    }
  }

  if (birthday) {
    card.classList.add("is-birthday");

    // The party hat photo is simply how his card looks all day, so it goes on
    // straight away rather than fading in.
    setPhoto("data-birthday-photo", "data-birthday-photo-alt", false);

    // The cake is decoration; the greeting below is the real text, so screen
    // readers get the message once rather than twice.
    var name = card.querySelector("h3");
    if (name) {
      var cake = document.createElement("span");
      cake.setAttribute("aria-hidden", "true");
      cake.textContent = " 🎂";
      name.appendChild(cake);
    }

    var line = document.createElement("p");
    line.className = "officer__bday";
    line.textContent = "Happy birthday, Preston!";
    card.appendChild(line);

    // Fetch the reveal up front, so the turn doesn't show a gap.
    var waiting = card.getAttribute("data-birthday-reveal");
    if (waiting) new Image().src = waiting;

    shower(22, faces);
  }
})();


/* ==========================================================================
   Ink Night theme: home page calligraphy and scroll fades
   1. Adds the home hero's brushed 武术, seal and caption. The photo and its
      ink-splash mask are pure CSS; the text in index.html is never touched.
   2. Fades sections in as they scroll into view. No blur: a short fade and
      a small rise, then the element is handed back to its normal styles.
   Nothing is hidden unless this file runs, so the page reads fine without it.
   ========================================================================== */

(function () {
  "use strict";

  var root = document.documentElement;
  var calm = window.matchMedia &&
             window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (!calm) root.classList.add("night-motion");

  function ready(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }


  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text) node.textContent = text;
    return node;
  }

  function buildHero() {
    var hero = document.querySelector(".hero");
    if (!hero) return;

    var callig = el("div", "night-callig");
    callig.setAttribute("aria-hidden", "true");
    callig.appendChild(el("span", "night-callig__small", "卡内基梅隆大学 · 武术社"));
    callig.appendChild(el("span", "night-callig__big", "武术"));

    var seal = el("span", "ink-seal", "卡梅武术"); // CMU wushu, read right to left
    seal.setAttribute("aria-hidden", "true");

    var caption = el("p", "night-caption", "Oops!… It’s DS Again · Dancers Symposium, April 2026");
    caption.setAttribute("aria-hidden", "true");

    hero.appendChild(callig);
    hero.appendChild(seal);
    hero.appendChild(caption);

    window.requestAnimationFrame(function () { hero.classList.add("is-playing"); });
  }

  function reveals() {
    if (calm || !("IntersectionObserver" in window)) return;

    var selector = [
      "main .section-header",
      "main .split > *",
      "main .grid > *",
      "main .contact-grid > *",
      "main .steps > li",
      "main .gallery-group",
      "main .table-wrap",
      "main .cal-embed",
      ".cta-band .container"
    ].join(",");

    var nodes = [];
    Array.prototype.forEach.call(document.querySelectorAll(selector), function (node) {
      if (nodes.indexOf(node) !== -1) return;
      // Anything already on screen stays put; only what is below the fold
      // waits for its turn.
      if (node.getBoundingClientRect().top < window.innerHeight * 0.92) return;
      var index = 0;
      var sib = node.previousElementSibling;
      while (sib) {
        if (sib.classList.contains("night-reveal")) index++;
        sib = sib.previousElementSibling;
      }
      node.style.transitionDelay = Math.min(index, 4) * 70 + "ms";
      node.classList.add("night-reveal");
      nodes.push(node);
    });

    function settle(node) {
      node.classList.remove("night-reveal", "is-in");
      node.style.transitionDelay = "";
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var node = entry.target;
        io.unobserve(node);
        node.classList.add("is-in");
        // Hand the element back so hover lifts use their own timing again.
        window.setTimeout(function () { settle(node); }, 800);
      });
    }, { rootMargin: "0px 0px -6% 0px", threshold: 0.06 });

    nodes.forEach(function (node) { io.observe(node); });
  }

  ready(function () {
    buildHero();
    reveals();
  });
})();

/* ==========================================================================
   A photo hidden behind a word (About page)
   Someone's bio can turn one word into a quiet trigger, the way "beans"
   works on Preston's card: clicking it opens a photo full-size in the same
   viewer the galleries use. The word is a real button, so a keyboard reaches
   it too, and it is styled to read as ordinary text so finding it is the
   point. With JavaScript off it is just a word, and the photo stays hidden.
   ========================================================================== */

(function () {
  "use strict";

  document.addEventListener("click", function (event) {
    var word = event.target.closest && event.target.closest(".secret-trigger");
    if (!word) return;
    var card = word.closest("li, article");
    var photo = card && card.querySelector(".secret-photo");
    // The viewer is listening for clicks on photos, so handing it one is all
    // this has to do.
    if (photo) photo.click();
  });
})();


/* ==========================================================================
   Cards with two photos (About page: members, and officers who have one)
   Hovering swaps the first photo for the second in CSS alone. Phones have
   no hover, so tapping the photo (or pressing Enter or Space on it) flips it
   instead: this only toggles aria-pressed, and the styles do the rest. With
   JavaScript off the first photo simply stays.
   ========================================================================== */

(function () {
  "use strict";

  if (!document.querySelector(".photo-swap")) return; // No such card here.

  document.addEventListener("click", function (event) {
    var button = event.target.closest(".photo-swap");
    if (!button) return;
    var on = button.getAttribute("aria-pressed") === "true";
    button.setAttribute("aria-pressed", on ? "false" : "true");
  });
})();


/* ==========================================================================
   MOTION AND LIVE DETAILS (styles.css section 10)
   ========================================================================== */


/* ==========================================================================
   Preview layer: Polish — behaviour
   Adds html.polish-motion when the visitor has not asked for reduced motion,
   then marks each brush rule .is-painted as it scrolls into view so
   styles.css section 10 can paint it in. Without this file every rule simply shows.
   ========================================================================== */

(function () {
  "use strict";

  var root = document.documentElement;
  var calm = window.matchMedia &&
             window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (calm || !("IntersectionObserver" in window)) return;

  root.classList.add("polish-motion");

  function ready(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  ready(function () {
    var rules = document.querySelectorAll(".eyebrow, .accent-rule");
    if (!rules.length) return;

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        io.unobserve(entry.target);
        entry.target.classList.add("is-painted");
      });
    }, { rootMargin: "0px 0px -6% 0px", threshold: 0.2 });

    Array.prototype.forEach.call(rules, function (node) { io.observe(node); });
  });
})();


/* ==========================================================================
   Bloom (home only) — the hero's ink bloom (wide screens only).
   On load a blot appears where the stage photo will be, its edge tears and
   spreads for about a second, and the photo develops inside it.

   How: the theme draws the hero photo as .hero::before, masked by the
   --splash drawing in styles.css. This script never touches that element's
   box, transform or picture. It only swaps the MASK for an animated copy of
   the same drawing: the same SVG with <animate> elements inside it, so the
   browser itself moves the tear, the pool and the drops every frame, as
   smoothly as the machine allows. The animation ends on exactly the shapes
   the theme's drawing has, and then the --splash variable is handed back to
   the theme, so there is nothing to hand off and nothing that can move. If
   anything goes wrong the theme's plain fade runs instead.
   ========================================================================== */

(function () {
  "use strict";

  var root = document.documentElement;
  var calm = window.matchMedia &&
             window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var wide = window.matchMedia && window.matchMedia("(min-width: 960px)").matches;

  if (calm || !wide || !document.querySelector || !window.requestAnimationFrame) return;
  if (!/(^|\s)home(\s|$)/.test(root.getAttribute("data-page") || "")) return;

  var DURATION = 1.3;  // seconds, blot to full splash (the SVG's own clock)
  var SETTLE = 250;    // ms of margin after that before handing the mask back

  // Arm straight away: styles.css section 10 holds the photo at opacity 0 and the
  // calligraphy back until we start (see the armed rules there).
  root.classList.add("bloom-armed");

  function ready(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  // Short number for an SVG attribute: 380 stays "380", 152.5 -> "152.5".
  function num(v) { return String(Math.round(v * 100) / 100); }

  /* The theme's --splash drawing, written out as a template. With `anim`
     false it is character for character the value in styles.css (checked
     below). With `anim` true the same shapes carry <animate> elements: the
     pool grows from 40% of its size, the torn edge calms from 520 to 150,
     and the tails and drops fade in once the pool is well under way. Every
     animation freezes on the theme's own numbers. */
  function splash(anim) {
    var EASE = " calcMode='spline' keySplines='0.2 0.8 0.2 1'";
    var dur = " dur='" + num(DURATION) + "s' fill='freeze'";
    function e(cx, cy, rx, ry) {
      if (!anim) return "<ellipse cx='" + cx + "' cy='" + cy + "' rx='" + rx + "' ry='" + ry + "'/>";
      return "<ellipse cx='" + cx + "' cy='" + cy + "' rx='" + num(rx * 0.4) + "' ry='" + num(ry * 0.4) + "'>" +
        "<animate attributeName='rx' values='" + num(rx * 0.4) + ";" + rx + "'" + EASE + dur + "/>" +
        "<animate attributeName='ry' values='" + num(ry * 0.4) + ";" + ry + "'" + EASE + dur + "/>" +
        "</ellipse>";
    }
    var tear = anim
      ? "<feDisplacementMap in='SourceGraphic' in2='n' scale='520' xChannelSelector='R' yChannelSelector='G'>" +
          "<animate attributeName='scale' values='520;150'" + EASE + dur + "/></feDisplacementMap>"
      : "<feDisplacementMap in='SourceGraphic' in2='n' scale='150' xChannelSelector='R' yChannelSelector='G'/>";
    // Tails and drops: hidden at first, in by the time the pool settles.
    var late = anim
      ? " opacity='0'><animate attributeName='opacity' values='0;1' begin='" + num(DURATION * 0.4) + "s' dur='" + num(DURATION * 0.45) + "s' fill='freeze'/"
      : "";
    // The browser keeps an SVG image, clock and all, for as long as its
    // address is the same, so a second visit would get the finished drawing
    // and no bloom. A stamp on the animated copy makes every visit's address
    // new; the still copy must stay exactly the theme's, so it has none.
    var stamp = anim ? " data-run='" + Date.now().toString(36) + "'" : "";
    return "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1000 700' preserveAspectRatio='none'" + stamp + ">" +
      "<filter id='a' x='-20%25' y='-20%25' width='140%25' height='140%25'>" +
        "<feTurbulence type='fractalNoise' baseFrequency='0.008' numOctaves='4' seed='4' result='n'/>" +
        tear +
      "</filter>" +
      "<filter id='b' x='-20%25' y='-80%25' width='140%25' height='260%25'>" +
        "<feTurbulence type='fractalNoise' baseFrequency='0.003 0.12' numOctaves='3' seed='8' result='n'/>" +
        "<feDisplacementMap in='SourceGraphic' in2='n' scale='46' xChannelSelector='R' yChannelSelector='G'/>" +
      "</filter>" +
      "<filter id='c' x='-50%25' y='-50%25' width='200%25' height='200%25'>" +
        "<feTurbulence type='fractalNoise' baseFrequency='0.06' numOctaves='2' seed='2' result='n'/>" +
        "<feDisplacementMap in='SourceGraphic' in2='n' scale='12' xChannelSelector='R' yChannelSelector='G'/>" +
      "</filter>" +
      "<g filter='url(%23a)'>" + e(560, 345, 380, 265) + e(340, 420, 210, 150) + e(760, 230, 200, 150) + "</g>" +
      "<g filter='url(%23b)'" + late + "><rect x='150' y='582' width='700' height='34' rx='17'/><rect x='230' y='150' width='400' height='26' rx='13'/></g>" +
      "<g filter='url(%23c)'" + late + "><circle cx='120' cy='262' r='17'/><circle cx='82' cy='314' r='7'/><circle cx='150' cy='330' r='4'/><circle cx='930' cy='80' r='13'/><circle cx='968' cy='128' r='6'/><circle cx='900' cy='650' r='11'/><circle cx='205' cy='655' r='6'/><circle cx='955' cy='520' r='5'/></g>" +
      "</svg>";
  }

  // The theme's own value, e.g. url("data:image/svg+xml,<svg ...>").
  function themeSplash() {
    var v = window.getComputedStyle(root).getPropertyValue("--splash") || "";
    return v.trim();
  }

  function fallback(hero) {
    hero.style.removeProperty("--splash");
    root.classList.remove("bloom-armed");
    hero.classList.remove("bloom-run");
    hero.classList.add("bloom-fallback");
  }

  function play(hero) {
    var theme = themeSplash();
    if (!/^url\(/.test(theme)) return fallback(hero);

    // Our frozen end state must be the theme's drawing. If it ever is not
    // (someone edited --splash in styles.css), the theme's value is still
    // what ends up on the element, so nothing can jump; the bloom just
    // settles onto a slightly different shape in its last step.
    if ('url("' + splash(false) + '")' !== theme && window.console && console.warn) {
      console.warn("bloom: --splash in styles.css differs from the bloom template; the bloom ends on the theme's drawing.");
    }

    // The animated drawing's clock starts when the browser loads it, so it
    // goes on in the same breath as the photo starts to develop.
    hero.style.setProperty("--splash", 'url("' + splash(true) + '")');
    hero.classList.add("bloom-run");

    window.setTimeout(function () {
      // Back to the theme's own drawing: the same shapes the animation
      // froze on, so the picture does not change here.
      hero.style.removeProperty("--splash");
      hero.classList.add("bloom-done");
    }, DURATION * 1000 + SETTLE);
  }

  ready(function () {
    var hero = document.querySelector(".hero");
    if (!hero) { root.classList.remove("bloom-armed"); return; }
    try {
      play(hero);
    } catch (e) {
      fallback(hero);
    }
  });
})();


/* ==========================================================================
   Gallery layer — the lightbox
   Click (or press Enter on) any photo in an Events page carousel, or an
   officer's photo on the About page, and it opens full-size in a <dialog>:
   gold hairline frame, the alt text as a caption on a paper strip, arrows,
   ← → keys and swipe to move within the same carousel, Esc or the seal to
   close. Focus goes back to the photo you were on.

   Nothing here touches the HTML officers edit: it reads the same
   <figure class="carousel__slide"> blocks they already paste in. Preston's
   card is skipped: it has its own click behaviour for his birthday.
   ========================================================================== */

(function () {
  "use strict";

  if (typeof HTMLDialogElement === "undefined") return; // very old browser: nothing changes

  var root = document.documentElement;
  var calm = window.matchMedia &&
             window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function ready(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  function el(tag, className, attrs) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (attrs) Object.keys(attrs).forEach(function (k) { node.setAttribute(k, attrs[k]); });
    return node;
  }

  var PHOTO = ".carousel__slide img, .officer:not([data-birthday]) .officer__photo, .secret-photo";

  // Every photo that opens the lightbox. Officer photos on the About page
  // form one group; each carousel is its own group; a secret photo is shown
  // on its own, with no arrows to anywhere else.
  function groupFor(img) {
    if (img.classList.contains("secret-photo")) return [img];
    var track = img.closest(".carousel__track");
    if (track) return Array.prototype.slice.call(track.querySelectorAll(".carousel__slide img"));
    return Array.prototype.slice.call(document.querySelectorAll(".officer:not([data-birthday]) .officer__photo"));
  }

  var dialog, stage, image, caption, count, prev, next, close;
  var group = [];
  var index = 0;
  var opener = null;

  function build() {
    dialog = el("dialog", "gallery-lightbox", { "aria-label": "Photo viewer", tabindex: "-1" });

    var figure = el("figure", "gallery-lightbox__figure");
    stage = el("div", "gallery-lightbox__stage");
    image = el("img", "gallery-lightbox__img", { alt: "" });
    stage.appendChild(image);

    caption = el("figcaption", "gallery-lightbox__caption");
    count = el("span", "gallery-lightbox__count");
    var text = el("span", "gallery-lightbox__text");
    caption.appendChild(count);
    caption.appendChild(text);

    figure.appendChild(stage);
    figure.appendChild(caption);

    prev = el("button", "gallery-lightbox__btn gallery-lightbox__btn--prev", { type: "button", "aria-label": "Previous photo" });
    prev.innerHTML = "&lsaquo;";
    next = el("button", "gallery-lightbox__btn gallery-lightbox__btn--next", { type: "button", "aria-label": "Next photo" });
    next.innerHTML = "&rsaquo;";
    close = el("button", "gallery-lightbox__close", { type: "button", "aria-label": "Close" });
    close.innerHTML = "&times;";

    dialog.appendChild(prev);
    dialog.appendChild(figure);
    dialog.appendChild(next);
    dialog.appendChild(close);
    document.body.appendChild(dialog);

    prev.addEventListener("click", function () { go(-1); });
    next.addEventListener("click", function () { go(1); });
    close.addEventListener("click", function () { dialog.close(); });

    // Clicking the dark ground (not the print, caption or buttons) closes.
    dialog.addEventListener("click", function (e) {
      if (e.target === dialog || e.target === figure || e.target === stage) dialog.close();
    });

    dialog.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight") { e.preventDefault(); go(1); }
      else if (e.key === "ArrowLeft") { e.preventDefault(); go(-1); }
      else if (e.key === "Home") { e.preventDefault(); show(0); }
      else if (e.key === "End") { e.preventDefault(); show(group.length - 1); }
    });

    // Swipe left / right on a phone.
    var fromX = 0, fromY = 0, startedAt = 0;
    dialog.addEventListener("touchstart", function (e) {
      var t = e.changedTouches[0];
      fromX = t.clientX; fromY = t.clientY; startedAt = Date.now();
    }, { passive: true });
    dialog.addEventListener("touchend", function (e) {
      var t = e.changedTouches[0];
      var dx = t.clientX - fromX, dy = t.clientY - fromY;
      if (Date.now() - startedAt < 600 && Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy) * 1.5) {
        go(dx < 0 ? 1 : -1);
      }
    }, { passive: true });

    dialog.addEventListener("close", function () {
      root.classList.remove("gallery-lock");
      var current = group[index];
      if (current) {
        // Bring the carousel to the print that was open, then hand focus back.
        if (current !== opener) {
          var slide = current.closest(".carousel__slide");
          if (slide) slide.scrollIntoView({ inline: "center", block: "nearest", behavior: "instant" });
        }
        // A secret photo is hidden and cannot hold focus, so it goes back to
        // the word in the bio that opened it.
        var back = current;
        if (current.classList.contains("secret-photo")) {
          var card = current.closest("li, article");
          back = (card && card.querySelector(".secret-trigger")) || document.body;
        }
        back.focus({ preventScroll: true });
      }
      image.removeAttribute("src");
      group = [];
      opener = null;
    });
  }

  function show(i) {
    if (i < 0 || i >= group.length) return;
    var turning = i !== index && !calm;
    index = i;
    var src = group[i].currentSrc || group[i].src;

    if (turning) {
      stage.classList.remove("is-turning");
      void stage.offsetWidth; // restart the little settle
      stage.classList.add("is-turning");
    }
    image.src = src;
    image.alt = group[i].alt || "";
    caption.lastChild.textContent = group[i].alt || "";
    // Gallery photos carry no caption, so the strip is just the position in
    // the set; a photo shown on its own has no position worth printing.
    count.textContent = group.length > 1 ? (i + 1) + " / " + group.length : "";
    caption.style.display = (group[i].alt || group.length > 1) ? "" : "none";

    prev.disabled = i === 0;
    next.disabled = i === group.length - 1;
    // A photo shown on its own has nowhere to page to.
    var alone = group.length < 2;
    prev.hidden = alone;
    next.hidden = alone;

    // Fetch the neighbours so the next turn shows no gap.
    [i - 1, i + 1].forEach(function (n) {
      if (group[n]) new Image().src = group[n].currentSrc || group[n].src;
    });
  }

  function go(step) { show(index + step); }

  function open(img) {
    group = groupFor(img);
    index = Math.max(0, group.indexOf(img));
    opener = img;
    root.classList.add("gallery-lock");
    show(index);
    dialog.showModal();
    dialog.focus();
  }

  ready(function () {
    build();

    // Photos become real controls: focusable, and Enter / Space opens them.
    Array.prototype.forEach.call(document.querySelectorAll(PHOTO), function (img) {
      if (img.classList.contains("secret-photo")) return; // reached by its word
      img.setAttribute("tabindex", "0");
      img.setAttribute("role", "button");
      img.setAttribute("aria-haspopup", "dialog");
    });

    document.addEventListener("click", function (e) {
      var img = e.target.closest && e.target.closest(PHOTO);
      if (!img) return;
      e.preventDefault();
      open(img);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key !== "Enter" && e.key !== " ") return;
      var img = e.target.closest && e.target.closest(PHOTO);
      if (!img) return;
      e.preventDefault();
      open(img);
    });

    root.classList.add("gallery-ready");
  });
})();


/* ==========================================================================
   Practice layer: the "Next practice" line under the home hero.
   Reads data/live.json, which scripts/update_events.py rewrites from the
   club calendar every day, picks the first session still to come (or a
   one-off event if that is sooner) and writes one line into the hero.
   Home page only. Nothing is in the HTML: if the script or the fetch fails,
   the hero is simply the hero. Times are always shown in Pittsburgh time.
   ========================================================================== */

(function () {
  "use strict";

  var ZONE = "America/New_York";
  var page = document.documentElement.getAttribute("data-page") || "";
  if (page !== "home" || !window.fetch) return;

  function ready(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn);
    } else {
      fn();
    }
  }

  function el(tag, className, text) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }

  /* ---------- Pittsburgh clock helpers ---------- */

  // Calendar date of a moment in Pittsburgh, as a day number, so "tomorrow"
  // means tomorrow there even for someone browsing from another time zone.
  function dayNumber(date) {
    var parts = new Intl.DateTimeFormat("en-US", {
      timeZone: ZONE, year: "numeric", month: "numeric", day: "numeric"
    }).formatToParts(date);
    var v = {};
    parts.forEach(function (p) { v[p.type] = p.value; });
    return Math.round(Date.UTC(+v.year, +v.month - 1, +v.day) / 864e5);
  }

  function fmt(date, opts) {
    opts.timeZone = ZONE;
    return new Intl.DateTimeFormat("en-US", opts).format(date);
  }

  function clock(date) {
    return fmt(date, { hour: "numeric", minute: "2-digit" });
  }

  // "7:00–9:00 PM" when both halves share a suffix, "11:30 AM–1:00 PM" otherwise.
  function span(start, end) {
    if (!end) return clock(start);
    var a = clock(start), b = clock(end);
    if (a.slice(-2) === b.slice(-2)) a = a.slice(0, -3);
    return a + "–" + b;
  }

  function relative(diff, inProgress, start) {
    if (inProgress) return "happening now";
    if (diff <= 0) return "today at " + clock(start).replace(":00", "");
    if (diff === 1) return "tomorrow";
    if (diff < 14) return "in " + diff + " days";
    var weeks = Math.round(diff / 7);
    return "in " + weeks + " week" + (weeks === 1 ? "" : "s");
  }

  /* ---------- pick the next session ---------- */

  function pickNext(data, now) {
    var soonest = null;
    function consider(item, kind) {
      var start = new Date(item.start);
      var end = item.end ? new Date(item.end) : null;
      if (isNaN(start)) return;
      // A session already under way still counts until it ends; an all-day
      // event counts for the whole of its day.
      var lastMoment = end || (item.allDay ? new Date(start.getTime() + 864e5) : start);
      if (lastMoment <= now) return;
      if (!soonest || start < soonest.start) {
        soonest = { start: start, end: end, item: item, kind: kind };
      }
    }
    (data.practices || []).forEach(function (p) { consider(p, "practice"); });
    (data.events || []).forEach(function (e) { consider(e, "event"); });
    return soonest;
  }

  /* ---------- the line ---------- */

  function build(next, now) {
    var isPractice = next.kind === "practice";
    var diff = dayNumber(next.start) - dayNumber(now);
    var inProgress = next.start <= now;

    var when;
    if (next.item.allDay) {
      when = fmt(next.start, { weekday: "long", month: "long", day: "numeric" });
    } else {
      var day = diff < 7
        ? fmt(next.start, { weekday: "long" })
        : fmt(next.start, { weekday: "short", month: "short", day: "numeric" });
      when = day + " · " + span(next.start, next.end);
    }

    var strip = el("aside", "practice");
    strip.setAttribute("aria-label", isPractice ? "Next practice" : "Next event");

    var seal = el("span", "practice__seal", isPractice ? "练" : "演"); // practise / perform
    seal.setAttribute("aria-hidden", "true");
    strip.appendChild(seal);

    var body = el("div", "practice__body");
    body.appendChild(el("span", "practice__label",
      isPractice ? "Next practice" : "Next up · " + next.item.title));

    var line = el("span", "practice__line");
    line.appendChild(el("span", "practice__when", when));
    if (next.item.location) {
      line.appendChild(el("span", "practice__where", next.item.location));
    }
    body.appendChild(line);
    strip.appendChild(body);

    var rel = el("span", "practice__rel", relative(diff, inProgress, next.start));
    if (inProgress) rel.classList.add("practice__rel--now");
    strip.appendChild(rel);

    return strip;
  }

  ready(function () {
    // It goes under the hero buttons, inside the text column, so the
    // sections after the hero keep their places.
    var inner = document.querySelector("main > .hero .hero__inner");
    if (!inner) return;

    // The line's space is reserved straight away, before the data arrives,
    // so the hero is its final height from the first paint. Otherwise the
    // line would land mid-way through the ink bloom and the photo, which is
    // sized off the hero, would visibly grow. The placeholder is invisible
    // (visibility, not opacity, so the theme's rise animation can't reveal
    // it) and only holds the height that styles.css section 10 gives every line.
    var strip = el("aside", "practice practice--pending");
    strip.setAttribute("aria-hidden", "true");
    inner.appendChild(strip);

    // No session to show: let go of the space, but only once the hero has
    // finished playing, so nothing moves while the visitor is watching it.
    function release() {
      var hero = inner.closest(".hero");
      var settled = function () { if (strip.parentNode) strip.parentNode.removeChild(strip); };
      var armed = document.documentElement.classList.contains("bloom-armed");
      if (armed && hero && !hero.classList.contains("bloom-done")) {
        var watch = new MutationObserver(function () {
          if (hero.classList.contains("bloom-done") || hero.classList.contains("bloom-fallback")) {
            watch.disconnect();
            window.setTimeout(settled, 600);
          }
        });
        watch.observe(hero, { attributes: true, attributeFilter: ["class"] });
        window.setTimeout(function () { watch.disconnect(); settled(); }, 4000);
      } else {
        window.setTimeout(settled, 2200);
      }
    }

    fetch("data/live.json", { cache: "no-cache" })
      .then(function (r) { return r.ok ? r.json() : Promise.reject(); })
      .then(function (data) {
        var now = new Date();
        var next = pickNext(data, now);
        if (!next) return release();
        var built = build(next, now);
        strip.className = built.className;
        strip.setAttribute("aria-label", built.getAttribute("aria-label"));
        strip.removeAttribute("aria-hidden");
        while (built.firstChild) strip.appendChild(built.firstChild);
        // Force a style flush so the fade below starts from hidden.
        void strip.offsetWidth;
        strip.classList.add("practice--in");
      })
      .catch(release);
  });
})();
