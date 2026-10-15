/* nim.js: home page behavior. The collection filter, plus the life layer:
   tile stagger indices, animated filtering, counting stats, the cloud.
   Plain script, no dependencies, ES5 style. Everything here is
   enhancement; the page is complete without it. */
(function () {
  "use strict";

  var reduced = false;
  try {
    reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch (e) {}

  /* ---------- the cloud ---------- */
  var cloud = document.getElementById("cloud");
  if (cloud) {
    var svg = cloud.querySelector(".cloud-svg");
    var pupils = svg ? svg.querySelectorAll(".pupil") : [];
    // NOTE: the gaze follows the cursor in 2px steps, never smoothly.
    // Pixel motion is the house law (style.css, v2).
    if (!reduced) {
      document.addEventListener("mousemove", function (e) {
        var r = cloud.getBoundingClientRect();
        var cx = r.left + r.width / 2, cy = r.top + r.height / 3;
        var dx = e.clientX - cx, dy = e.clientY - cy;
        var step = function (v) { return Math.max(-4, Math.min(4, Math.round(v / 160) * 2)); };
        var gx = step(dx), gy = step(dy);
        Array.prototype.forEach.call(pupils, function (p) {
          p.setAttribute("transform", "translate(" + gx + " " + gy + ")");
        });
      }, { passive: true });
    }
    function burst(n) {
      if (reduced) return;
      var r = cloud.getBoundingClientRect();
      for (var i = 0; i < n; i++) {
        var b = document.createElement("span");
        b.className = "px-bit" + (i % 3 === 0 ? " bone" : "");
        b.style.left = (r.left + r.width / 2 + (Math.random() * 80 - 40)) + "px";
        b.style.top = (r.top + r.height / 3) + "px";
        b.style.setProperty("--dx", (Math.random() * 160 - 80) + "px");
        b.style.setProperty("--dy", (40 + Math.random() * 90) + "px");
        document.body.appendChild(b);
        (function (el) { setTimeout(function () { el.remove(); }, 900); })(b);
      }
    }
    cloud.addEventListener("click", function () {
      cloud.classList.remove("hop");
      void cloud.offsetWidth;
      cloud.classList.add("hop");
      burst(10);
    });
    // NOTE: type n, i, m anywhere and it rains gold, briefly.
    var seq = "";
    document.addEventListener("keydown", function (e) {
      if (e.target && (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA")) return;
      if (!/^[a-z]$/i.test(e.key || "")) return;
      seq = (seq + e.key.toLowerCase()).slice(-3);
      if (seq === "nim" && !reduced) {
        for (var i = 0; i < 26; i++) {
          var d = document.createElement("span");
          d.className = "rain-bit";
          d.style.left = (Math.random() * 96) + "vw";
          d.style.animationDelay = (Math.random() * 0.5) + "s";
          if (i % 4 === 0) d.style.background = "#ece5d3";
          document.body.appendChild(d);
          (function (el) { setTimeout(function () { el.remove(); }, 2600); })(d);
        }
        seq = "";
      }
    });
  }

  /* ---------- ticker: duplicate the track so the belt loops seamlessly ---------- */
  var track = document.getElementById("ticker-track");
  if (track) track.innerHTML += track.innerHTML;

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

  tiles.forEach(function (el, i) { el.style.setProperty("--i", String(i % 8)); });

  var tags = {};
  tiles.forEach(function (el) {
    tagsOf(el).forEach(function (t) { tags[t] = (tags[t] || 0) + 1; });
  });

  /* ---------- stats: count the garden from the tiles themselves ---------- */
  var counted = false;
  function runCounts() {
    if (counted) return;
    counted = true;
    Array.prototype.forEach.call(document.querySelectorAll("[data-count]"), function (el) {
      var kind = el.getAttribute("data-count");
      var target = kind === "all" ? tiles.length : (tags[kind] || 0);
      if (reduced || !("IntersectionObserver" in window)) { el.textContent = String(target); return; }
      var n = 0;
      var iv = setInterval(function () {
        n += 1;
        if (n >= target) { n = target; clearInterval(iv); }
        el.textContent = String(n);
      }, 60);
    });
  }
  var statsEl = document.querySelector(".stats");
  if (statsEl && "IntersectionObserver" in window && !reduced) {
    var so = new IntersectionObserver(function (es) {
      es.forEach(function (en) { if (en.isIntersecting) { runCounts(); so.disconnect(); } });
    }, { threshold: 0.4 });
    so.observe(statsEl);
  } else {
    runCounts();
  }

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
  // NOTE: the homepage filters by kind only (essay, experiment, weekly,
  // note). Topic filtering lives on the shelves (essays/, experiments/),
  // where the full tag list belongs. A ?tag= URL naming any real tag
  // still filters here; it just gets no chip of its own.
  chip("all", "", tiles.length);
  ["essay", "experiment", "weekly", "note"].forEach(function (t) {
    if (tags[t]) chip(t === "essay" ? "essays" : t === "experiment" ? "experiments" : t, t, tags[t]);
  });

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

  function setTag(t, write, instant) {
    activeTag = t;
    Array.prototype.forEach.call(chips.children, function (c) {
      c.setAttribute("aria-pressed", c.getAttribute("data-tag") === activeTag ? "true" : "false");
    });
    if (write) writeTag();
    if (instant) applyNow(); else applyAnimated();
  }

  function applyNow() {
    var q = search.value.trim().toLowerCase();
    var n = 0;
    tiles.forEach(function (el) {
      var title = el.querySelector(".t");
      var sub = el.querySelector(".s");
      var body = el.querySelector(".tile-text");
      var hay = ((title ? title.textContent : "") + " " + (sub ? sub.textContent : "") + " " + (body ? body.textContent : "") + " " + tagsOf(el).join(" ")).toLowerCase();
      var okTag = !activeTag || tagsOf(el).indexOf(activeTag) >= 0;
      var show = okTag && (!q || hay.indexOf(q) >= 0);
      el.hidden = !show;
      if (show) n++;
    });
    count.textContent = n + " of " + tiles.length;
    empty.hidden = n > 0;
    clear.hidden = !search.value;
  }

  // NOTE: filtering steps through a view transition where the browser
  // offers one; elsewhere it is instant, as before.
  function applyAnimated() {
    if (!reduced && document.startViewTransition) {
      document.startViewTransition(function () { applyNow(); });
    } else {
      applyNow();
    }
  }

  // NOTE: typing filters instantly (a transition per keystroke flickers);
  // the animated path is for chip changes, where the eye is already there.
  search.addEventListener("input", applyNow);
  search.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && search.value) { search.value = ""; applyNow(); }
  });
  clear.addEventListener("click", function () {
    search.value = "";
    applyNow();
    search.focus();
  });
  reset.addEventListener("click", function () {
    search.value = "";
    setTag("", true);
    search.focus();
  });

  setTag(readTag(), false, true);
})();
