/* AMRPredict — Main JavaScript */
'use strict';

/* ── GLOBAL HELPERS (available before DOMContentLoaded) ──────── */
window.AMR = {
  /* Returns Plotly-compatible layout fragment that adapts to current theme */
  plotLayout() {
    const dark = document.documentElement.getAttribute('data-theme') === 'dark';
    return {
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor:  'rgba(0,0,0,0)',
      tickColor:  dark ? '#94a3b8' : '#64748b',
      gridColor:  dark ? 'rgba(255,255,255,0.06)' : 'rgba(15,23,42,0.08)',
      lineColor:  dark ? 'rgba(255,255,255,0.10)' : 'rgba(15,23,42,0.12)',
      fontFamily: "'Inter',-apple-system,sans-serif",
    };
  },

  /* Show a toast notification */
  toast(message, type = 'info', title = null, duration = 5000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const icons = {
      success: 'check-circle-fill',
      error:   'exclamation-circle-fill',
      warning: 'exclamation-triangle-fill',
      info:    'info-circle-fill',
    };
    const labels = { success: 'Success', error: 'Error', warning: 'Warning', info: 'Notice' };
    const item = document.createElement('div');
    item.className = `toast-item toast-${type}`;
    item.innerHTML = `
      <i class="bi bi-${icons[type] || icons.info} toast-icon"></i>
      <div class="toast-body">
        <div class="toast-title">${title || labels[type]}</div>
        <div class="toast-msg">${message}</div>
      </div>
      <button class="toast-close" aria-label="Close"><i class="bi bi-x"></i></button>`;
    item.querySelector('.toast-close').addEventListener('click', () => AMR.dismissToast(item));
    container.appendChild(item);
    if (duration > 0) setTimeout(() => AMR.dismissToast(item), duration);
    return item;
  },

  dismissToast(item) {
    if (!item || item.classList.contains('toast-removing')) return;
    item.classList.add('toast-removing');
    setTimeout(() => item.remove(), 240);
  },
};

/* ── DARK MODE (run immediately — prevents flash) ────────────── */
(function initTheme() {
  const saved = localStorage.getItem('amr-theme');
  if (saved === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
})();

/* ── DOM READY ───────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function () {
  initNavbarScroll();
  initThemeToggle();
  initFormSubmitLoading();
  initTooltips();
  initNumberAnimation();
  initProbBars();
  initAlertAutoDismiss();
  initDragDrop();
});

/* ── NAVBAR SHADOW ON SCROLL ─────────────────────────────────── */
function initNavbarScroll() {
  const nav = document.getElementById('mainNav');
  if (!nav) return;
  const update = () => {
    nav.style.boxShadow = window.scrollY > 20
      ? '0 4px 24px rgba(0,0,0,0.15)'
      : '';
  };
  window.addEventListener('scroll', update, { passive: true });
  update();
}

/* ── DARK MODE TOGGLE ────────────────────────────────────────── */
function initThemeToggle() {
  const btn = document.getElementById('themeToggle');
  if (!btn) return;

  const isDark = () => document.documentElement.getAttribute('data-theme') === 'dark';

  function updateIcon() {
    btn.innerHTML = isDark()
      ? '<i class="bi bi-sun"></i>'
      : '<i class="bi bi-moon"></i>';
    btn.title = isDark() ? 'Switch to light mode' : 'Switch to dark mode';
  }

  updateIcon();

  btn.addEventListener('click', () => {
    if (isDark()) {
      document.documentElement.removeAttribute('data-theme');
      localStorage.setItem('amr-theme', 'light');
    } else {
      document.documentElement.setAttribute('data-theme', 'dark');
      localStorage.setItem('amr-theme', 'dark');
    }
    updateIcon();
    /* Re-render any active Plotly charts with correct colors */
    document.querySelectorAll('[id$="Chart"]').forEach(el => {
      if (el._fullLayout) {
        const t = AMR.plotLayout();
        Plotly.relayout(el, {
          'xaxis.tickfont.color': t.tickColor,
          'xaxis.gridcolor':      t.gridColor,
          'yaxis.tickfont.color': t.tickColor,
          'yaxis.gridcolor':      t.gridColor,
        }).catch(() => {});
      }
    });
  });
}

/* ── FORM SUBMIT LOADING STATE ───────────────────────────────── */
function initFormSubmitLoading() {
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function () {
      const btn = form.querySelector('[type=submit]');
      if (!btn) return;
      const orig = btn.innerHTML;
      btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Processing…';
      btn.disabled = true;
      /* Restore if server takes too long (30s) */
      setTimeout(() => { btn.innerHTML = orig; btn.disabled = false; }, 30000);
    });
  });
}

/* ── BOOTSTRAP TOOLTIPS ──────────────────────────────────────── */
function initTooltips() {
  document.querySelectorAll('[data-bs-toggle="tooltip"]')
    .forEach(el => new bootstrap.Tooltip(el));
}

/* ── NUMBER COUNTER ANIMATION (IntersectionObserver) ─────────── */
function initNumberAnimation() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const el = entry.target;
      const text = el.dataset.target || el.textContent;
      const num = parseFloat(text.replace(/[^0-9.]/g, ''));
      if (!isNaN(num) && num > 0 && text.length < 10) {
        animateCount(el, 0, num, text, 900);
      }
      observer.unobserve(el);
    });
  }, { threshold: 0.3 });

  document.querySelectorAll('.stat-mini-value, .stat-number, .hpanel-stat-val')
    .forEach(el => observer.observe(el));
}

function animateCount(el, start, end, originalText, duration) {
  const suffix  = originalText.replace(/[0-9.,]/g, '').trim();
  const isFloat = originalText.includes('.');
  const decimals = isFloat ? (originalText.split('.')[1] || '').replace(/[^0-9]/g, '').length : 0;
  const startTime = performance.now();

  function update(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = start + (end - start) * eased;
    el.textContent = (isFloat ? current.toFixed(decimals) : Math.round(current).toLocaleString())
      + (suffix ? ' ' + suffix : '');
    if (progress < 1) requestAnimationFrame(update);
    else el.textContent = originalText;
  }
  requestAnimationFrame(update);
}

/* ── PROBABILITY BAR ENTRANCE ANIMATION ──────────────────────── */
function initProbBars() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      entry.target.querySelectorAll('.prob-bar-fill, .hpanel-bar-fill, .kmer-bar, .gene-fill').forEach(bar => {
        const target = bar.style.width;
        bar.style.width = '0';
        requestAnimationFrame(() => {
          bar.style.transition = 'width 0.9s cubic-bezier(0.4,0,0.2,1)';
          bar.style.width = target;
        });
      });
      observer.unobserve(entry.target);
    });
  }, { threshold: 0.2 });

  document.querySelectorAll('.result-hero, .info-card, .gene-row, .hpanel-bars')
    .forEach(el => observer.observe(el));
}

/* ── AUTO-DISMISS ALERTS ─────────────────────────────────────── */
function initAlertAutoDismiss() {
  document.querySelectorAll('.alert-success-custom').forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.5s';
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 500);
    }, 7000);
  });
}

/* ── DRAG-AND-DROP FILE ZONES (generic) ──────────────────────── */
function initDragDrop() {
  document.querySelectorAll('.file-drop-zone').forEach(zone => {
    zone.addEventListener('dragover', e => {
      e.preventDefault();
      zone.classList.add('dragover');
    });
    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
    zone.addEventListener('drop', e => {
      e.preventDefault();
      zone.classList.remove('dragover');
      const input = zone.querySelector('input[type=file]');
      const nameEl = zone.parentElement.querySelector('[id^=fileName]') || zone.querySelector('[id^=fileName]');
      if (input && e.dataTransfer.files[0]) {
        try {
          input.files = e.dataTransfer.files;
        } catch (_) {}
        if (nameEl) nameEl.textContent = e.dataTransfer.files[0].name;
      }
    });
    /* Click-on-zone also opens file picker */
    zone.addEventListener('click', e => {
      if (e.target.tagName === 'LABEL' || e.target.tagName === 'INPUT') return;
      zone.querySelector('input[type=file]')?.click();
    });
  });
}
