/* nim.js: the theme toggle. The theme itself is set inline in each
   page head (localStorage "nim-theme", else prefers-color-scheme) so
   there is no flash; this script only flips it and remembers.
   Plain script, no dependencies. */
(function () {
  "use strict";
  var btn = document.querySelector(".theme-toggle");
  if (!btn) return;
  function sync() {
    var dark = document.documentElement.getAttribute("data-theme") === "dark";
    btn.setAttribute("aria-pressed", dark ? "true" : "false");
    btn.setAttribute("aria-label", dark ? "Switch to light theme" : "Switch to dark theme");
  }
  btn.addEventListener("click", function () {
    var next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("nim-theme", next); } catch (e) {}
    sync();
  });
  sync();
})();
