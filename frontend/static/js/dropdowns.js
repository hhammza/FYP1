/* ============================================================
   AMRPredict — Dynamic Dropdowns
   Fetches lists from the Flask API and populates any
   <select data-populate="..."> elements on the page.

   Supported data-populate values:
     "antibiotics"  → GET /api/antibiotics  (plain array)
     "organisms"    → GET /api/organisms    (plain array)
     "mic-sign"     → built-in static list  (no fetch)

   Pre-selection after a POST:
     Add data-selected="<value>" to the <select> element.
     The matching <option> is automatically set to selected.

   Caching:
     Fetched lists are cached in sessionStorage so the API is
     only called once per browser tab, even across navigations.
   ============================================================ */

(function () {
  'use strict';

  /* ── Static lists (no fetch needed) ──────────────────────── */
  const STATIC = {
    'mic-sign': [
      { value: '<=', label: '≤  (less than or equal)' },
      { value: '<',  label: '<  (less than)' },
      { value: '=',  label: '=  (equal)' },
      { value: '>',  label: '>  (greater than)' },
      { value: '>=', label: '≥  (greater than or equal)' },
    ],
  };

  /* ── API endpoints ────────────────────────────────────────── */
  const ENDPOINTS = {
    antibiotics: '/api/antibiotics',
    organisms:   '/api/organisms',
  };

  /* ── Fetch with sessionStorage cache ─────────────────────── */
  function fetchCached(key, url) {
    const cacheKey = 'amr_dropdown_' + key;
    const cached = sessionStorage.getItem(cacheKey);
    if (cached) {
      try { return Promise.resolve(JSON.parse(cached)); } catch (_) {}
    }
    return fetch(url)
      .then(r => r.json())
      .then(data => {
        try { sessionStorage.setItem(cacheKey, JSON.stringify(data)); } catch (_) {}
        return data;
      });
  }

  /* ── Build <option> elements for a select ─────────────────── */
  function populateSelect(select, items, selectedValue) {
    /* keep the placeholder option */
    const placeholder = select.querySelector('option[value=""]');
    select.innerHTML = '';
    if (placeholder) select.appendChild(placeholder);

    items.forEach(item => {
      const opt = document.createElement('option');
      if (typeof item === 'string') {
        opt.value = item;
        opt.textContent = item.charAt(0).toUpperCase() + item.slice(1);
      } else {
        opt.value = item.value;
        opt.textContent = item.label;
      }
      if (selectedValue && opt.value === selectedValue) {
        opt.selected = true;
      }
      select.appendChild(opt);
    });

    /* remove the temporary "Loading…" placeholder if present */
    const loading = select.querySelector('option[disabled]');
    if (loading) loading.remove();
  }

  /* ── Process all data-populate selects on the page ────────── */
  function initSelects() {
    const selects = document.querySelectorAll('select[data-populate]');
    if (!selects.length) return;

    selects.forEach(select => {
      const key      = select.dataset.populate;
      const selected = select.dataset.selected || '';

      if (STATIC[key]) {
        populateSelect(select, STATIC[key], selected);
        return;
      }

      const url = ENDPOINTS[key];
      if (!url) return;

      fetchCached(key, url)
        .then(data => populateSelect(select, data, selected))
        .catch(() => {
          /* fail silently — leave whatever HTML options were there */
        });
    });
  }

  /* ── Searchable antibiotic input (optional enhancement) ───── */
  function enhanceAntibioticSelects() {
    document.querySelectorAll('select[data-populate="antibiotics"]').forEach(select => {
      /* If a search wrapper already exists, skip */
      if (select.parentElement.classList.contains('select-search-wrap')) return;

      const wrapper = document.createElement('div');
      wrapper.className = 'select-search-wrap';
      wrapper.style.cssText = 'position:relative;';
      select.parentNode.insertBefore(wrapper, select);
      wrapper.appendChild(select);

      const search = document.createElement('input');
      search.type = 'text';
      search.placeholder = 'Type to filter…';
      search.className = 'form-control form-control-custom';
      search.style.cssText = 'margin-bottom:6px;font-size:13px;';
      search.setAttribute('aria-label', 'Filter antibiotic list');
      wrapper.insertBefore(search, select);

      search.addEventListener('input', function () {
        const q = this.value.toLowerCase();
        Array.from(select.options).forEach(opt => {
          if (!opt.value) return; /* keep placeholder */
          opt.hidden = q.length > 0 && !opt.textContent.toLowerCase().includes(q);
        });
        /* auto-select if exactly one visible match */
        const visible = Array.from(select.options).filter(o => o.value && !o.hidden);
        if (visible.length === 1) {
          select.value = visible[0].value;
        }
      });
    });
  }

  /* ── Run on DOMContentLoaded ──────────────────────────────── */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      initSelects();
      enhanceAntibioticSelects();
    });
  } else {
    initSelects();
    enhanceAntibioticSelects();
  }

})();
