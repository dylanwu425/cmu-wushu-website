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
