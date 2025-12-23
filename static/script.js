    // ---------- tiny helpers ----------
    const $ = (q, root=document) => root.querySelector(q);

    function copyToClipboard(text){
      if (navigator.clipboard && window.isSecureContext){
        navigator.clipboard.writeText(text).then(() => toast("Copied ✓"), () => fallbackCopy(text));
      } else {
        fallbackCopy(text);
      }
    }
    function fallbackCopy(text){
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand("copy"); toast("Copied ✓"); }
      catch { toast("Copy failed (sad trombone)"); }
      document.body.removeChild(ta);
    }

    // Toast (lightweight)
    let toastEl;
    function toast(msg){
      if (!toastEl){
        toastEl = document.createElement("div");
        toastEl.style.position = "fixed";
        toastEl.style.left = "50%";
        toastEl.style.bottom = "18px";
        toastEl.style.transform = "translateX(-50%)";
        toastEl.style.padding = "10px 12px";
        toastEl.style.borderRadius = "14px";
        toastEl.style.border = "1px solid rgba(255,255,255,.16)";
        toastEl.style.background = "rgba(0,0,0,.55)";
        toastEl.style.color = "rgba(255,255,255,.88)";
        toastEl.style.fontFamily = "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace";
        toastEl.style.fontSize = "12px";
        toastEl.style.zIndex = "9999";
        toastEl.style.backdropFilter = "blur(10px)";
        toastEl.style.boxShadow = "0 12px 40px rgba(0,0,0,.4)";
        document.body.appendChild(toastEl);
      }
      toastEl.textContent = msg;
      toastEl.style.opacity = "1";
      clearTimeout(toastEl._t);
      toastEl._t = setTimeout(() => toastEl && (toastEl.style.opacity = "0"), 1200);
    }

    // ---------- keyboard shortcuts ----------
    // G -> Projects, C -> Contact, ? -> help
    const helpText = [
      "Shortcuts:",
      "  G  → projects",
      "  C  → contact",
      "  ?  → this help",
      "Tip: press Esc to close help"
    ].join("\\n");

    let helpOpen = false;
    function showHelp(){
      if (helpOpen) return;
      helpOpen = true;
      const modal = document.createElement("div");
      modal.id = "helpModal";
      modal.setAttribute("role","dialog");
      modal.setAttribute("aria-modal","true");
      modal.style.position = "fixed";
      modal.style.inset = "0";
      modal.style.display = "grid";
      modal.style.placeItems = "center";
      modal.style.background = "rgba(0,0,0,.45)";
      modal.style.zIndex = "9998";

      const box = document.createElement("div");
      box.style.width = "min(520px, 92vw)";
      box.style.borderRadius = "18px";
      box.style.border = "1px solid rgba(255,255,255,.18)";
      box.style.background = "rgba(10,12,20,.85)";
      box.style.backdropFilter = "blur(12px)";
      box.style.boxShadow = "0 24px 80px rgba(0,0,0,.55)";
      box.style.padding = "14px";

      const pre = document.createElement("pre");
      pre.textContent = helpText;
      pre.style.margin = "0";
      pre.style.whiteSpace = "pre-wrap";
      pre.style.fontFamily = "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace";
      pre.style.fontSize = "13px";
      pre.style.color = "rgba(255,255,255,.85)";

      const hint = document.createElement("div");
      hint.textContent = "Click outside to close.";
      hint.style.marginTop = "10px";
      hint.style.color = "rgba(255,255,255,.55)";
      hint.style.fontSize = "12px";

      box.appendChild(pre);
      box.appendChild(hint);
      modal.appendChild(box);
      document.body.appendChild(modal);

      const close = () => {
        helpOpen = false;
        modal.remove();
      };
      modal.addEventListener("click", (e) => { if (e.target === modal) close(); });
      window.addEventListener("keydown", function esc(e){
        if (e.key === "Escape"){ close(); window.removeEventListener("keydown", esc); }
      });
    }

    window.addEventListener("keydown", (e) => {
      if (e.ctrlKey || e.metaKey || e.altKey) return;
      const k = e.key.toLowerCase();
      if (k === "g") { $("#projects")?.scrollIntoView({behavior: "smooth"}); }
      if (k === "c") { $("#contact")?.scrollIntoView({behavior: "smooth"}); }
      if (k === "?") { showHelp(); }
    });

    // Copy email button
    const EMAIL = "daniil.kuskalo@example.com"; // <- change me
    $("#copyEmailBtn")?.addEventListener("click", (e) => { e.preventDefault(); copyToClipboard(EMAIL); });

    // Footer year
    $("#year").textContent = String(new Date().getFullYear());

    // ---------- Quirky rotating fun facts (lightweight, no timers if reduced motion) ----------
    const facts = [
      "→ ships before perfection",
      "→ likes boring reliability",
      "→ measures impact, not vibes",
      "→ will profile before guessing",
      "→ writes docs so future-me doesn't rage",
      "→ enjoys removing code more than adding it"
    ];
    const reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!reduceMotion){
      let i = 0;
      setInterval(() => {
        i = (i + 1) % facts.length;
        const el = document.getElementById("funFacts");
        if (!el) return;
        // Replace only the last line for a subtle "live terminal" effect
        const lines = el.innerHTML.split("<br/>");
        if (lines.length >= 4) lines[lines.length - 2] = facts[i];
        el.innerHTML = lines.join("<br/>");
      }, 2600);
    }

    // ---------- Canvas particle network (performance-aware) ----------
    const canvas = document.getElementById("fx");
    const ctx = canvas.getContext("2d", { alpha: true });

    function resize(){
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.floor(innerWidth * dpr);
      canvas.height = Math.floor(innerHeight * dpr);
      canvas.style.width = innerWidth + "px";
      canvas.style.height = innerHeight + "px";
      ctx.setTransform(dpr,0,0,dpr,0,0);
    }
    window.addEventListener("resize", resize, { passive: true });
    resize();

    // Adaptive: fewer particles on small screens, save-data, or reduced motion
    const conn = navigator.connection;
    const saveData = !!(conn && conn.saveData);
    const small = Math.min(innerWidth, innerHeight) < 720;

    let N = 54;
    if (small) N = 40;
    if (saveData) N = 28;
    if (reduceMotion) N = 0;

    const rand = (a,b)=> a + Math.random()*(b-a);
    const pts = Array.from({length: N}, () => ({
      x: rand(0, innerWidth),
      y: rand(0, innerHeight),
      vx: rand(-0.35, 0.35),
      vy: rand(-0.35, 0.35),
      r: rand(1.0, 2.2)
    }));

    let last = performance.now();
    function frame(now){
      const dt = Math.min(32, now - last); // clamp
      last = now;

      ctx.clearRect(0,0,innerWidth,innerHeight);

      // draw
      // (avoid per-pixel work; O(N^2) but N is capped & adaptive)
      for (let i=0;i<pts.length;i++){
        const p = pts[i];

        p.x += p.vx * (dt/16);
        p.y += p.vy * (dt/16);

        if (p.x < -20) p.x = innerWidth + 20;
        if (p.x > innerWidth + 20) p.x = -20;
        if (p.y < -20) p.y = innerHeight + 20;
        if (p.y > innerHeight + 20) p.y = -20;

        // nodes
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI*2);
        ctx.fillStyle = "rgba(255,255,255,.55)";
        ctx.fill();
      }

      const maxDist = small ? 110 : 140;
      for (let i=0;i<pts.length;i++){
        for (let j=i+1;j<pts.length;j++){
          const a = pts[i], b = pts[j];
          const dx = a.x - b.x, dy = a.y - b.y;
          const d = Math.hypot(dx,dy);
          if (d < maxDist){
            const t = 1 - (d / maxDist);
            ctx.strokeStyle = `rgba(34,211,238,${0.10 * t})`;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(a.x,a.y);
            ctx.lineTo(b.x,b.y);
            ctx.stroke();
          }
        }
      }

      requestAnimationFrame(frame);
    }

    if (N > 0) requestAnimationFrame(frame);