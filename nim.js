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

/* The portrait, clicked: a hop and a small gold burst. Garnish only;
   the portrait is fully visible and meaningful without it. */
(function () {
  "use strict";
  var fig = document.querySelector(".hero-figure");
  var img = fig ? fig.querySelector("img") : null;
  if (!fig || !img) return;
  var reduced = false;
  try { reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches; } catch (e) {}
  if (reduced) return;
  img.setAttribute("title", "nim");
  img.addEventListener("click", function () {
    var r = fig.getBoundingClientRect();
    var cx = r.width / 2, cy = r.height / 2 - 10;
    var dirs = [[-56, -40], [56, -40], [-72, 6], [72, 6], [-30, -72], [30, -72], [0, -88], [-88, -24], [88, -24]];
    dirs.forEach(function (d) {
      var s = document.createElement("span");
      s.className = "burst-p";
      s.style.left = cx + "px";
      s.style.top = cy + "px";
      s.style.setProperty("--dx", d[0] + "px");
      s.style.setProperty("--dy", d[1] + "px");
      fig.appendChild(s);
      setTimeout(function () { s.remove(); }, 650);
    });
  });
})();
