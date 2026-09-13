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
      big.src = im.currentSrc.replace("-1200.webp", "-2400.webp");
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
