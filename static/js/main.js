(function () {
  "use strict";

  // ---- Mobile nav toggle ----
  var navToggle = document.getElementById("navToggle");
  var mobileMenu = document.getElementById("mobileMenu");

  if (navToggle && mobileMenu) {
    navToggle.addEventListener("click", function () {
      var isOpen = mobileMenu.classList.toggle("is-open");
      navToggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
    });

    mobileMenu.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", function () {
        mobileMenu.classList.remove("is-open");
        navToggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  // ---- Home page slider ----
  var track = document.getElementById("sliderTrack");
  if (!track) return;

  var slides = Array.prototype.slice.call(track.children);
  var dots = Array.prototype.slice.call(document.querySelectorAll("#sliderDots .slider-dot"));
  var prevBtn = document.getElementById("sliderPrev");
  var nextBtn = document.getElementById("sliderNext");
  var current = 0;
  var isDesktop = window.matchMedia("(min-width: 901px)").matches;

  function goTo(index) {
    if (!isDesktop) return;
    current = (index + slides.length) % slides.length;
    track.style.transform = "translateX(-" + current * 100 / slides.length + "%)";
    dots.forEach(function (dot, i) {
      dot.classList.toggle("is-active", i === current);
    });
  }

  dots.forEach(function (dot, i) {
    dot.addEventListener("click", function () { goTo(i); });
  });

  if (prevBtn) prevBtn.addEventListener("click", function () { goTo(current - 1); });
  if (nextBtn) nextBtn.addEventListener("click", function () { goTo(current + 1); });

  document.addEventListener("keydown", function (e) {
    if (!isDesktop) return;
    if (e.key === "ArrowLeft") goTo(current - 1);
    if (e.key === "ArrowRight") goTo(current + 1);
  });

  // Basic swipe support on desktop-sized touch screens
  var touchStartX = null;
  track.addEventListener("touchstart", function (e) {
    touchStartX = e.touches[0].clientX;
  }, { passive: true });
  track.addEventListener("touchend", function (e) {
    if (touchStartX === null) return;
    var dx = e.changedTouches[0].clientX - touchStartX;
    if (Math.abs(dx) > 50) {
      goTo(dx < 0 ? current + 1 : current - 1);
    }
    touchStartX = null;
  }, { passive: true });

  window.addEventListener("resize", function () {
    var wasDesktop = isDesktop;
    isDesktop = window.matchMedia("(min-width: 901px)").matches;
    if (isDesktop && !wasDesktop) {
      goTo(current);
    } else if (!isDesktop) {
      track.style.transform = "";
    }
  });

  goTo(0);
})();
