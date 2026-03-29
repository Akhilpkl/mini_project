// ─── PAGE TRANSITION SYSTEM ────────────────────────────────
// Uses CSS classes .page-enter and .page-exit on #pageWrapper

(function () {
  'use strict';

  // Create the top progress bar element
  const bar = document.createElement('div');
  bar.id = 'nav-bar';
  bar.style.cssText = `
    position: fixed;
    top: 0; left: 0;
    height: 2px;
    width: 0%;
    background: linear-gradient(90deg, #7C3AED, #4F46E5, #06B6D4);
    z-index: 99999;
    transition: width 0.3s ease, opacity 0.4s ease;
    pointer-events: none;
    box-shadow: 0 0 8px rgba(124,58,237,.6);
  `;
  document.documentElement.appendChild(bar);

  function startBar() {
    bar.style.opacity = '1';
    bar.style.width = '70%';
  }
  function finishBar() {
    bar.style.width = '100%';
    setTimeout(() => { bar.style.opacity = '0'; bar.style.width = '0%'; }, 300);
  }

  // ─── Page wrapper fade-in on load ────────────────────────
  document.documentElement.style.opacity = '0';
  document.documentElement.style.transform = 'translateY(8px)';
  document.documentElement.style.transition = 'opacity 0.35s ease, transform 0.35s ease';

  window.addEventListener('pageshow', function (e) {
    // pageshow fires after bfcache restores as well
    requestAnimationFrame(() => {
      document.documentElement.style.opacity = '1';
      document.documentElement.style.transform = 'translateY(0)';
    });
    finishBar();
  });

  // ─── Intercept link clicks ───────────────────────────────
  document.addEventListener('click', function (e) {
    const link = e.target.closest('a[href]');
    if (!link) return;

    const href = link.getAttribute('href');

    // Skip: anchors, external links, new tab, download, javascript:, mailto:, tel:
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

    // Fade + slide page out
    document.documentElement.style.transition = 'opacity 0.22s ease, transform 0.22s ease';
    document.documentElement.style.opacity = '0';
    document.documentElement.style.transform = 'translateY(-6px)';

    setTimeout(() => {
      window.location.href = href;
    }, 220);
  });

  // ─── Form submit transitions ─────────────────────────────
  document.addEventListener('submit', function (e) {
    const form = e.target;
    // Only animate non-AJAX same-page forms
    if (form.method && form.method.toLowerCase() !== 'dialog') {
      startBar();
    }
  });

})();

// ─── Sidebar card hover animations (existing) ────────────
document.addEventListener('DOMContentLoaded', function () {
  // Stagger-animate cards on initial page load
  const cards = document.querySelectorAll('.dash-card, .glass-card, .stat-card, .feature-card');
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
