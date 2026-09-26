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
      this.setAttribute('aria-valuenow', this.value);
    });
  }

  /* ── Quick-fill organism ──────────────────────────────────── */
  window.fillOrganism = function (val) {
    if (!val) return;
    const parts = val.split(':');
    document.querySelector('[name=genus]').value    = parts[0] || '';
    document.querySelector('[name=species]').value  = parts[1] || '';
    /* Taxon ID is deliberately not filled: the species-level IDs people
       recognise (562 for E. coli) are absent from the training data, so
       filling one would look meaningful while changing nothing. */
    refreshRecognition();
  };

  /* ── Input recognition: say up front what the model can use ──
     The model only has categories for the values it saw in training. A
     genus it does not know behaves exactly like a blank field, so the
     form says so before the user submits rather than after. */
  const genusInput   = document.getElementById('genusInput');
  const speciesInput = document.getElementById('speciesInput');
  const taxonInput   = document.getElementById('taxonInput');
  const micInput     = document.querySelector('[name=mic_value]');
  const preview      = document.getElementById('evidencePreview');
  const previewText  = document.getElementById('evidencePreviewText');
  let vocab = null;

  function setHint(el, hintId, ok, text) {
    const hint = document.getElementById(hintId);
    if (!hint) return;
    hint.textContent = text;
    hint.classList.toggle('hint-ok', ok === true);
    hint.classList.toggle('hint-warn', ok === false);
  }

  function inVocab(list, value) {
    if (!list || !value) return null;
    return list.some(v => String(v).toLowerCase() === value.trim().toLowerCase());
  }

  function refreshRecognition() {
    if (!vocab) return;

    const g = genusInput ? genusInput.value.trim() : '';
    const gOk = inVocab(vocab.genera, g);
    setHint(genusInput, 'genusHint', gOk,
      !g ? '' : gOk ? 'Recognised — will be used' : 'Not in the training data — will be ignored');

    const sp = speciesInput ? speciesInput.value.trim() : '';
    const sOk = inVocab(vocab.species, sp);
    setHint(speciesInput, 'speciesHint', sOk,
      !sp ? '' : sOk ? 'Recognised — will be used' : 'Not in the training data — will be ignored');

    const t = taxonInput ? taxonInput.value.trim() : '';
    const tOk = t ? (vocab.taxon_ids || []).includes(parseInt(t, 10)) : null;
    setHint(taxonInput, 'taxonHint', tOk,
      !t ? 'Only IDs present in the training data change the result'
         : tOk ? 'Recognised — organism-specific rate will be used'
               : 'Not in the training data — will be ignored');

    /* Headline: what the result will actually represent */
    if (!preview || !previewText) return;
    const hasMic = micInput && micInput.value.trim() !== '';
    const hasOrg = gOk === true || tOk === true;
    let msg = '';
    if (!hasMic && !hasOrg) {
      msg = 'With no MIC value and no recognised organism, the result will be the ' +
            'population resistance rate for the selected drug — the same number for any isolate.';
    } else if (!hasMic) {
      msg = 'Without an MIC value, the result reflects historical rates for this ' +
            'organism and drug, not this particular isolate.';
    } else if (!hasOrg) {
      msg = 'No recognised organism: the MIC drives the result, with population ' +
            'rates standing in for the species.';
    }
    previewText.textContent = msg;
    preview.classList.toggle('d-none', msg === '');
  }

  [genusInput, speciesInput, taxonInput, micInput].forEach(el => {
    if (el) el.addEventListener('input', refreshRecognition);
  });

  fetch('/api/vocabulary')
    .then(r => r.json())
    .then(data => {
      vocab = data && data.lgbm;
      if (!vocab) return;
      fillDatalist('genusList', vocab.genera);
      fillDatalist('speciesList', vocab.species);
      fillDatalist('taxonList', (vocab.taxon_ids || []).slice(0, 50));
      refreshRecognition();
    })
    .catch(() => {});

  function fillDatalist(id, values) {
    const dl = document.getElementById(id);
    if (!dl || !values) return;
    dl.innerHTML = '';
    values.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v;
      dl.appendChild(opt);
    });
  }

  /* ── Probability bar (width set from data-prob attribute) ──── */
  const probBar = document.querySelector('.prob-bar-fill[data-prob]');
  if (probBar) {
    probBar.style.width = parseFloat(probBar.dataset.prob).toFixed(1) + '%';
  }

  /* ── Comparison chart ─────────────────────────────────────── */
  /* thresholdPct: the model's decision threshold as a percentage, so a bar
     is red exactly when the model would call that drug Resistant */
  function renderChart(compData, thresholdPct) {
    if (!compData || !compData.length) return;

    const labels = compData.map(d => d.antibiotic);
    const values = compData.map(d => d.resistance_probability);
    const colors = values.map(v =>
      v >= thresholdPct       ? 'rgba(239,68,68,0.82)' :
      v >= thresholdPct * 0.6 ? 'rgba(245,158,11,0.82)' :
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
        y0: thresholdPct, y1: thresholdPct,
        line: { color: 'rgba(239,68,68,0.55)', width: 1.5, dash: 'dash' },
      }],
      annotations: [{
        x: labels.length - 1, y: thresholdPct + 3,
        text: Math.round(thresholdPct) + '% threshold',
        font: { color: 'rgba(239,68,68,0.75)', size: 10 },
        showarrow: false,
      }],
      font: { family: t.fontFamily },
    }, { responsive: true, displayModeBar: false });
  }

  /* Auto-init from data island */
  const dataEl = document.getElementById('forecast-chart-data');
  if (dataEl) {
    const thr = parseFloat(dataEl.dataset.threshold);
    try { renderChart(JSON.parse(dataEl.textContent), isNaN(thr) ? 50 : thr * 100); } catch (_) {}
  }

})();
