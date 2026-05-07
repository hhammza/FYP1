/* AMRPredict — Main JavaScript */
'use strict';

document.addEventListener('DOMContentLoaded', function () {
  initNavbar();
  initFormSubmitLoading();
  initTooltips();
  animateNumbers();
});

function initNavbar() {
  const nav = document.getElementById('mainNav');
  if (!nav) return;
  window.addEventListener('scroll', () => {
    nav.style.boxShadow = window.scrollY > 20
      ? '0 4px 24px rgba(0,0,0,0.5)'
      : 'none';
  });
}

function initFormSubmitLoading() {
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function (e) {
      const btn = form.querySelector('[type=submit]');
      if (!btn) return;
      const original = btn.innerHTML;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Processing...';
      btn.disabled = true;
      setTimeout(() => {
        btn.innerHTML = original;
        btn.disabled = false;
      }, 30000);
    });
  });
}

function initTooltips() {
  const tooltipEls = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipEls.forEach(el => new bootstrap.Tooltip(el));
}

function animateNumbers() {
  const els = document.querySelectorAll('.stat-mini-value');
  els.forEach(el => {
    const text = el.textContent;
    const num = parseFloat(text.replace(/[^0-9.]/g, ''));
    if (!isNaN(num) && num > 0 && text.length < 10) {
      animateCount(el, 0, num, text, 800);
    }
  });
}

function animateCount(el, start, end, originalText, duration) {
  const suffix = originalText.replace(/[0-9.,]/g, '').trim();
  const isFloat = originalText.includes('.');
  const decimals = isFloat ? (originalText.split('.')[1] || '').length : 0;
  const startTime = performance.now();

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = start + (end - start) * eased;
    el.textContent = (isFloat ? current.toFixed(decimals) : Math.round(current).toLocaleString()) + (suffix ? ' ' + suffix : '');
    if (progress < 1) requestAnimationFrame(update);
    else el.textContent = originalText;
  }
  requestAnimationFrame(update);
}

/* Probability meter animation on result pages */
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.prob-bar-fill').forEach(bar => {
    const w = bar.style.width;
    bar.style.width = '0';
    setTimeout(() => { bar.style.width = w; }, 200);
  });
});

/* Auto-dismiss alerts after 8 seconds */
document.querySelectorAll('.alert').forEach(alert => {
  if (alert.classList.contains('alert-success-custom')) {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.5s';
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 500);
    }, 8000);
  }
});
