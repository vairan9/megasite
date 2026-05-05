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
(() => {
  const slider = document.querySelector("[data-slider]");
  if (!slider) return;

  const track = slider.querySelector(".slider-track");
  const slides = Array.from(track.children);

  // Prefer finding controls INSIDE this hero to avoid conflicts
  const root = slider.closest(".hero-slider") || document;
  const prev = root.querySelector("[data-prev]");
  const next = root.querySelector("[data-next]");
  const dots = root.querySelectorAll("[data-dot]");

  let index = 0;
  const total = slides.length;

  // --- autoplay settings
  const AUTO_INTERVAL = 6000;   // time between auto slide changes
  const MANUAL_COOLDOWN = 12000; // pause this long after user clicks

  let autoTimer = null;
  let resumeTimer = null;

  function update() {
    track.style.transform = `translateX(-${index * 100}%)`;

    dots.forEach((d, i) => {
      d.classList.toggle("is-active", i === index);
      d.setAttribute("aria-selected", i === index ? "true" : "false");
    });
  }

  function goTo(i) {
    index = (i + total) % total;
    update();
  }

  function nextSlide() { goTo(index + 1); }
  function prevSlide() { goTo(index - 1); }

  function stopAutoplay() {
    if (autoTimer) clearInterval(autoTimer);
    autoTimer = null;
  }

  function startAutoplay() {
    stopAutoplay();
    autoTimer = setInterval(nextSlide, AUTO_INTERVAL);
  }

  function pauseAfterManual() {
    // stop autoplay now
    stopAutoplay();

    // clear any previous "resume" countdown
    if (resumeTimer) clearTimeout(resumeTimer);

    // resume after cooldown
    resumeTimer = setTimeout(() => {
      startAutoplay();
    }, MANUAL_COOLDOWN);
  }

  // --- events (manual actions trigger cooldown)
  next?.addEventListener("click", () => {
    pauseAfterManual();
    nextSlide();
  });

  prev?.addEventListener("click", () => {
    pauseAfterManual();
    prevSlide();
  });

  dots.forEach(dot => {
    dot.addEventListener("click", () => {
      pauseAfterManual();
      goTo(Number(dot.dataset.dot));
    });
  });

  // Optional: pause while hovering (doesn't affect the manual cooldown timer)
  slider.addEventListener("mouseenter", () => stopAutoplay());
  slider.addEventListener("mouseleave", () => {
    // only restart if we are NOT in manual cooldown
    if (!resumeTimer) startAutoplay();
  });

  update();
  startAutoplay();
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
})();
