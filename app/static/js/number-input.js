/**
 * NumberInput — Vanilla JS animated number input (NumberFlow-equivalent)
 * Replaces <input type="number"> fields marked with data-number-input
 *
 * Usage in HTML:
 *   <input type="number" data-number-input min="2000" max="2030" value="2022" name="graduation_year">
 */

(function () {
  'use strict';

  /**
   * Animates a digit element rolling from oldVal to newVal.
   * Creates a vertical "slot machine" style roll.
   */
  function rollDigits(displayEl, oldVal, newVal) {
    const going_up = newVal > oldVal;
    const diff = Math.abs(newVal - oldVal);
    const steps = Math.min(diff, 8);

    // ── Lock the container height BEFORE touching content ──
    // This is what prevents the wrapper bar from shrinking/growing.
    const lockedH = displayEl.offsetHeight || 44;
    displayEl.style.height  = lockedH + 'px';
    displayEl.style.overflow = 'hidden';
    displayEl.style.position = 'relative';

    displayEl.textContent = '';

    // Build vertical strip
    const strip = document.createElement('div');
    strip.style.cssText = `
      display: flex;
      flex-direction: column;
      will-change: transform;
    `;

    const nums = [];
    for (let i = 0; i <= steps; i++) {
      const n = going_up
        ? oldVal + Math.round((i / steps) * (newVal - oldVal))
        : oldVal - Math.round((i / steps) * diff);
      nums.push(n);
    }

    nums.forEach((n) => {
      const span = document.createElement('span');
      span.textContent = String(n);
      span.style.cssText = `
        display: flex;
        align-items: center;
        justify-content: center;
        height: ${lockedH}px;
        flex-shrink: 0;
      `;
      strip.appendChild(span);
    });

    displayEl.appendChild(strip);

    // Slide the strip (each item is exactly lockedH px tall)
    requestAnimationFrame(() => {
      strip.style.transition = 'transform 0.38s cubic-bezier(0.16, 1, 0.3, 1)';
      strip.style.transform  = `translateY(-${steps * lockedH}px)`;
    });

    setTimeout(() => {
      displayEl.textContent = String(newVal);
      displayEl.style.height   = '';
      displayEl.style.overflow = '';
      displayEl.style.position = '';
    }, 420);
  }

  /**
   * Builds the widget DOM around a hidden <input>.
   */
  function buildWidget(input) {
    const min = parseInt(input.min) || 1900;
    const max = parseInt(input.max) || new Date().getFullYear() + 10;
    let value = parseInt(input.value) || parseInt(input.min) || new Date().getFullYear();

    // Clamp initial value
    value = Math.min(Math.max(value, min), max);
    input.value = value;

    // Hide original input (keep in DOM for form submission)
    input.type = 'hidden';

    // ── Wrapper ──────────────────────────────────────────────
    const wrapper = document.createElement('div');
    wrapper.className = 'ni-wrapper';
    wrapper.setAttribute('role', 'group');
    wrapper.setAttribute('aria-label', input.name || 'Number input');

    // ── Minus button ─────────────────────────────────────────
    const btnMinus = document.createElement('button');
    btnMinus.type = 'button';
    btnMinus.className = 'ni-btn ni-btn-minus';
    btnMinus.setAttribute('aria-label', 'Decrease');
    btnMinus.setAttribute('tabindex', '-1');
    btnMinus.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round"><line x1="5" y1="12" x2="19" y2="12"/></svg>`;

    // ── Display ───────────────────────────────────────────────
    const display = document.createElement('div');
    display.className = 'ni-display';
    display.setAttribute('aria-live', 'polite');
    display.textContent = String(value);

    // ── Plus button ───────────────────────────────────────────
    const btnPlus = document.createElement('button');
    btnPlus.type = 'button';
    btnPlus.className = 'ni-btn ni-btn-plus';
    btnPlus.setAttribute('aria-label', 'Increase');
    btnPlus.setAttribute('tabindex', '-1');
    btnPlus.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>`;

    wrapper.appendChild(btnMinus);
    wrapper.appendChild(display);
    wrapper.appendChild(btnPlus);

    // Insert after the original input
    input.parentNode.insertBefore(wrapper, input.nextSibling);

    // ── State ─────────────────────────────────────────────────
    function updateButtons() {
      btnMinus.disabled = value <= min;
      btnPlus.disabled  = value >= max;
      btnMinus.classList.toggle('ni-btn-disabled', value <= min);
      btnPlus.classList.toggle('ni-btn-disabled', value >= max);
    }

    function setValue(newVal) {
      newVal = Math.min(Math.max(newVal, min), max);
      if (newVal === value) return;

      const oldVal = value;
      value = newVal;
      input.value = value;

      // Dispatch change event so Flask-WTF picks up the value
      input.dispatchEvent(new Event('change', { bubbles: true }));

      rollDigits(display, oldVal, newVal);
      updateButtons();
    }

    // ── Events ────────────────────────────────────────────────
    btnMinus.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      setValue(value - 1);
      wrapper.focus();
    });

    btnPlus.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      setValue(value + 1);
      wrapper.focus();
    });

    // Keyboard support (arrow keys / scroll)
    wrapper.tabIndex = 0;
    wrapper.addEventListener('keydown', (e) => {
      if (e.key === 'ArrowUp'   || e.key === 'ArrowRight') { e.preventDefault(); setValue(value + 1); }
      if (e.key === 'ArrowDown' || e.key === 'ArrowLeft')  { e.preventDefault(); setValue(value - 1); }
      if (e.key === 'Home') { e.preventDefault(); setValue(min); }
      if (e.key === 'End')  { e.preventDefault(); setValue(max); }
    });

    // Mouse wheel
    wrapper.addEventListener('wheel', (e) => {
      if (document.activeElement !== wrapper) return;
      e.preventDefault();
      setValue(e.deltaY < 0 ? value + 1 : value - 1);
    }, { passive: false });

    // Long-press repeat
    let repeatTimer = null;
    function startRepeat(dir) {
      stopRepeat();
      repeatTimer = setTimeout(() => {
        repeatTimer = setInterval(() => setValue(value + dir), 80);
      }, 400);
    }
    function stopRepeat() {
      clearTimeout(repeatTimer);
      clearInterval(repeatTimer);
      repeatTimer = null;
    }

    btnMinus.addEventListener('pointerdown', () => startRepeat(-1));
    btnPlus.addEventListener('pointerdown',  () => startRepeat(+1));
    document.addEventListener('pointerup', stopRepeat);

    updateButtons();
  }

  // ── Init ────────────────────────────────────────────────────
  function init() {
    document.querySelectorAll('input[data-number-input]').forEach(buildWidget);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
