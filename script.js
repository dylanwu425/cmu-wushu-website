/* ==========================================================================
   CMU Wushu Club — site JavaScript
   This file does exactly one thing: open and close the mobile menu.
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
   On his birthday the whole card becomes the trigger, so clicking his photo
   works too, the third click turns his photo over to the birthday picture, and
   the card gets a cake beside his name, a greeting line and a shimmer, with the
   beans falling once by themselves on page load.

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

  // A few clicks in, the portrait gives way to the birthday picture. It happens
  // once per visit, and only on the day. The path lives in data-birthday-photo
  // on the card, so swapping the picture never means editing this file.
  function turnPhoto() {
    var photo = card.querySelector(".officer__photo");
    var next = card.getAttribute("data-birthday-photo");
    if (!photo || !next) return;

    function apply() {
      photo.src = next;
      photo.alt = photo.getAttribute("data-birthday-alt") || photo.alt;
      photo.classList.remove("is-turning");
    }

    if (calm) {
      apply(); // no fade for anyone who asked for less motion
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
    card.addEventListener("click", function () {
      shower(18, faces);
      clicks++;
      if (clicks === CLICKS_TO_TURN) turnPhoto();
    });
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

    // Fetch the birthday picture up front, so the turn doesn't show a gap.
    var waiting = card.getAttribute("data-birthday-photo");
    if (waiting) new Image().src = waiting;

    shower(22, faces);
  }
})();
