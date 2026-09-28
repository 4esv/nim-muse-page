/* nim.js: site behavior. Top bar state, the wall, the ledger filter, and the
   collection pages (pile or browser, constellation, ledger).
   Plain script, no dependencies, ES5 style. The hero dust stays inline in
   index.html so it can be read in one place. */
(function () {
  "use strict";

  var doc = document;
  // NOTE: one motion flag for everything JS animates: pile swaps, the
  // constellation draw. CSS handles its own transitions under the same query.
  var still = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);

  /* ---------- small helpers ---------- */
  function $(id) { return doc.getElementById(id); }
  function arr(list) { return Array.prototype.slice.call(list); }
  function el(tag, cls, text) {
    var n = doc.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function txt(root, sel) {
    var n = root.querySelector(sel);
    return n ? n.textContent.replace(/\s+/g, " ").trim() : "";
  }
  function tagsOf(n) {
    return (n.getAttribute("data-tags") || "").split(/\s+/).filter(function (t) { return t; });
  }
  function hasTag(n, t) { return tagsOf(n).indexOf(t) >= 0; }
  // NOTE: newest first by data-date. Equal dates keep document order.
  function newest(list) {
    return list
      .map(function (n, i) { return { n: n, d: n.getAttribute("data-date") || "", i: i }; })
      .sort(function (a, b) { return a.d < b.d ? 1 : (a.d > b.d ? -1 : a.i - b.i); })
      .map(function (o) { return o.n; });
  }
  // NOTE: tile titles are caps by contract. Serif headings read better in
  // sentence case, so an all-caps title is lowered with its first letter kept.
  function sentence(s) {
    if (!s || s !== s.toUpperCase()) return s;
    s = s.toLowerCase();
    return s.charAt(0).toUpperCase() + s.slice(1);
  }
  function nameOf(href) {
    var m = /[?&]e=([a-z0-9-]+)/.exec(href) || /([a-z0-9-]+)\.html(?:[?#]|$)/.exec(href);
    return m ? m[1] : "";
  }
  function firstSentence(s) {
    var m = /^[\s\S]*?[.!?](?=\s|$)/.exec(s);
    return m ? m[0] : s;
  }
  function chipLink(text, href) {
    var a = el("a", "chip px", text);
    a.href = href;
    return a;
  }
  function chipButton(text, label) {
    var b = el("button", "chip px", text);
    b.type = "button";
    if (label) b.setAttribute("aria-label", label);
    return b;
  }
  // NOTE: a 160ms stepped slide on the swapped card. Nothing under reduced motion.
  function bump(n, dir) {
    if (still || !n) return;
    n.classList.remove("swap-l", "swap-r");
    void n.offsetWidth;
    n.classList.add(dir < 0 ? "swap-l" : "swap-r");
  }

  /* ---------- items: one shape for tiles and collection rows ---------- */
  function fromTile(n) {
    var img = n.querySelector("img");
    return {
      href: n.getAttribute("href") || "",
      date: n.getAttribute("data-date") || "",
      min: n.getAttribute("data-min") || "",
      label: txt(n, ".tile-meta .t"),
      title: sentence(txt(n, ".tile-meta .t")),
      deck: txt(n, ".tile-meta .s") || txt(n, ".tile-text p"),
      text: txt(n, ".tile-text"),
      img: img ? { src: img.getAttribute("src"), alt: img.getAttribute("alt") || "" } : null
    };
  }
  function fromItem(n) {
    var thumb = n.getAttribute("data-thumb");
    var title = txt(n, ".title");
    return {
      href: n.getAttribute("href") || "",
      date: n.getAttribute("data-date") || "",
      min: n.getAttribute("data-min") || "",
      label: title.toUpperCase(),
      title: sentence(title),
      deck: txt(n, ".deck"),
      text: txt(n, ".deck"),
      img: thumb ? { src: thumb, alt: n.getAttribute("data-alt") || "" } : null
    };
  }

  /* ---------- cycling: prev, counter, next, arrow keys inside the cell ---------- */
  function cycler(cell, items, render, noun) {
    var i = 0;
    var n = items.length;
    var prev = chipButton("prev", "previous " + noun);
    var next = chipButton("next", "next " + noun);
    var count = el("span", "counter", "1 / " + n);
    count.setAttribute("aria-live", "polite");
    if (n < 2) { prev.disabled = true; next.disabled = true; }
    function go(d) {
      if (n < 2) return;
      i = (i + d + n) % n;
      count.textContent = (i + 1) + " / " + n;
      render(items[i], d);
    }
    prev.addEventListener("click", function () { go(-1); });
    next.addEventListener("click", function () { go(1); });
    cell.addEventListener("keydown", function (e) {
      if (e.altKey || e.ctrlKey || e.metaKey) return;
      if (e.key === "ArrowLeft") { e.preventDefault(); go(-1); }
      else if (e.key === "ArrowRight") { e.preventDefault(); go(1); }
    });
    render(items[0], 0);
    var bar = el("div", "controls");
    bar.appendChild(prev);
    bar.appendChild(count);
    bar.appendChild(next);
    return bar;
  }

  function cellHead(text) {
    var h = el("h2", "cell-h", text);
    return h;
  }

  /* ---------- the pile: essays as stacked chalk cards ---------- */
  function buildPile(items, o) {
    var cell = el("div", "cell pile-cell");
    if (o.head) cell.appendChild(cellHead(o.head));
    var pile = el("div", "pile");
    for (var k = Math.min(items.length - 1, 2); k >= 1; k--) {
      var back = el("div", "card px back back-" + k);
      back.setAttribute("aria-hidden", "true");
      pile.appendChild(back);
    }
    var card = el("a", "card px top");
    var magnet = el("span", "magnet");
    magnet.setAttribute("aria-hidden", "true");
    var t = el("span", "t", "ESSAY");
    var title = el("span", "title");
    var deck = el("span", "deck");
    var d = el("span", "d");
    card.appendChild(t);
    card.appendChild(title);
    card.appendChild(deck);
    card.appendChild(d);
    pile.appendChild(card);
    pile.appendChild(magnet);
    cell.appendChild(pile);
    var controls = cycler(cell, items, function (it, dir) {
      card.href = it.href;
      title.textContent = it.title;
      deck.textContent = it.deck;
      deck.hidden = !it.deck;
      d.textContent = it.date + (it.min ? " · " + it.min + " min" : "");
      if (dir) bump(card, dir);
    }, "essay");
    if (o.all) controls.appendChild(chipLink(o.all[0], o.all[1]));
    cell.appendChild(controls);
    return cell;
  }

  /* ---------- the browser: experiments in a pixel window ---------- */
  function buildBrowser(items, o) {
    var cell = el("div", "cell browser-cell");
    if (o.head) cell.appendChild(cellHead(o.head));
    var win = el("div", "browser px");
    var bar = el("div", "titlebar");
    bar.setAttribute("aria-hidden", "true");
    bar.appendChild(el("span", "dot"));
    bar.appendChild(el("span", "dot"));
    bar.appendChild(el("span", "dot"));
    var url = el("span", "url");
    bar.appendChild(url);
    win.appendChild(bar);
    // NOTE: the picture repeats the open chip, so it stays out of tab order
    // and out of the accessibility tree; the chip is the real control.
    var view = el("a", "viewport");
    view.tabIndex = -1;
    view.setAttribute("aria-hidden", "true");
    win.appendChild(view);
    cell.appendChild(win);
    var cap = el("div", "caption");
    var t = el("span", "t");
    var s = el("span", "s");
    cap.appendChild(t);
    cap.appendChild(s);
    cell.appendChild(cap);
    var open = chipLink("open", "#");
    var controls = cycler(cell, items, function (it, dir) {
      var name = nameOf(it.href);
      url.textContent = "nim.aesv.io/experiments/" + (name || "index") + ".html";
      view.href = it.href;
      view.textContent = "";
      if (it.img) {
        var img = el("img");
        img.src = it.img.src;
        img.alt = it.img.alt;
        img.width = 320;
        img.height = 240;
        view.appendChild(img);
      } else {
        var page = el("span", "chalk-page");
        page.appendChild(el("span", "", it.text || it.deck || it.title));
        view.appendChild(page);
      }
      t.textContent = it.label;
      s.textContent = it.img ? it.deck : "";
      s.hidden = !s.textContent;
      open.href = it.href;
      open.setAttribute("aria-label", "open " + it.title.toLowerCase());
      if (dir) bump(view, dir);
    }, "experiment");
    controls.appendChild(open);
    if (o.all) controls.appendChild(chipLink(o.all[0], o.all[1]));
    cell.appendChild(controls);
    return cell;
  }

  /* ---------- pinned: this week's print ---------- */
  function buildPinned(it) {
    var cell = el("div", "cell pinned");
    cell.appendChild(cellHead("this week"));
    var print = el("a", "print");
    print.href = it.href;
    if (it.img) {
      var img = el("img");
      img.src = it.img.src;
      img.alt = it.img.alt;
      img.width = 320;
      img.height = 240;
      print.appendChild(img);
    } else {
      print.appendChild(el("span", "chalk-page", it.deck || it.label));
    }
    var pin = el("span", "pin");
    pin.setAttribute("aria-hidden", "true");
    var board = el("div", "print-wrap");
    board.appendChild(print);
    board.appendChild(pin);
    cell.appendChild(board);
    var cap = el("div", "caption");
    cap.appendChild(el("span", "t", it.label));
    if (it.deck) cap.appendChild(el("span", "s", it.deck));
    cap.appendChild(el("span", "d", it.date));
    cell.appendChild(cap);
    var controls = el("div", "controls");
    controls.appendChild(chipLink("all weeks", "index.html?tag=weekly#ledger"));
    cell.appendChild(controls);
    return cell;
  }

  /* ---------- scribbles: notes, chalked on the board ---------- */
  function buildScribbles(items) {
    var cell = el("div", "cell scribbles");
    cell.appendChild(cellHead("notes"));
    var ul = el("ul");
    items.forEach(function (it) {
      var li = el("li");
      li.appendChild(el("span", "t", it.label));
      li.appendChild(doc.createTextNode(" " + firstSentence(it.text || it.deck)));
      ul.appendChild(li);
    });
    cell.appendChild(ul);
    return cell;
  }

  /* ---------- the constellation: collection items as chalk stars ---------- */
  // NOTE: FNV-1a seeds each star from its href, mulberry32 spreads it, so the
  // sky is the same on every load and every screen.
  function fnv(s) {
    var h = 0x811c9dc5;
    for (var i = 0; i < s.length; i++) {
      h ^= s.charCodeAt(i);
      h = Math.imul(h, 0x01000193) >>> 0;
    }
    return h >>> 0;
  }
  function prng(seed) {
    var a = seed >>> 0;
    return function () {
      a = (a + 0x6d2b79f5) >>> 0;
      var t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function place(items) {
    var M = 0.12, ASPECT = 1.6, MIN = 0.16;
    var pts = items.map(function (it) {
      var r = prng(fnv(it.href));
      return { x: M + r() * (1 - 2 * M), y: M + r() * (1 - 2 * M) };
    });
    for (var pass = 0; pass < 3; pass++) {
      for (var i = 0; i < pts.length; i++) {
        for (var j = i + 1; j < pts.length; j++) {
          var dx = (pts[j].x - pts[i].x) * ASPECT;
          var dy = pts[j].y - pts[i].y;
          var dist = Math.sqrt(dx * dx + dy * dy) || 0.001;
          if (dist >= MIN) continue;
          var push = (MIN - dist) / 2;
          var ux = dx / dist, uy = dy / dist;
          pts[i].x -= ux * push / ASPECT; pts[i].y -= uy * push;
          pts[j].x += ux * push / ASPECT; pts[j].y += uy * push;
        }
      }
      pts.forEach(function (p) {
        p.x = Math.min(1 - M, Math.max(M, p.x));
        p.y = Math.min(1 - M, Math.max(M, p.y));
      });
    }
    return pts;
  }

  function buildSky(items, noun) {
    var BONE = "#ece5d3", CHALK = "rgba(236,229,211,0.72)", CHALK_DIM = "rgba(236,229,211,0.45)";
    var frame = el("div", "sky-frame");
    frame.tabIndex = 0;
    frame.setAttribute("role", "group");
    frame.setAttribute("aria-label", "constellation, drag or use arrow keys to pan");
    var pan = el("div", "sky-pan");
    var canvas = el("canvas", "sky");
    canvas.setAttribute("role", "img");
    canvas.setAttribute("aria-label", "a constellation of " + items.length + " " + noun +
      " drawn in chalk; the same links are listed after it");
    var ul = el("ul", "stars");
    var pts = place(items);
    items.forEach(function (it, i) {
      var p = pts[i];
      var li = el("li");
      li.style.left = (p.x * 100) + "%";
      li.style.top = (p.y * 100) + "%";
      var a = el("a", "star");
      a.href = it.href;
      a.setAttribute("aria-label", it.title);
      var tip = el("span", "tip px");
      tip.appendChild(el("span", "title", it.title));
      if (it.deck) tip.appendChild(el("span", "deck", it.deck));
      tip.appendChild(el("span", "d", it.date));
      if (p.x > 0.62) a.classList.add("tip-l");
      else if (p.x < 0.38) a.classList.add("tip-r");
      if (p.y < 0.4) a.classList.add("tip-b");
      a.appendChild(tip);
      li.appendChild(a);
      ul.appendChild(li);
    });
    pan.appendChild(canvas);
    pan.appendChild(ul);
    frame.appendChild(pan);

    // NOTE: the line runs oldest to newest; items arrive newest first.
    var order = pts.map(function (p, i) { return i; }).reverse();
    var W = 0, H = 0, ctx = null, path = [], bg = [];

    function line(x0, y0, x1, y1, out) {
      var dx = Math.abs(x1 - x0), sx = x0 < x1 ? 1 : -1;
      var dy = -Math.abs(y1 - y0), sy = y0 < y1 ? 1 : -1;
      var err = dx + dy;
      for (;;) {
        out.push(x0, y0);
        if (x0 === x1 && y0 === y1) break;
        var e2 = 2 * err;
        if (e2 >= dy) { err += dy; x0 += sx; }
        if (e2 <= dx) { err += dx; y0 += sy; }
      }
    }
    function at(i) { return [Math.round(pts[i].x * W), Math.round(pts[i].y * H)]; }
    function measure() {
      var r = frame.getBoundingClientRect();
      W = Math.max(1, Math.floor(r.width));
      H = Math.max(1, Math.floor(r.height));
      var s = Math.max(2, Math.round(window.devicePixelRatio || 1));
      canvas.width = W * s;
      canvas.height = H * s;
      canvas.style.width = W + "px";
      canvas.style.height = H + "px";
      ctx = canvas.getContext("2d");
      ctx.setTransform(s, 0, 0, s, 0, 0);
      ctx.imageSmoothingEnabled = false;
      path = [];
      for (var k = 1; k < order.length; k++) {
        var a = at(order[k - 1]), b = at(order[k]);
        line(a[0], a[1], b[0], b[1], path);
      }
      bg = [];
      var r2 = prng(fnv("nim sky " + noun));
      var n = Math.min(240, Math.floor(W * H / 5000));
      for (var j = 0; j < n; j++) bg.push(Math.floor(r2() * W), Math.floor(r2() * H));
    }
    function draw(progress) {
      if (!ctx) return;
      ctx.clearRect(0, 0, W, H);
      ctx.fillStyle = "rgba(236,229,211,0.25)";
      for (var j = 0; j < bg.length; j += 2) ctx.fillRect(bg[j], bg[j + 1], 2, 2);
      ctx.fillStyle = CHALK;
      var upto = Math.floor(path.length / 2 * progress) * 2;
      for (var k = 0; k < upto; k += 2) ctx.fillRect(path[k], path[k + 1], 1, 1);
      for (var i = pts.length - 1; i >= 0; i--) {
        var size = i === 0 ? 4 : (i <= 2 ? 3 : 2);
        ctx.fillStyle = i === 0 ? BONE : (i <= 2 ? CHALK : CHALK_DIM);
        var c = at(i);
        ctx.fillRect(c[0] - Math.floor(size / 2), c[1] - Math.floor(size / 2), size, size);
      }
    }
    function start() {
      measure();
      if (still) { draw(1); return; }
      var t0 = null;
      function step(t) {
        if (t0 === null) t0 = t;
        var p = Math.min(1, (t - t0) / 900);
        draw(p);
        if (p < 1) window.requestAnimationFrame(step);
      }
      window.requestAnimationFrame(step);
    }
    var timer = 0;
    window.addEventListener("resize", function () {
      clearTimeout(timer);
      timer = setTimeout(function () {
        if (!frame.offsetParent) return;
        measure(); draw(1); setPan(px, py);
      }, 120);
    });

    // NOTE: pan by drag or arrows, clamped to 30% of the frame either way.
    var px = 0, py = 0;
    function setPan(x, y) {
      var mx = W * 0.3, my = H * 0.3;
      px = Math.round(Math.max(-mx, Math.min(mx, x)));
      py = Math.round(Math.max(-my, Math.min(my, y)));
      pan.style.transform = "translate(" + px + "px," + py + "px)";
    }
    var drag = null, moved = false;
    frame.addEventListener("pointerdown", function (e) {
      if (e.button !== 0) return;
      drag = { x: e.clientX, y: e.clientY, px: px, py: py, id: e.pointerId };
      moved = false;
    });
    frame.addEventListener("pointermove", function (e) {
      if (!drag || e.pointerId !== drag.id) return;
      var dx = e.clientX - drag.x, dy = e.clientY - drag.y;
      if (!moved && Math.abs(dx) + Math.abs(dy) < 4) return;
      if (!moved) {
        moved = true;
        frame.classList.add("is-dragging");
        try { frame.setPointerCapture(e.pointerId); } catch (err) { /* NOTE: pointer already gone */ }
      }
      setPan(drag.px + dx, drag.py + dy);
    });
    function end() { drag = null; frame.classList.remove("is-dragging"); }
    frame.addEventListener("pointerup", end);
    frame.addEventListener("pointercancel", end);
    // NOTE: a drag that ends on a star must not follow the link.
    frame.addEventListener("click", function (e) {
      if (moved) { e.preventDefault(); e.stopPropagation(); moved = false; }
    }, true);
    frame.addEventListener("keydown", function (e) {
      var step = e.shiftKey ? 96 : 24;
      var k = { ArrowLeft: [step, 0], ArrowRight: [-step, 0], ArrowUp: [0, step], ArrowDown: [0, -step] }[e.key];
      if (!k) return;
      e.preventDefault();
      setPan(px + k[0], py + k[1]);
    });

    return { el: frame, start: start };
  }

  /* ---------- filter: chips, search, count, empty state ----------
     Shared by the home ledger and the collection ledgers.
     o: { items, chips, count, empty, reset, search, clear, hay, exclude, hash } */
  function filter(o) {
    var items = o.items;
    var activeTag = "";
    var tags = {};
    var total = {};
    items.forEach(function (n) {
      total[key(n)] = 1;
    });
    var seen = {};
    items.forEach(function (n) {
      if (seen[key(n)]) return;
      seen[key(n)] = 1;
      tagsOf(n).forEach(function (t) {
        if (t !== o.exclude) tags[t] = (tags[t] || 0) + 1;
      });
    });
    var totalN = Object.keys(total).length;

    // NOTE: the featured essay repeats the first row; count each link once.
    function key(n) { return n.getAttribute("href") || String(items.indexOf(n)); }
    function hide(n, h) {
      var box = n.parentNode && n.parentNode.tagName === "LI" ? n.parentNode : n;
      box.hidden = h;
    }

    function chip(label, tag, count) {
      var b = chipButton(label);
      b.setAttribute("data-tag", tag);
      b.setAttribute("aria-pressed", "false");
      var c = el("span", "n", String(count));
      b.appendChild(c);
      b.addEventListener("click", function () {
        setTag(activeTag === tag ? "" : tag, true);
      });
      o.chips.appendChild(b);
    }
    chip("all", "", totalN);
    Object.keys(tags).sort().forEach(function (t) { chip(t, t, tags[t]); });

    // NOTE: only tags that exist on an item are accepted from the URL.
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
      var hash = window.location.hash || (activeTag && o.hash ? o.hash : "");
      window.history.replaceState(null, "", window.location.pathname + (keep.length ? "?" + keep.join("&") : "") + hash);
    }
    function setTag(t, write) {
      activeTag = t;
      arr(o.chips.children).forEach(function (c) {
        c.setAttribute("aria-pressed", c.getAttribute("data-tag") === activeTag ? "true" : "false");
      });
      if (write) writeTag();
      apply();
    }
    function apply() {
      var q = o.search ? o.search.value.trim().toLowerCase() : "";
      var shown = {};
      items.forEach(function (n) {
        var okTag = !activeTag || hasTag(n, activeTag);
        var show = okTag && (!q || o.hay(n).toLowerCase().indexOf(q) >= 0);
        hide(n, !show);
        if (show) shown[key(n)] = 1;
      });
      var k = Object.keys(shown).length;
      o.count.textContent = k + " of " + totalN;
      o.empty.hidden = k > 0;
      if (o.clear) o.clear.hidden = !(o.search && o.search.value);
    }

    if (o.search) {
      o.search.addEventListener("input", apply);
      o.search.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && o.search.value) { o.search.value = ""; apply(); }
      });
    }
    if (o.clear) {
      o.clear.addEventListener("click", function () {
        o.search.value = "";
        apply();
        o.search.focus();
      });
    }
    if (o.reset) {
      o.reset.addEventListener("click", function () {
        if (o.search) o.search.value = "";
        setTag("", true);
        (o.search || o.chips.firstChild).focus();
      });
    }
    setTag(readTag(), false);
  }

  /* ---------- top bar: clear over the hero, solid once scrolled ---------- */
  var bar = $("bar");
  if (bar && !doc.body.classList.contains("collection")) {
    var queued = false;
    var paint = function () {
      queued = false;
      var y = window.pageYOffset || doc.documentElement.scrollTop || 0;
      bar.classList.toggle("is-clear", y < 24);
    };
    window.addEventListener("scroll", function () {
      if (!queued) { queued = true; window.requestAnimationFrame(paint); }
    }, { passive: true });
    paint();
  }

  /* ---------- home: sort the ledger, build the wall, wire the filter ---------- */
  var grid = $("grid");
  if (grid) {
    var tiles = newest(arr(grid.querySelectorAll(".tile")));
    tiles.forEach(function (n) { grid.appendChild(n); });

    var wall = $("wall");
    if (wall) {
      var pick = function (t) { return tiles.filter(function (n) { return hasTag(n, t); }).map(fromTile); };
      // NOTE: an essay is a page in essays/. Experiments may carry the tag too.
      var essays = tiles.filter(function (n) { return /^essays\//.test(n.getAttribute("href") || ""); }).map(fromTile);
      var exps = pick("experiment").filter(function (it) { return !/^essays\//.test(it.href || ""); });
      var weeks = pick("weekly");
      var notes = pick("note");
      if (essays.length) wall.appendChild(buildPile(essays, { head: "essays", all: ["all essays", "essays.html"] }));
      if (exps.length) wall.appendChild(buildBrowser(exps, { head: "experiments", all: ["all experiments", "experiments.html"] }));
      if (weeks.length) wall.appendChild(buildPinned(weeks[0]));
      if (notes.length) wall.appendChild(buildScribbles(notes));
      wall.hidden = !wall.children.length;
    }

    filter({
      items: tiles,
      chips: $("chips"),
      count: $("count"),
      empty: $("empty"),
      reset: $("reset"),
      search: $("q"),
      clear: $("q-clear"),
      hash: "#ledger",
      hay: function (n) { return txt(n, ".t") + " " + txt(n, ".s") + " " + tagsOf(n).join(" "); }
    });
  }

  /* ---------- collection pages: essays.html, experiments.html ---------- */
  if (doc.body.classList.contains("collection")) {
    var kind = doc.body.getAttribute("data-kind") || "essays";
    var kindTag = kind === "experiments" ? "experiment" : "essay";
    var first = kind === "experiments" ? "browser" : "pile";
    var rows = arr(doc.querySelectorAll("[data-item]"));
    var ledger = $("ledger");
    var stage = $("stage");
    var views = $("views");

    filter({
      items: rows,
      chips: $("chips"),
      count: $("count"),
      empty: $("empty"),
      reset: $("reset"),
      search: null,
      clear: null,
      exclude: kindTag,
      hash: "",
      hay: function (n) { return n.textContent; }
    });

    var seenHref = {};
    var models = newest(rows).filter(function (n) {
      var h = n.getAttribute("href");
      if (seenHref[h]) return false;
      seenHref[h] = 1;
      return true;
    }).map(fromItem);

    if (views && stage && ledger && models.length) {
      var built = {};
      var current = "";
      var show = function (v, write) {
        if (v !== "constellation" && v !== "ledger") v = first;
        current = v;
        arr(views.querySelectorAll("[data-view]")).forEach(function (b) {
          b.setAttribute("aria-pressed", b.getAttribute("data-view") === v ? "true" : "false");
        });
        if (write && window.history && window.history.replaceState) {
          var h = v === first ? "" : "#" + v;
          window.history.replaceState(null, "", window.location.pathname + window.location.search + h);
        }
        ledger.hidden = v !== "ledger";
        stage.hidden = v === "ledger";
        if (v === "ledger") return;
        stage.setAttribute("aria-label", kind + ", " + v);
        arr(stage.children).forEach(function (c) { c.hidden = c.getAttribute("data-for") !== v; });
        if (!built[v]) {
          var made;
          if (v === "constellation") {
            var sky = buildSky(models, kind);
            made = sky.el;
            made.setAttribute("data-for", v);
            stage.appendChild(made);
            sky.start();
          } else {
            made = v === "browser" ? buildBrowser(models, {}) : buildPile(models, {});
            made.setAttribute("data-for", v);
            made.classList.add("solo");
            stage.appendChild(made);
          }
          built[v] = made;
        }
      };
      views.hidden = false;
      arr(views.querySelectorAll("[data-view]")).forEach(function (b) {
        b.addEventListener("click", function () { show(b.getAttribute("data-view"), true); });
      });
      var fromHash = function () { return window.location.hash.replace(/^#/, ""); };
      window.addEventListener("hashchange", function () {
        var v = fromHash();
        if (v !== current) show(v, false);
      });
      show(fromHash(), false);
    }
  }
})();
