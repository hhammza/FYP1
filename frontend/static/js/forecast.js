/* ============================================================
   AMRPredict — Forecast Page (resistance_forecast.html)
   Threshold slider, organism quick-fill, and comparison chart.
   Chart data is read from <script type="application/json" id="forecast-chart-data">.
   Expects: window.AMR (from main.js), Plotly (CDN)
   ============================================================ */

(function () {
  'use strict';

  /* ── Threshold slider ─────────────────────────────────────── */
  const slider    = document.getElementById('threshSlider');
  const sliderVal = document.getElementById('threshVal');
  if (slider && sliderVal) {
    slider.addEventListener('input', function () {
      sliderVal.textContent = this.value;
    });
  }

  /* ── Quick-fill organism ──────────────────────────────────── */
  window.fillOrganism = function (val) {
    if (!val) return;
    const parts = val.split(':');
    document.querySelector('[name=genus]').value    = parts[0] || '';
    document.querySelector('[name=species]').value  = parts[1] || '';
    document.querySelector('[name=taxon_id]').value = parts[2] || '';
  };

  /* ── Probability bar (width set from data-prob attribute) ──── */
  const probBar = document.querySelector('.prob-bar-fill[data-prob]');
  if (probBar) {
    probBar.style.width = parseFloat(probBar.dataset.prob).toFixed(1) + '%';
  }

  /* ── Comparison chart ─────────────────────────────────────── */
  function renderChart(compData) {
    if (!compData || !compData.length) return;

    const labels = compData.map(d => d.antibiotic);
    const values = compData.map(d => d.resistance_probability);
    const colors = values.map(v =>
      v > 50 ? 'rgba(239,68,68,0.82)' :
      v > 30 ? 'rgba(245,158,11,0.82)' :
               'rgba(34,197,94,0.82)'
    );
    const t = AMR.plotLayout();

    Plotly.newPlot('comparisonChart', [{
      type: 'bar',
      x: labels,
      y: values,
      marker: { color: colors, line: { color: t.lineColor, width: 1 } },
      text: values.map(v => v.toFixed(1) + '%'),
      textposition: 'outside',
      textfont: { color: t.tickColor, size: 11 },
      hovertemplate: '%{x}<br>Resistance: %{y:.1f}%<extra></extra>',
    }], {
      paper_bgcolor: t.paper_bgcolor,
      plot_bgcolor:  t.plot_bgcolor,
      margin: { t: 20, b: 100, l: 44, r: 20 },
      xaxis: {
        tickangle: -35,
        tickfont: { color: t.tickColor, size: 11 },
        gridcolor: t.gridColor,
        linecolor: t.gridColor,
      },
      yaxis: {
        tickfont: { color: t.tickColor },
        gridcolor: t.gridColor,
        range: [0, 115],
        ticksuffix: '%',
      },
      shapes: [{
        type: 'line',
        x0: -0.5, x1: labels.length - 0.5,
        y0: 50,   y1: 50,
        line: { color: 'rgba(239,68,68,0.55)', width: 1.5, dash: 'dash' },
      }],
      annotations: [{
        x: labels.length - 1, y: 53,
        text: '50% threshold',
        font: { color: 'rgba(239,68,68,0.75)', size: 10 },
        showarrow: false,
      }],
      font: { family: t.fontFamily },
    }, { responsive: true, displayModeBar: false });
  }

  /* Auto-init from data island */
  const dataEl = document.getElementById('forecast-chart-data');
  if (dataEl) {
    try { renderChart(JSON.parse(dataEl.textContent)); } catch (_) {}
  }

})();
