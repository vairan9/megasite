(() => {
  // Footer year
  const yearEl = document.getElementById("year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  // Mobile nav toggle
  const toggleBtn = document.querySelector(".nav-toggle");
  const mobileNav = document.querySelector("[data-mobile-nav]");
  if (toggleBtn && mobileNav) {
    toggleBtn.addEventListener("click", () => {
      const isOpen = toggleBtn.getAttribute("aria-expanded") === "true";
      toggleBtn.setAttribute("aria-expanded", String(!isOpen));
      mobileNav.hidden = isOpen;

      // Close menu after clicking a link
      if (!isOpen) {
        mobileNav.querySelectorAll("a").forEach(a => {
          a.addEventListener("click", () => {
            toggleBtn.setAttribute("aria-expanded", "false");
            mobileNav.hidden = true;
          }, { once: true });
        });
      }
    });
  }

  // Slider
  const slider = document.querySelector("[data-slider]");
  if (!slider) return;

  const slides = Array.from(slider.querySelectorAll(".slide"));
  const prevBtn = document.querySelector("[data-prev]");
  const nextBtn = document.querySelector("[data-next]");
  const dotBtns = Array.from(document.querySelectorAll("[data-dot]"));

  let index = 0;
  let timer = null;
  const AUTOPLAY_MS = 4500;

  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function setActive(i) {
    index = (i + slides.length) % slides.length;

    slides.forEach((s, idx) => s.classList.toggle("is-active", idx === index));
    dotBtns.forEach((d, idx) => {
      d.classList.toggle("is-active", idx === index);
      d.setAttribute("aria-selected", idx === index ? "true" : "false");
    });
  }

  function next() { setActive(index + 1); }
  function prev() { setActive(index - 1); }

  function stop() {
    if (timer) window.clearInterval(timer);
    timer = null;
  }

  function start() {
    if (prefersReducedMotion) return;
    stop();
    timer = window.setInterval(next, AUTOPLAY_MS);
  }

  // Buttons
  if (nextBtn) nextBtn.addEventListener("click", () => { next(); start(); });
  if (prevBtn) prevBtn.addEventListener("click", () => { prev(); start(); });

  dotBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const i = Number(btn.getAttribute("data-dot"));
      if (Number.isFinite(i)) setActive(i);
      start();
    });
  });

  // Pause on hover/focus (nice feel)
  const sliderCard = document.querySelector(".slider");
  if (sliderCard) {
    sliderCard.addEventListener("mouseenter", stop);
    sliderCard.addEventListener("mouseleave", start);
    sliderCard.addEventListener("focusin", stop);
    sliderCard.addEventListener("focusout", start);
  }

  // Touch swipe (lightweight)
  let startX = 0;
  slider.addEventListener("touchstart", (e) => {
    startX = e.touches?.[0]?.clientX ?? 0;
  }, { passive: true });

  slider.addEventListener("touchend", (e) => {
    const endX = e.changedTouches?.[0]?.clientX ?? 0;
    const dx = endX - startX;
    if (Math.abs(dx) > 40) {
      dx < 0 ? next() : prev();
      start();
    }
  });

  // Init
  setActive(0);
  start();
})();
(() => {
  const headerH = 68; // match --header-h

  function easeInOutCubic(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  function smoothScrollTo(targetY, duration = 700) {
    const startY = window.scrollY;
    const delta = targetY - startY;
    const start = performance.now();

    function tick(now) {
      const p = Math.min(1, (now - start) / duration);
      const eased = easeInOutCubic(p);
      window.scrollTo(0, startY + delta * eased);
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }

  document.addEventListener("click", (e) => {
    const a = e.target.closest('a[href^="#"]');
    if (!a) return;

    const id = a.getAttribute("href");
    if (!id || id === "#") return;

    const el = document.querySelector(id);
    if (!el) return;

    e.preventDefault();

    const y = el.getBoundingClientRect().top + window.scrollY - headerH - 14;
    smoothScrollTo(Math.max(0, y), 750);

    // keeps URL hash (nice for refresh/copy link)
    history.pushState(null, "", id);
  });
})();
document.addEventListener("submit", (e) => {
  const btn = e.target.querySelector('button[type="submit"]');
  if (btn) btn.disabled = true;
});