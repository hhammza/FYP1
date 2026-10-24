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

  /* ── Linked organism lists: genus → species → taxon ID ────────
     Built from /api/vocabulary's `organisms` (backend/api/organisms.py):
     only genera, species and taxon IDs the model was trained on, and a
     species is offered only under the genus it really belongs to ('coli'
     is Escherichia coli or Campylobacter coli). */
  const genusSel   = document.getElementById('genusSelect');
  const speciesSel = document.getElementById('speciesSelect');
  const taxonSel   = document.getElementById('taxonSelect');
  const abSel      = document.querySelector('#forecastForm [name=antibiotic]');
  const micInput   = document.getElementById('micInput');
  const preview    = document.getElementById('evidencePreview');
  const previewText = document.getElementById('evidencePreviewText');
  let tree = [];

  function setHint(hintId, text) {
    const hint = document.getElementById(hintId);
    if (hint) hint.textContent = text;
  }

  function option(value, label) {
    const o = document.createElement('option');
    o.value = value;
    o.textContent = label;
    return o;
  }

  function fillSelect(sel, placeholder, items, wanted) {
    sel.innerHTML = '';
    sel.appendChild(option('', placeholder));
    items.forEach(([value, label]) => sel.appendChild(option(value, label)));
    sel.disabled = items.length === 0;
    const match = items.find(([v]) => String(v).toLowerCase() === String(wanted || '').toLowerCase());
    sel.value = match ? match[0] : '';
  }

  const currentGenus = () => tree.find(g => g.genus === genusSel.value);

  function fillSpecies(wanted) {
    const g = currentGenus();
    /* the genus is already shown beside it, so the species name alone fits the narrow box */
    const items = g ? g.species.map(s => [s.name, s.name]) : [];
    fillSelect(speciesSel, !g ? '-- Choose a genus first --'
                         : items.length ? '-- Any species --' : '-- None listed for this genus --', items, wanted);
    setHint('speciesHint', g && items.length ? `${items.length} species of ${g.genus}` : '');
  }

  function fillTaxa(wanted) {
    const g = currentGenus();
    let items = [];
    if (g) {
      const sp = g.species.find(s => s.name === speciesSel.value);
      const ofSpecies = s => s.taxon_ids.map(id => [String(id), `${id} · ${s.label}`]);
      items = sp ? ofSpecies(sp)
                 : g.species.flatMap(ofSpecies).concat(g.other_taxon_ids.map(o => [String(o.id), `${o.id} · ${o.label}`]));
    }
    fillSelect(taxonSel, !g ? '-- Choose a genus first --'
                       : items.length ? '-- None --' : '-- No ID for this choice --', items, wanted);
    setHint('taxonHint', items.length ? 'Only IDs the model has a resistance rate for' : '');
  }

  /* ── MIC suggestions for the chosen drug and organism ─────── */
  const LEVEL = { species: 'this species', genus: 'this genus', antibiotic: 'all organisms' };
  let micRequest = 0;
  function refreshMic() {
    const ab = abSel ? abSel.value : '';
    const list = document.getElementById('micList');
    if (!ab || !list) { if (list) list.innerHTML = ''; setHint('micHint', ''); return; }
    const q = new URLSearchParams({ antibiotic: ab, genus: genusSel.value, species: speciesSel.value });
    const mine = ++micRequest;
    fetch('/api/mic-values?' + q)
      .then(r => r.json())
      .then(d => {
        if (mine !== micRequest) return;               /* a newer choice was made meanwhile */
        list.innerHTML = '';
        (d.values || []).forEach(v => list.appendChild(option(v, `${v} mg/L`)));
        const who = d.level === 'species' && speciesSel.value
          ? `${genusSel.value} ${speciesSel.value}` : d.level === 'genus' ? genusSel.value : LEVEL.antibiotic;
        setHint('micHint', d.values && d.values.length
          ? `Suggested: MICs recorded in BV-BRC for ${who} and ${d.antibiotic}. Any value can be typed.`
          : 'No recorded MICs to suggest for this choice; any value can be typed.');
      })
      .catch(() => setHint('micHint', ''));
  }

  if (genusSel) genusSel.addEventListener('change', () => { fillSpecies(); fillTaxa(); refreshMic(); refreshRecognition(); });
  if (speciesSel) speciesSel.addEventListener('change', () => { fillTaxa(); refreshMic(); refreshRecognition(); });
  if (taxonSel) taxonSel.addEventListener('change', refreshRecognition);
  if (abSel) abSel.addEventListener('change', refreshMic);
  if (micInput) micInput.addEventListener('input', refreshRecognition);

  /* ── Quick-fill organism ──────────────────────────────────── */
  window.fillOrganism = function (val) {
    if (!val || !genusSel) return;
    const [genus, species] = val.split(':');
    const g = tree.find(x => x.genus.toLowerCase() === (genus || '').toLowerCase());
    genusSel.value = g ? g.genus : '';
    fillSpecies(species);
    fillTaxa();
    refreshMic();
    refreshRecognition();
  };

  function refreshRecognition() {
    /* Headline: what the result will actually represent */
    if (!preview || !previewText) return;
    const hasMic = micInput && micInput.value.trim() !== '';
    const hasOrg = !!(genusSel && genusSel.value) || !!(taxonSel && taxonSel.value);
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

  const treeReady = fetch('/api/vocabulary')
    .then(r => r.json())
    .then(data => {
      const vocab = data && data.lgbm;
      tree = (vocab && vocab.organisms) || [];
      if (!genusSel) return;
      if (!tree.length) {
        setHint('genusHint', 'The organism lists need the backend; the result uses population rates without them.');
        return;
      }
      /* After a submit the page comes back with the choices made: keep them */
      fillSelect(genusSel, '-- Any genus --', tree.map(g => [g.genus, g.genus]), genusSel.dataset.selected);
      fillSpecies(speciesSel.dataset.selected);
      fillTaxa(taxonSel.dataset.selected);
      setHint('genusHint', `${tree.length} genera the model was trained on`);
      refreshMic();
      refreshRecognition();
    })
    .catch(() => {});

  /* ── Fill from Genome ID ──────────────────────────────────────
     /api/genome/<id> (backend/api/genome_lookup.py): the organism to fill,
     the genome's laboratory results and whether the forecaster trained on
     it. The ID is never sent to the model; a training genome gets a caution,
     since its prediction looks better than a new genome's would. */
  const genomeInput = document.getElementById('genomeIdInput');
  const genomeBtn   = document.getElementById('genomeFillBtn');
  const genomeInfo  = document.getElementById('genomeInfo');
  const GENOME_ID   = /^\d{1,9}\.\d{1,9}$/;
  let genomeRequest = 0;

  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  function line(icon, text, cls) {
    const p = el('div', 'genome-info-line' + (cls ? ' ' + cls : ''));
    p.appendChild(el('i', 'bi bi-' + icon + ' me-1'));
    p.appendChild(document.createTextNode(text));
    return p;
  }

  function micText(r) {
    if (!r.value) return '';
    const sign = r.sign && r.sign !== '=' ? r.sign + ' ' : '';
    if (r.is_mic || (r.unit || '').toLowerCase() === 'mg/l') return ` (MIC ${sign}${r.value} mg/L)`;
    return ` (${r.value}${r.unit ? ' ' + r.unit : ''}, not a MIC)`;
  }

  function predictionShown() {
    const label = document.querySelector('.result-main-label');
    return label ? label.textContent.trim() : '';
  }

  function showGenome(d) {
    genomeInfo.innerHTML = '';
    genomeInfo.classList.remove('d-none');
    const o = d.organism || {};
    const filled = [o.genus, o.species, o.taxon_id].filter(Boolean).length;
    genomeInfo.appendChild(line('bacteria',
      (o.name || `Taxon ${d.taxon_id}`) + (filled ? '' : ': not an organism the model knows, so nothing was filled')));

    /* Did the forecaster see this genome? Hamza's genome_status (format §7) */
    const f = (d.models || {}).forecast;
    if (f && f.role === 'train') {
      genomeInfo.appendChild(line('exclamation-triangle',
        'The forecaster was trained on this genome, so its prediction will look better than on a new genome.',
        'genome-info-warn'));
    } else if (f && f.role === 'test') {
      genomeInfo.appendChild(line('check-circle', 'Not used in training: a fair test of the forecaster.', 'genome-info-ok'));
    } else if (f) {
      genomeInfo.appendChild(line('dash-circle', "Not in the forecaster's data."));
    }

    /* The genome's lab result for the chosen drug, and the model's call beside it */
    const ab = abSel && abSel.value;
    const labs = d.lab_for_antibiotic || [];
    if (ab && labs.length) {
      const r = labs[0];
      const shown = predictionShown();
      const agree = shown && r.phenotype ? (shown === (r.phenotype === 'Intermediate' ? 'Resistant' : r.phenotype)) : null;
      genomeInfo.appendChild(line('clipboard2-pulse',
        `Lab result for ${ab}: ${r.phenotype || 'no phenotype recorded'}${micText(r)}` +
        (r.method ? `, ${r.method}` : '') + (labs.length > 1 ? ` (${labs.length} results)` : '') +
        (agree === null ? '' : agree ? '. The model agrees.' : `. The model said ${shown}.`)));
      if (r.is_mic && r.value && micInput) {
        const use = el('button', 'btn btn-link btn-sm p-0 ms-1 genome-use-mic', 'Use this MIC');
        use.type = 'button';
        use.addEventListener('click', () => {
          micInput.value = r.value;
          const sign = document.querySelector('#forecastForm [name=mic_sign]');
          if (sign) sign.value = r.sign || '=';
          refreshRecognition();
        });
        genomeInfo.lastChild.appendChild(use);
      }
    } else {
      const n = (d.lab_results || []).length;
      genomeInfo.appendChild(line('clipboard2',
        n ? `${n} lab result${n === 1 ? '' : 's'} for this genome, ${ab ? 'none for ' + ab : 'choose an antibiotic to see one'}.`
          : 'No laboratory result for this genome in our data.'));
    }
    const genes = el('a', 'genome-info-link', 'Resistance genes for this genome');
    genes.href = d.genes_url;
    genomeInfo.appendChild(genes);
  }

  function lookupGenome(fillForm) {
    const id = genomeInput.value.trim();
    if (!id) { genomeInfo.classList.add('d-none'); return; }
    if (!GENOME_ID.test(id)) {
      genomeInfo.innerHTML = '';
      genomeInfo.appendChild(line('exclamation-circle', 'A BV-BRC Genome ID looks like 562.1234 (taxon ID, a dot, a number).', 'genome-info-warn'));
      genomeInfo.classList.remove('d-none');
      return;
    }
    const mine = ++genomeRequest;
    const q = new URLSearchParams({ antibiotic: abSel ? abSel.value : '' });
    Promise.all([fetch(`/api/genome/${encodeURIComponent(id)}?${q}`).then(r => r.json()), treeReady])
      .then(([d]) => {
        if (mine !== genomeRequest) return;
        if (d.error) {
          genomeInfo.innerHTML = '';
          genomeInfo.appendChild(line('exclamation-circle', d.error, 'genome-info-warn'));
          genomeInfo.classList.remove('d-none');
          return;
        }
        if (fillForm && d.organism && d.organism.genus) {
          genusSel.value = d.organism.genus;
          fillSpecies(d.organism.species);
          fillTaxa(d.organism.taxon_id);
          refreshMic();
          refreshRecognition();
        }
        showGenome(d);
      })
      .catch(() => {});
  }

  if (genomeBtn) genomeBtn.addEventListener('click', () => lookupGenome(true));
  if (genomeInput) genomeInput.addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); lookupGenome(true); }    /* fill, don't submit */
  });
  /* the lab result shown follows the chosen drug */
  if (abSel) abSel.addEventListener('change', () => { if (genomeInput && genomeInput.value.trim()) lookupGenome(false); });
  /* after a submit: show it again, now beside the prediction (the form is already filled) */
  if (genomeInput && genomeInput.value.trim()) {
    const again = () => lookupGenome(false);
    if (abSel && !abSel.value) {
      const w = new MutationObserver(() => { if (abSel.value) { w.disconnect(); again(); } });
      w.observe(abSel, { childList: true });
    } else {
      again();
    }
  }

  /* The antibiotic list is filled by dropdowns.js, so the MIC suggestions
     for a restored choice wait until it has a value */
  if (abSel && !abSel.value) {
    const watch = new MutationObserver(() => { if (abSel.value) { watch.disconnect(); refreshMic(); } });
    watch.observe(abSel, { childList: true });
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
        automargin: true,
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

  /* ── Batch chart: resistant vs susceptible rows per antibiotic ── */
  function renderBatchChart(byAb) {
    if (!byAb || !byAb.length || !document.getElementById('batchChart')) return;
    const t = AMR.plotLayout();
    const labels = byAb.map(d => d.antibiotic);
    const bar = (name, values, color) => ({
      type: 'bar', name: name, x: labels, y: values,
      marker: { color: color },
      hovertemplate: '%{x}<br>' + name + ': %{y}<extra></extra>',
    });
    Plotly.newPlot('batchChart', [
      bar('Resistant', byAb.map(d => d.resistant), 'rgba(239,68,68,0.82)'),
      bar('Susceptible', byAb.map(d => d.n - d.resistant), 'rgba(34,197,94,0.82)'),
    ], {
      barmode: 'stack',
      paper_bgcolor: t.paper_bgcolor,
      plot_bgcolor: t.plot_bgcolor,
      margin: { t: 20, b: 100, l: 50, r: 20 },
      xaxis: { tickangle: -35, tickfont: { color: t.tickColor, size: 11 }, gridcolor: t.gridColor, linecolor: t.gridColor },
      yaxis: { title: { text: 'Rows', font: { color: t.tickColor } }, tickfont: { color: t.tickColor }, gridcolor: t.gridColor },
      legend: { orientation: 'h', y: 1.12, font: { color: t.tickColor } },
      font: { family: t.fontFamily },
    }, { responsive: true, displayModeBar: false });
  }

  const batchEl = document.getElementById('batch-chart-data');
  if (batchEl) {
    try { renderBatchChart(JSON.parse(batchEl.textContent)); } catch (_) {}
  }

  /* Auto-init from data island */
  const dataEl = document.getElementById('forecast-chart-data');
  if (dataEl) {
    const thr = parseFloat(dataEl.dataset.threshold);
    try { renderChart(JSON.parse(dataEl.textContent), isNaN(thr) ? 50 : thr * 100); } catch (_) {}
  }

})();
