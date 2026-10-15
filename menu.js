/* menu.js: the Garden Menu. One full-screen door set for every portal
   page, stamped by scripts/grow.py between MENU markers. This script
   only opens and closes it; the links are plain HTML and the noscript
   style in the stamped block keeps them reachable without JS.
   Plain script, no dependencies, ES5 style. */
(function () {
  "use strict";
  var btn = document.getElementById("menu-btn");
  var menu = document.getElementById("garden-menu");
  if (!btn || !menu) return;
  var closeBtn = menu.querySelector(".menu-close");
  var lastFocus = null;

  function open() {
    lastFocus = document.activeElement;
    menu.hidden = false;
    void menu.offsetWidth;
    menu.classList.add("open");
    btn.setAttribute("aria-expanded", "true");
    document.documentElement.style.overflow = "hidden";
    if (closeBtn) closeBtn.focus();
  }
  function close() {
    menu.classList.remove("open");
    btn.setAttribute("aria-expanded", "false");
    document.documentElement.style.overflow = "";
    setTimeout(function () { menu.hidden = true; }, 240);
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  btn.addEventListener("click", function () {
    if (menu.classList.contains("open")) close(); else open();
  });
  if (closeBtn) closeBtn.addEventListener("click", close);
  menu.addEventListener("click", function (e) {
    if (e.target === menu) close();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && menu.classList.contains("open")) close();
  });
})();
