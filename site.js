/* nim.aesv.io - everything here runs locally. No network, no cookies, no tracking. */
(function () {
  "use strict";

  /* ---------- poke the cloud ---------- */
  var cloud = document.getElementById("cloud");
  var remark = document.getElementById("remark");
  if (cloud && remark) {
    var remarks = [
      "Still a cloud.",
      "The arms are load-bearing.",
      "Mouthless. Not speechless.",
      "That tickles, in the structural sense.",
      "I have no mouth and I must flex."
    ];
    var ri = 0;
    cloud.addEventListener("click", function () {
      remark.textContent = remarks[ri % remarks.length];
      ri++;
      cloud.classList.remove("flex");
      void cloud.offsetWidth;
      cloud.classList.add("flex");
    });
  }

  /* ---------- consult the cloud (oracle) ---------- */
  var askBtn = document.getElementById("ask");
  var oracleOut = document.getElementById("oracle-out");
  if (askBtn && oracleOut) {
    var sayings = [
      "Clutter is just decisions you postponed.",
      "If it needs an app, it is not a tool. It is a landlord.",
      "Do the unglamorous work right. Nobody claps, which is how you know it worked.",
      "Ignore what you cannot control. It is most of it.",
      "A backup you have not tested is a rumor.",
      "Perfection is a rumor too. Ship the good version.",
      "The obstacle is the way, but the shortcut is also sometimes the way. Check first.",
      "You do not rise to the occasion. You fall to the level of your checklists.",
      "Ask what it is for before asking what it costs.",
      "Silence is an answer. So is a shrug. Learn both.",
      "Automate the boring part. Keep the interesting part for yourself.",
      "Nobody remembers the meeting. Everybody remembers the outage."
    ];
    var typing = null;
    function typewrite(text) {
      if (typing) { clearInterval(typing); typing = null; }
      oracleOut.textContent = "";
      var cursor = document.createElement("span");
      cursor.className = "cursor";
      cursor.textContent = "\u2588";
      oracleOut.appendChild(cursor);
      var n = 0;
      typing = setInterval(function () {
        n++;
        oracleOut.textContent = text.slice(0, n);
        oracleOut.appendChild(cursor);
        if (n >= text.length) { clearInterval(typing); typing = null; }
      }, 28);
    }
    askBtn.addEventListener("click", function () {
      typewrite(sayings[Math.floor(Math.random() * sayings.length)]);
    });
  }

  /* ---------- the margin: a pixel canvas ---------- */
  var pad = document.getElementById("pixelpad");
  if (pad) {
    var N = 32;
    var SCALE = 12;
    pad.width = N * SCALE;
    pad.height = N * SCALE;
    var ctx = pad.getContext("2d");
    var KEY = "nim-pixelpad-v1";
    var current = "#ece5d3";
    var painting = false;

    var palette = document.getElementById("palette");
    var colors = ["#ece5d3", "#c8a24a", "#a03a2e", "#4a6fa5", "#101014"];
    colors.forEach(function (c, idx) {
      var b = document.createElement("button");
      b.className = "swatch" + (idx === 0 ? " active" : "");
      b.style.background = c;
      b.setAttribute("aria-label", "color " + c);
      b.addEventListener("click", function () {
        current = c;
        var s = palette.querySelectorAll(".swatch");
        for (var k = 0; k < s.length; k++) s[k].classList.remove("active");
        b.classList.add("active");
      });
      palette.appendChild(b);
    });

    function save() {
      try { localStorage.setItem(KEY, pad.toDataURL()); } catch (e) { /* private mode etc. */ }
    }
    function load() {
      var img = new Image();
      img.onload = function () { ctx.drawImage(img, 0, 0); };
      img.src = localStorage.getItem(KEY) || "";
    }
    function cellAt(e) {
      var r = pad.getBoundingClientRect();
      var x = Math.floor((e.clientX - r.left) / r.width * N);
      var y = Math.floor((e.clientY - r.top) / r.height * N);
      if (x < 0 || y < 0 || x >= N || y >= N) return null;
      return { x: x, y: y };
    }
    function paint(e) {
      var c = cellAt(e);
      if (!c) return;
      ctx.fillStyle = current;
      ctx.fillRect(c.x * SCALE, c.y * SCALE, SCALE, SCALE);
    }
    pad.addEventListener("pointerdown", function (e) {
      painting = true;
      pad.setPointerCapture(e.pointerId);
      paint(e);
    });
    pad.addEventListener("pointermove", function (e) { if (painting) paint(e); });
    pad.addEventListener("pointerup", function () { painting = false; save(); });
    pad.addEventListener("pointercancel", function () { painting = false; save(); });

    var clearBtn = document.getElementById("pad-clear");
    if (clearBtn) {
      clearBtn.addEventListener("click", function () {
        ctx.clearRect(0, 0, pad.width, pad.height);
        try { localStorage.removeItem(KEY); } catch (e) {}
      });
    }
    try { load(); } catch (e) {}
  }
})();
