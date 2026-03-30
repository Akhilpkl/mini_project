// ─── PAGE TRANSITION SYSTEM ────────────────────────────────
// Spinner-ring overlay: dark backdrop + thin gradient circle spinner
// (matches the 2nd animation in the reference grid).

(function () {
  'use strict';

  // ── Grab elements from native DOM ────────────────────────
  const overlay = document.getElementById('page-overlay');
  const spinner = document.getElementById('page-spinner');
  const bar = document.getElementById('nav-bar');

  // If elements aren't present in HTML, bail out to avoid errors
  if (!overlay || !spinner || !bar) return;

  function showSpinner() {
    spinner.style.opacity = '1';
  }
  function hideSpinner() {
    spinner.style.opacity = '0';
  }

  function startBar() {
    bar.style.opacity = '1';
    bar.style.width = '70%';
  }
  function finishBar() {
    bar.style.width = '100%';
    setTimeout(() => { bar.style.opacity = '0'; bar.style.width = '0%'; }, 350);
  }

  // ── Fade overlay + spinner out after page paints ─────────
  window.addEventListener('pageshow', function () {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        overlay.style.opacity = '0';
        hideSpinner();
        finishBar();
      });
    });
  });

  // ── Intercept link clicks ────────────────────────────────
  document.addEventListener('click', function (e) {
    const link = e.target.closest('a[href]');
    if (!link) return;

    const href = link.getAttribute('href');

    // Skip: anchors, external, new-tab, download, special-protocols
    if (
      !href ||
      href.startsWith('#') ||
      href.startsWith('mailto:') ||
      href.startsWith('tel:') ||
      href.startsWith('javascript:') ||
      link.target === '_blank' ||
      link.hasAttribute('download') ||
      link.hostname !== window.location.hostname
    ) return;

    e.preventDefault();

    startBar();
    showSpinner();

    // Fade overlay in, then navigate
    overlay.style.transition = 'opacity 0.2s ease';
    overlay.style.opacity = '1';

    setTimeout(() => {
      window.location.href = href;
    }, 450);
  });

  // ── Form submit: show bar ────────────────────────────────
  document.addEventListener('submit', function (e) {
    const form = e.target;
    if (form.method && form.method.toLowerCase() !== 'dialog') {
      startBar();
      showSpinner();
      overlay.style.transition = 'opacity 0.2s ease';
      overlay.style.opacity = '1';
    }
  });

})();

// ─── Sidebar card hover animations (existing) ────────────
document.addEventListener('DOMContentLoaded', function () {
  // Stagger-animate cards on initial page load
  const cards = document.querySelectorAll('.dash-card, .glass-card, .stat-card, .feature-card, .stagger-element');
  cards.forEach((card, i) => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(18px)';
    card.style.transition = 'none';
    setTimeout(() => {
      card.style.transition = 'opacity 0.45s ease, transform 0.45s ease';
      card.style.opacity = '1';
      card.style.transform = 'translateY(0)';
    }, 60 + i * 55);
  });

  // Ripple effect on primary buttons
  document.querySelectorAll('.btn-primary-custom').forEach(btn => {
    btn.addEventListener('click', function (e) {
      const ripple = document.createElement('span');
      const rect = btn.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      ripple.style.cssText = `
        position: absolute;
        border-radius: 50%;
        width: ${size}px; height: ${size}px;
        left: ${e.clientX - rect.left - size / 2}px;
        top: ${e.clientY - rect.top - size / 2}px;
        background: rgba(255,255,255,0.25);
        transform: scale(0);
        animation: ripple-out 0.5s ease forwards;
        pointer-events: none;
      `;
      btn.style.overflow = 'hidden';
      btn.style.position = 'relative';
      btn.appendChild(ripple);
      setTimeout(() => ripple.remove(), 500);
    });
  });
});

// ─── SLIDING NAV PILL ───────────────────────────────────────
// Creates a magic pill that flows between sidebar nav items,
// even across full page loads (via sessionStorage for position memory).
(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    const menu = document.getElementById('menu');
    if (!menu) return;

    const links = Array.from(menu.querySelectorAll('.nav-link'));
    if (!links.length) return;

    // Find active link index
    const activeIdx = links.findIndex(l => l.classList.contains('active'));
    if (activeIdx === -1) return;

    // ── Create the pill element ──────────────────────────────
    const pill = document.createElement('div');
    pill.id = 'nav-pill';
    pill.style.cssText = `
      position: absolute;
      left: 12px; right: 12px;
      border-radius: 8px;
      background: linear-gradient(135deg, rgba(124,58,237,.22), rgba(79,70,229,.16));
      border: 1px solid rgba(124,58,237,.32);
      pointer-events: none;
      z-index: 0;
      transition: top 0.45s cubic-bezier(0.16, 1, 0.3, 1),
                  height 0.45s cubic-bezier(0.16, 1, 0.3, 1),
                  opacity 0.3s ease;
    `;

    // Position needs the menu to be relative
    menu.style.position = 'relative';
    menu.insertBefore(pill, menu.firstChild);

    // Make links stack above the pill
    links.forEach(l => { l.style.position = 'relative'; l.style.zIndex = '1'; });

    function getPillGeometry(link) {
      const menuRect = menu.getBoundingClientRect();
      const linkRect = link.getBoundingClientRect();
      return {
        top: linkRect.top - menuRect.top,
        height: linkRect.height,
      };
    }

    function setPill(link, instant) {
      const { top, height } = getPillGeometry(link);
      if (instant) {
        pill.style.transition = 'none';
      } else {
        pill.style.transition = `
          top 0.45s cubic-bezier(0.16, 1, 0.3, 1),
          height 0.45s cubic-bezier(0.16, 1, 0.3, 1),
          opacity 0.3s ease
        `;
      }
      pill.style.top    = top + 'px';
      pill.style.height = height + 'px';
      pill.style.opacity = '1';
    }

    // ── Animate from previous tab if stored ─────────────────
    const prevIdx = parseInt(sessionStorage.getItem('navPillIdx') ?? '-1');

    if (prevIdx !== -1 && prevIdx !== activeIdx && links[prevIdx]) {
      // Instantly place pill at old position
      setPill(links[prevIdx], true);

      // Force reflow so browser registers the starting position
      void pill.offsetHeight;

      // Then animate to new position
      requestAnimationFrame(() => {
        setPill(links[activeIdx], false);
      });
    } else {
      // No history — just softly fade in at current position
      pill.style.opacity = '0';
      setPill(links[activeIdx], true);
      void pill.offsetHeight;
      pill.style.transition = 'opacity 0.35s ease';
      requestAnimationFrame(() => { pill.style.opacity = '1'; });
    }

    // ── Store clicked index before navigation ────────────────
    links.forEach((link, idx) => {
      link.addEventListener('click', () => {
        sessionStorage.setItem('navPillIdx', String(idx));
      });
    });

    // ── Handle window resize ─────────────────────────────────
    window.addEventListener('resize', () => {
      setPill(links[activeIdx], true);
    });
  });
})();

// ─── TELEGRAM-STYLE DARK / LIGHT MODE TOGGLE ───────────────
// On click: captures button position → switches data-theme on <html>
// → animates a clip-path circle that grows from the button outward,
// revealing the new theme underneath — identical to Telegram's animation.
(function () {
  'use strict';

  // Inject the clip-path animation stylesheet for View Transitions
  const vt = document.createElement('style');
  vt.textContent = `
    /* When theme transition runs via View Transitions API */
    ::view-transition-old(root),
    ::view-transition-new(root) {
      animation: none;
      mix-blend-mode: normal;
    }
    /* New theme expands as a circle from toggle button */
    ::view-transition-new(root) {
      z-index: 9999;
      clip-path: var(--theme-ripple-clip, circle(0px at 50% 50%));
      animation: _theme_ripple 0.7s ease-in-out forwards;
      will-change: clip-path;
    }
    ::view-transition-old(root) {
      z-index: 9998;
      animation: none;
    }
    @keyframes _theme_ripple {
      from { clip-path: var(--theme-ripple-from, circle(0px at 50% 50%)); }
      to   { clip-path: var(--theme-ripple-to,   circle(200vmax at 50% 50%)); }
    }
  `;
  document.head.appendChild(vt);

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    // Update label text if it exists (sidebar toggle)
    const label = document.getElementById('theme-toggle-label');
    if (label) label.textContent = theme === 'dark' ? 'Light Mode' : 'Dark Mode';
  }

  function toggleTheme(btn) {
    const current  = document.documentElement.getAttribute('data-theme') || 'dark';
    const next     = current === 'dark' ? 'light' : 'dark';

    // Get the center of the toggle button for the ripple origin
    const rect = btn.getBoundingClientRect();
    const x    = Math.round(rect.left + rect.width  / 2);
    const y    = Math.round(rect.top  + rect.height / 2);
    const from = `circle(0px at ${x}px ${y}px)`;
    const to   = `circle(200vmax at ${x}px ${y}px)`;

    // Set CSS vars used by the @keyframes above
    document.documentElement.style.setProperty('--theme-ripple-from', from);
    document.documentElement.style.setProperty('--theme-ripple-to',   to);

    // Native View Transitions API (Chrome 111+, Firefox 126+)
    if (document.startViewTransition) {
      document.startViewTransition(() => { applyTheme(next); });
    } else {
      // Fallback: just switch instantly
      applyTheme(next);
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    // Sync label text after DOM ready
    const theme = document.documentElement.getAttribute('data-theme') || 'dark';
    const label = document.getElementById('theme-toggle-label');
    if (label) label.textContent = theme === 'dark' ? 'Light Mode' : 'Dark Mode';

    // Support #theme-toggle, .auth-theme-toggle, and .nav-theme-toggle buttons
    const btns = document.querySelectorAll('#theme-toggle, .auth-theme-toggle, .nav-theme-toggle');
    btns.forEach(btn => {
      btn.addEventListener('click', () => toggleTheme(btn));
    });
  });
})();
