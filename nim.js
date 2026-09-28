/* nim.js: home page behavior. Top bar state and the collection filter.
   Plain script, no dependencies, ES5 style. The hero dust stays inline in
   index.html so it can be read in one place. */
(function () {
  "use strict";

  /* ---------- top bar: clear over the hero, solid once scrolled ---------- */
  var bar = document.getElementById("bar");
  if (bar) {
    var queued = false;
    var paint = function () {
      queued = false;
      var y = window.pageYOffset || document.documentElement.scrollTop || 0;
      bar.classList.toggle("is-clear", y < 24);
    };
    window.addEventListener("scroll", function () {
      if (!queued) { queued = true; window.requestAnimationFrame(paint); }
    }, { passive: true });
    paint();
  }

  /* ---------- collection ---------- */
  var grid = document.getElementById("grid");
  if (!grid) return;

  var search = document.getElementById("q");
  var clear = document.getElementById("q-clear");
  var chips = document.getElementById("chips");
  var count = document.getElementById("count");
  var empty = document.getElementById("empty");
  var reset = document.getElementById("reset");
  var activeTag = "";

  function tagsOf(el) {
    return (el.getAttribute("data-tags") || "").split(/\s+/).filter(function (t) { return t; });
  }

  // NOTE: newest first by data-date. Equal dates keep document order, so the
  // tile prepended after <!-- TILES --> wins a tie.
  var tiles = Array.prototype.slice.call(grid.querySelectorAll(".tile"))
    .map(function (el, i) { return { el: el, d: el.getAttribute("data-date") || "", i: i }; })
    .sort(function (a, b) { return a.d < b.d ? 1 : (a.d > b.d ? -1 : a.i - b.i); })
    .map(function (o) { grid.appendChild(o.el); return o.el; });

  var tags = {};
  tiles.forEach(function (el) {
    tagsOf(el).forEach(function (t) { tags[t] = (tags[t] || 0) + 1; });
  });

  function chip(label, tag, n) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "chip px";
    b.setAttribute("data-tag", tag);
    b.setAttribute("aria-pressed", "false");
    b.appendChild(document.createTextNode(label));
    var c = document.createElement("span");
    c.className = "n";
    c.textContent = String(n);
    b.appendChild(c);
    b.addEventListener("click", function () {
      setTag(activeTag === tag ? "" : tag, true);
    });
    chips.appendChild(b);
  }
  chip("all", "", tiles.length);
  Object.keys(tags).sort().forEach(function (t) { chip(t, t, tags[t]); });

  // NOTE: only tags that exist on a tile are accepted from the URL.
  function readTag() {
    var m = /[?&]tag=([^&#]*)/.exec(window.location.search);
    if (!m) return "";
    var t;
    try { t = decodeURIComponent(m[1].replace(/\+/g, " ")); } catch (e) { return ""; }
    return Object.prototype.hasOwnProperty.call(tags, t) ? t : "";
  }

  function writeTag() {
    if (!window.history || !window.history.replaceState) return;
    var keep = window.location.search.replace(/^\?/, "").split("&").filter(function (p) {
      return p && p.split("=")[0] !== "tag";
    });
    if (activeTag) keep.push("tag=" + encodeURIComponent(activeTag));
    var hash = window.location.hash || (activeTag ? "#collection" : "");
    window.history.replaceState(null, "", window.location.pathname + (keep.length ? "?" + keep.join("&") : "") + hash);
  }

  function setTag(t, write) {
    activeTag = t;
    Array.prototype.forEach.call(chips.children, function (c) {
      c.setAttribute("aria-pressed", c.getAttribute("data-tag") === activeTag ? "true" : "false");
    });
    if (write) writeTag();
    apply();
  }

  function apply() {
    var q = search.value.trim().toLowerCase();
    var n = 0;
    tiles.forEach(function (el) {
      var title = el.querySelector(".t");
      var sub = el.querySelector(".s");
      var hay = ((title ? title.textContent : "") + " " + (sub ? sub.textContent : "") + " " + tagsOf(el).join(" ")).toLowerCase();
      var okTag = !activeTag || tagsOf(el).indexOf(activeTag) >= 0;
      var show = okTag && (!q || hay.indexOf(q) >= 0);
      el.hidden = !show;
      if (show) n++;
    });
    count.textContent = n + " of " + tiles.length;
    empty.hidden = n > 0;
    clear.hidden = !search.value;
  }

  search.addEventListener("input", apply);
  search.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && search.value) { search.value = ""; apply(); }
  });
  clear.addEventListener("click", function () {
    search.value = "";
    apply();
    search.focus();
  });
  reset.addEventListener("click", function () {
    search.value = "";
    setTag("", true);
    search.focus();
  });

  setTag(readTag(), false);
})();
