// Theme toggle, sticky bar border, scroll reveal, image lightbox.
(function () {
  var root = document.documentElement;
  try {
    var saved = localStorage.getItem("theme");
    if (saved) root.setAttribute("data-theme", saved);
  } catch (e) {}

  var btn = document.querySelector(".theme");
  if (btn) btn.addEventListener("click", function () {
    var dark = root.getAttribute("data-theme")
      ? root.getAttribute("data-theme") === "dark"
      : matchMedia("(prefers-color-scheme: dark)").matches;
    var next = dark ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("theme", next); } catch (e) {}
  });

  // Arriving from another page with a #section link (e.g. Films in the menu):
  // jump there once the page is laid out, instead of relying on smooth scroll.
  if (location.hash.length > 1) {
    var jump = function () {
      var target = document.getElementById(location.hash.slice(1));
      if (!target) return;
      root.style.scrollBehavior = "auto";
      target.scrollIntoView({ block: "start" });
      root.style.scrollBehavior = "";
    };
    if (document.readyState === "complete") jump();
    else addEventListener("load", jump);
  }

  // Background highlight reel: 720p on small screens, none for reduced motion,
  // paused while scrolled out of view, with a pause/play button.
  document.querySelectorAll(".reel-video").forEach(function (video) {
    var hero = video.closest(".reel-hero");
    var btn = hero && hero.querySelector(".reel-toggle");
    var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
    var saveData = navigator.connection && navigator.connection.saveData;
    if (reduce || saveData) { hero.classList.add("no-motion"); return; }  // poster stays as a still image
    video.src = innerWidth <= 900 ? video.dataset.srcSm : video.dataset.srcLg;
    video.preload = "auto";
    var userPaused = false;
    var play = function () { var p = video.play(); if (p && p.catch) p.catch(function () {}); };
    if (btn) btn.addEventListener("click", function () {
      userPaused = !userPaused;
      if (userPaused) video.pause(); else play();
      btn.setAttribute("aria-pressed", String(userPaused));
      btn.setAttribute("aria-label", userPaused ? "Play background video" : "Pause background video");
    });
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting && !userPaused) play(); else video.pause();
        });
      }, { threshold: 0.15 }).observe(hero);
    } else {
      play();
    }
  });

  // Concept-diagram clips (BRIDGE1400): stills for reduced motion, otherwise play only while on screen.
  document.querySelectorAll(".concept-clip video").forEach(function (video) {
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) { video.removeAttribute("autoplay"); video.pause(); return; }
    if (!("IntersectionObserver" in window)) return;
    new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { var p = video.play(); if (p && p.catch) p.catch(function () {}); } else video.pause();
      });
    }).observe(video);
  });

  // Performance dashboard: count-up numbers per tab, grid-price slider, water strategy buttons.
  document.querySelectorAll(".perf").forEach(function (perf) {
    var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
    var fmt = function (v, dec) { return dec ? v.toFixed(dec) : Math.round(v).toLocaleString("en-US"); };
    function run(panel) {
      if (!panel) return;
      panel.classList.remove("perf-animate"); void panel.offsetWidth; panel.classList.add("perf-animate");
      panel.querySelectorAll(".perf-dots i").forEach(function (d, i) { d.style.setProperty("--i", i); });
      var ring = panel.querySelector(".perf-ring");
      if (ring && !reduce) { var p = ring.style.getPropertyValue("--p"); ring.style.setProperty("--p", 0); requestAnimationFrame(function () { requestAnimationFrame(function () { ring.style.setProperty("--p", p); }); }); }
      panel.querySelectorAll("[data-count]").forEach(function (el) {
        var end = parseFloat(el.dataset.count), dec = parseInt(el.dataset.dec || "0", 10);
        if (reduce) { el.textContent = fmt(end, dec); return; }
        var t0 = null;
        (function step(t) {
          t0 = t0 || t; var k = Math.min((t - t0) / 1400, 1), ease = 1 - Math.pow(1 - k, 4);
          el.textContent = fmt(end * ease, dec);
          if (k < 1) requestAnimationFrame(step);
        })(performance.now());
      });
    }
    var current = function () {
      var r = perf.querySelector(".perf-radio:checked");
      return r ? perf.querySelector(".perf-" + r.id.slice(5)) : perf.querySelector(".perf-panel");  // no tabs: the only panel
    };

    var tsim = perf.querySelector(".perf-timber-sim");
    if (tsim) {
      var trange = tsim.querySelector("input[type=range]"), tout = function (n) { return tsim.querySelector('[data-o="' + n + '"]'); };
      var tupdate = function () {
        var area = +trange.value, vol = area * +tsim.dataset.ft3, co2 = vol * +tsim.dataset.rate;
        trange.style.setProperty("--fill", ((area - trange.min) / (trange.max - trange.min) * 100) + "%");
        tout("area").textContent = area.toLocaleString("en-US");
        tout("vol").textContent = (vol / 1e6).toFixed(2) + "M";
        tout("co2").textContent = Math.round(co2).toLocaleString("en-US");
        tout("cars").textContent = Math.round(co2 / +tsim.dataset.car).toLocaleString("en-US");
        tout("meter").style.setProperty("--w", Math.min(co2 / 60000, 1) * 100 + "%");
      };
      trange.addEventListener("input", tupdate); tupdate();
    }
    perf.querySelectorAll(".perf-radio").forEach(function (r) { r.addEventListener("change", function () { run(current()); }); });
    if ("IntersectionObserver" in window) {
      var seen = new IntersectionObserver(function (en) { if (en[0].isIntersecting) { run(current()); seen.disconnect(); } }, { threshold: 0.3 });
      seen.observe(perf);
    }

    var sim = perf.querySelector(".perf-sim:not(.perf-timber-sim)");
    if (sim) {
      var range = sim.querySelector("input[type=range]"), out = function (n) { return sim.querySelector('[data-o="' + n + '"]'); };
      var money = function (v) { return v >= 1e6 ? "$" + (v / 1e6).toFixed(1) + "M" : "$" + Math.round(v / 1e3) + "K"; };
      var update = function () {
        var c = parseFloat(range.value), pv = +sim.dataset.pv, save = pv * c / 100, pay = +sim.dataset.cost / save;
        range.style.setProperty("--fill", ((c - range.min) / (range.max - range.min) * 100) + "%");
        out("price").textContent = c.toFixed(1) + "¢";
        out("save").textContent = money(save);
        out("payback").textContent = pay.toFixed(1);
        out("bill").textContent = money(+sim.dataset.use * c / 100);
        out("meter").style.setProperty("--w", Math.min(pay / 15, 1) * 100 + "%");
      };
      range.addEventListener("input", update); update();
    }

    var water = perf.querySelector(".perf-water-tool");
    if (water) water.querySelectorAll(".perf-chips button").forEach(function (b) {
      b.addEventListener("click", function () {
        water.querySelectorAll(".perf-chips button").forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
        var bar = water.querySelector(".perf-bar");
        bar.style.setProperty("--lo", b.dataset.lo + "%"); bar.style.setProperty("--hi", b.dataset.hi + "%");
        water.querySelector('[data-o="water"]').textContent = b.dataset.text;
      });
    });
  });

  var bar = document.querySelector(".bar");
  addEventListener("scroll", function () {
    bar.classList.toggle("scrolled", scrollY > 8);
  }, { passive: true });

  var items = document.querySelectorAll(".reveal");
  root.classList.add("js");
  var observed = false;
  // Safety net: never leave content hidden if the observer never fires.
  setTimeout(function () {
    if (!observed) items.forEach(function (el) { el.classList.add("in"); });
  }, 2500);
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { observed = true; en.target.classList.add("in"); io.unobserve(en.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px" });
    items.forEach(function (el) { io.observe(el); });
  } else {
    items.forEach(function (el) { el.classList.add("in"); });
  }

  var box = document.querySelector(".lightbox");
  var big = box && box.querySelector("img");
  function close() { box.hidden = true; box.classList.remove("full"); document.body.style.overflow = ""; }
  document.querySelectorAll(".zoom img").forEach(function (im) {
    im.addEventListener("click", function () {
      big.src = (im.currentSrc || im.src).replace("-1200.webp", "-2400.webp");  // currentSrc is empty until a lazy image has loaded
      // see-through drawings (plans, sketches, sections) zoom on the page colour with the same dark-mode filter as on the page
      var drawing = !!im.closest(".plan-sheet, .sketch, .callout-map");
      box.classList.toggle("drawing", drawing);
      big.style.filter = drawing ? getComputedStyle(im).filter : "";
      big.alt = im.alt;
      box.hidden = false;
      document.body.style.overflow = "hidden";
    });
  });
  if (box) {
    big.addEventListener("click", function (ev) { ev.stopPropagation(); box.classList.toggle("full"); });
    box.addEventListener("click", close);
    addEventListener("keydown", function (ev) { if (ev.key === "Escape" && !box.hidden) close(); });
  }
})();
