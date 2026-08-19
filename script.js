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
