/* ============================================================
   AMRPredict — shared chart helpers for the report pages
   (/models, /compare). Expects window.AMR (main.js) and Plotly.
   ============================================================ */
(function () {
  'use strict';

  /* Series colours come from CSS tokens so light and dark stay in one place */
  function palette() {
    const css = getComputedStyle(document.documentElement);
    const v = name => css.getPropertyValue(name).trim();
    return {
      c1: v('--viz-1'), c2: v('--viz-2'), c3: v('--viz-3'),
      c4: v('--viz-4'), c5: v('--viz-5'), other: v('--viz-other'),
      text: v('--text-1'), text2: v('--text-2'), card: v('--bg-card'),
      danger: v('--danger'),
      dark: document.documentElement.getAttribute('data-theme') === 'dark',
    };
  }

  /* Theme-aware Plotly layout; xaxis/yaxis in `extra` merge into the defaults */
  function layout(extra) {
    const t = AMR.plotLayout();
    const p = palette();
    const axis = {
      tickfont: { color: t.tickColor, size: 11 },
      gridcolor: t.gridColor, linecolor: t.lineColor, zeroline: false,
      title: { font: { color: t.tickColor, size: 12 } },
    };
    const base = {
      paper_bgcolor: t.paper_bgcolor, plot_bgcolor: t.plot_bgcolor,
      font: { family: t.fontFamily, color: p.text2 },
      margin: { t: 10, r: 16, b: 48, l: 56 },
      hoverlabel: { bgcolor: p.card, bordercolor: t.lineColor, font: { color: p.text, family: t.fontFamily } },
      legend: { orientation: 'h', y: -0.18, font: { color: p.text2, size: 11 } },
      xaxis: JSON.parse(JSON.stringify(axis)),
      yaxis: JSON.parse(JSON.stringify(axis)),
    };
    for (const key of Object.keys(extra || {})) {
      if (key === 'xaxis' || key === 'yaxis') {
        base[key] = Object.assign(base[key], extra[key]);
        if (extra[key].title) base[key].title = Object.assign({ font: axis.title.font }, extra[key].title);
      } else {
        base[key] = extra[key];
      }
    }
    return base;
  }

  function readData(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    try { return JSON.parse(el.textContent); } catch (_) { return null; }
  }

  /* Draw now, again once web fonts load (Plotly sizes legends with the
     fallback font), and again on theme change so series colours follow. */
  function draw(renderAll) {
    renderAll();
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(renderAll);
    const toggle = document.getElementById('themeToggle');
    if (toggle) toggle.addEventListener('click', () => setTimeout(renderAll, 0));
  }

  window.AMRReport = {
    config: { responsive: true, displayModeBar: false },
    palette, layout, readData, draw,
    fmt: x => x.toFixed(3),
    pct: x => (100 * x).toFixed(1) + '%',
    /* Plotly can undersize horizontal legend entries by a few pixels; pad so text is never clipped */
    legendName: name => name + '   ',
  };
})();
