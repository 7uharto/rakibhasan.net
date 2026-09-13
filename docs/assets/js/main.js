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
