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
