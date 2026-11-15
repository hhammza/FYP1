/* ============================================================
   AMRPredict: Timeline Page (mutation_timeline.html), two tabs.
   The what-if simulation tab (format §4, not a trained model): weeks slider,
   genome upload (suffix 3), the weekly chart from <script id="timeline-chart-data">
   and the RL panel from <script id="rl-data">.
   The ML trend forecast tab, the timeline ML model (format §8): the antibiotic and genus lists from
   <script id="trend-genera"> ({antibiotic: [genus, ...]}), the organism
   choose / genome toggle, the genome upload, the years slider, and the
   forecast chart from <script id="trend-data"> (the `ml_forecast` block).
   Expects: window.AMR (from main.js), Plotly (CDN)
   ============================================================ */

(function () {
  'use strict';

  const FEW_RESULTS = 30;   // a year with fewer lab results is drawn hollow and faded

  function readJson(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    try { return JSON.parse(el.textContent); } catch (e) { return null; }
  }

  /* ── Years slider ─────────────────────────────────────────── */
  const slider   = document.getElementById('yearsSlider');
  const yearsVal = document.getElementById('yearsVal');
  if (slider && yearsVal) {
    slider.addEventListener('input', function () { yearsVal.textContent = this.value; });
  }

  /* ── Antibiotic and genus lists ───────────────────────────── */
  const byDrug  = readJson('trend-genera') || {};
  const drugSel = document.getElementById('antibioticSelect');
  const genSel  = document.getElementById('genusSelect');
  const hint    = document.getElementById('genusHint');

  function fillGenera() {
    if (!genSel) return;
    const genera = (byDrug[drugSel.value] || []).slice().sort();
    const keep = genSel.dataset.selected || genSel.value;
    genSel.innerHTML = '';
    genSel.add(new Option(drugSel.value ? '-- Select Organism --' : '-- Choose an antibiotic first --', ''));
    genera.forEach(g => genSel.add(new Option(g, g, false, g === keep)));
    genSel.disabled = !genera.length;
    genSel.dataset.selected = '';
    if (hint) hint.textContent = drugSel.value && genera.length ? `${genera.length} genera have history for ${drugSel.value}` : '';
  }

  if (drugSel) {
    const drugs = Object.keys(byDrug).sort();
    if (!drugs.length) drugSel.options[0].text = 'Failed to load, check backend';
    drugs.forEach(d => drugSel.add(new Option(d.charAt(0).toUpperCase() + d.slice(1), d, false, d === drugSel.dataset.selected)));
    drugSel.addEventListener('change', fillGenera);
    fillGenera();
  }

  /* ── Organism: chosen, or identified from a genome ────────── */
  const fromInput  = document.getElementById('organismFrom');
  const choosePane = document.getElementById('choosePane');
  const genomePane = document.getElementById('genomePane');
  document.querySelectorAll('[data-organism-from]').forEach(btn => {
    btn.addEventListener('click', () => {
      const from = btn.dataset.organismFrom;
      if (fromInput) fromInput.value = from;
      document.querySelectorAll('[data-organism-from]').forEach(b => {
        b.classList.toggle('active', b === btn);
        b.setAttribute('aria-pressed', b === btn ? 'true' : 'false');
      });
      if (choosePane) choosePane.classList.toggle('d-none', from !== 'choose');
      if (genomePane) genomePane.classList.toggle('d-none', from !== 'genome');
      if (genSel) genSel.required = from === 'choose';
    });
  });

  /* ── Genome file: name, drag-and-drop ─────────────────────── */
  const fastaFile2  = document.getElementById('fastaFile2');
  const fileName2   = document.getElementById('fileName2');
  const fastaText2  = document.getElementById('fastaText2');
  const fastaError2 = document.getElementById('fastaError2');
  const clearGenomeError = () => { if (fastaError2) fastaError2.classList.add('d-none'); };

  if (fastaFile2) {
    fastaFile2.addEventListener('change', function () {
      if (fileName2) fileName2.textContent = this.files[0] ? this.files[0].name : '';
      clearGenomeError();
    });
  }
  if (fastaText2) fastaText2.addEventListener('input', clearGenomeError);

  const dropZone2 = document.getElementById('dropZone2');
  if (dropZone2) {
    dropZone2.addEventListener('dragover', e => { e.preventDefault(); dropZone2.classList.add('dragover'); });
    dropZone2.addEventListener('dragleave', () => dropZone2.classList.remove('dragover'));
    dropZone2.addEventListener('drop', e => {
      e.preventDefault();
      dropZone2.classList.remove('dragover');
      const file = e.dataTransfer.files[0];
      if (file && fastaFile2) {
        fastaFile2.files = e.dataTransfer.files;
        if (fileName2) fileName2.textContent = file.name;
        clearGenomeError();
      }
    });
  }

  /* ── A genome is needed when the organism comes from one ──── */
  const form = document.getElementById('timelineForm');
  if (form) {
    form.addEventListener('submit', function (e) {
      if (!fromInput || fromInput.value !== 'genome') return;
      const fileChosen = fastaFile2 && fastaFile2.files && fastaFile2.files.length > 0;
      const textTyped  = fastaText2 && fastaText2.value.trim().length > 0;
      if (fileChosen || textTyped) return;
      e.preventDefault();
      if (fastaError2) {
        fastaError2.classList.remove('d-none');
        fastaError2.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
      const textTabVisible = !document.getElementById('textTab2').classList.contains('d-none');
      if (textTabVisible && fastaText2) fastaText2.focus();
      else if (fastaFile2) fastaFile2.focus();
    });
  }

  /* ── The forecast chart ───────────────────────────────────── */
  const ml = readJson('trend-data');
  if (!ml || !document.getElementById('mlForecastChart') || typeof Plotly === 'undefined') return;
  const t = AMR.plotLayout();
  const hist = ml.history || [], fc = ml.forecast || [];
  const last = hist[hist.length - 1];
  // the forecast and its band start from the last observed year, so the lines join
  const fx = [last.year].concat(fc.map(f => f.year));
  const few = h => h.n < FEW_RESULTS;
  const traces = [
    { x: fx, y: [last.resistant_pct].concat(fc.map(f => f.lo)), mode: 'lines', line: { width: 0 },
      hoverinfo: 'skip', showlegend: false },
    { x: fx, y: [last.resistant_pct].concat(fc.map(f => f.hi)), mode: 'lines', line: { width: 0 },
      fill: 'tonexty', fillcolor: 'rgba(239,68,68,0.15)', name: '80% band', hoverinfo: 'skip' },
    { x: hist.map(h => h.year), y: hist.map(h => h.resistant_pct),
      customdata: hist.map(h => [h.n, few(h) ? `<br><i>few lab results (under ${FEW_RESULTS})</i>` : '']),
      name: 'Observed (lab results)', mode: 'lines+markers', line: { color: '#6366f1', width: 2.5 },
      marker: { size: 6, symbol: hist.map(h => (few(h) ? 'circle-open' : 'circle')), opacity: hist.map(h => (few(h) ? 0.5 : 1)) },
      hovertemplate: '%{x}: %{y:.1f}% resistant<br>%{customdata[0]} lab results%{customdata[1]}<extra></extra>' },
    { x: fx, y: [last.resistant_pct].concat(fc.map(f => f.resistant_pct)),
      customdata: [[last.resistant_pct, last.resistant_pct]].concat(fc.map(f => [f.lo, f.hi])),
      name: 'ML forecast', mode: 'lines+markers', line: { color: '#ef4444', width: 2.5, dash: 'dash' }, marker: { size: 6 },
      hovertemplate: '%{x}: %{y:.1f}% forecast<br>80% band %{customdata[0]:.1f} to %{customdata[1]:.1f}%<extra></extra>' },
  ];
  Plotly.newPlot('mlForecastChart', traces, {
    paper_bgcolor: t.paper_bgcolor, plot_bgcolor: t.plot_bgcolor,
    margin: { t: 30, b: 50, l: 50, r: 16 },
    legend: { font: { color: t.tickColor }, orientation: 'h', x: 0, y: 1.02, yanchor: 'bottom' },
    xaxis: { tickfont: { color: t.tickColor, size: 11 }, gridcolor: t.gridColor, linecolor: t.gridColor,
             title: { text: 'Year', font: { color: t.tickColor, size: 12 } }, dtick: 2, automargin: true },
    yaxis: { tickfont: { color: t.tickColor }, gridcolor: t.gridColor, range: [0, 105], ticksuffix: '%',
             title: { text: 'Resistant isolates', font: { color: t.tickColor, size: 12 } } },
    shapes: [{ type: 'line', xref: 'x', yref: 'paper', x0: last.year + 0.5, x1: last.year + 0.5, y0: 0, y1: 1,
               line: { color: t.gridColor, width: 1.5, dash: 'dot' } }],
    font: { family: t.fontFamily }, hovermode: 'closest',
  }, { responsive: true, displayModeBar: false });
})();

/* ── FASTA tab switching (called via onclick in the template) ───── */
window.switchTab2 = function (tab, btn) {
  document.querySelectorAll('#fastaTab2 .nav-link').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  document.getElementById('fileTab2').classList.toggle('d-none', tab !== 'file');
  document.getElementById('textTab2').classList.toggle('d-none', tab !== 'text');
};

/* ── The two tabs: ML trend forecast and what-if simulation ───── */
document.querySelectorAll('#timelineModes [data-mode]').forEach(btn => {
  btn.addEventListener('click', () => {
    const mode = btn.dataset.mode;
    document.querySelectorAll('#timelineModes [data-mode]').forEach(b => {
      b.classList.toggle('active', b === btn);
      b.setAttribute('aria-selected', b === btn ? 'true' : 'false');
    });
    document.querySelectorAll('[data-mode-pane]').forEach(p => p.classList.toggle('d-none', p.dataset.modePane !== mode));
    // a chart drawn while hidden gets its size now
    if (typeof Plotly !== 'undefined') {
      ['mlForecastChart', 'timelineChart', 'rlChart'].forEach(id => {
        const el = document.getElementById(id);
        if (el && el.data) Plotly.Plots.resize(el);
      });
    }
  });
});

/* ── The simulation form's FASTA tabs (onclick in the template) ── */
window.switchTab3 = function (tab, btn) {
  document.querySelectorAll('#fastaTab3 .nav-link').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  document.getElementById('fileTab3').classList.toggle('d-none', tab !== 'file');
  document.getElementById('textTab3').classList.toggle('d-none', tab !== 'text');
};

/* ── Load sample genome ───────────────────────────────────────── */
window.loadSample3 = function () {
  const textarea = document.querySelector('#textTab3 textarea');
  if (textarea) {
    textarea.value = `>sample_Ecoli_genome
ATGAAACGCATTAGCACCACCATTACCACCACCATCACCATTACCACAGGTAACGGTGCGGGCTGACGCGTACAGGAAACACAGAAAAAAGCCCGCACCTGACAGTGCGGGCTTTTTTTTTCGACCAAAGGTAACGAGGTAACAACCATGCGAGTGTTGAAGTTCGGCGGTACATCAGTGGCAAATGCAGAACGTTTTCTGCGCGTTGTTACGCGCATTTTCTGATATTCGATTCGCATCATTTTCGGTCGGGTATCGCGGCGTTTGCTAAAAAACGTCAGCGTTTGCAGTTTTCGCTGAAACAGATGCGTATTTCGGTTTATCTCAAAAGTTCGTTTAGTAACAACGATGCGTAAAGCAGCATTAACGAAACAGTTTCAACGTTTGGCTGAAACGCAGTTTAAAGCTCAACGCAACAGTTTGCAAACGCAGCGCAATTTAAACAAGCGTTTGCAGAAACG`;
  }
  const errBox = document.getElementById('fastaError3');
  if (errBox) errBox.classList.add('d-none');
  const textBtn = document.querySelectorAll('#fastaTab3 .nav-link')[1];
  if (textBtn) switchTab3('text', textBtn);
};

/* ── Toggle data table ────────────────────────────────────────── */
window.toggleTable = function () {
  const tbl = document.getElementById('timelineTable');
  const ch  = document.getElementById('tableChevron');
  if (!tbl) return;
  const hidden = tbl.classList.contains('d-none');
  tbl.classList.toggle('d-none', !hidden);
  if (ch) ch.className = hidden ? 'bi bi-chevron-up' : 'bi bi-chevron-down';
};


/* ── What-if simulation (not a trained model) and the RL panel ─── */
(function () {
  'use strict';

  /* ── Weeks slider ─────────────────────────────────────────── */
  const slider   = document.getElementById('weeksSlider');
  const weeksVal = document.getElementById('weeksVal');
  if (slider && weeksVal) {
    slider.addEventListener('input', function () {
      weeksVal.textContent = this.value;
      this.setAttribute('aria-valuenow', this.value);
    });
  }

  /* ── File name display ────────────────────────────────────── */
  const fastaFile3 = document.getElementById('fastaFile3');
  const fileName3  = document.getElementById('fileName3');
  if (fastaFile3 && fileName3) {
    fastaFile3.addEventListener('change', function () {
      fileName3.textContent = this.files[0] ? this.files[0].name : '';
    });
  }

  /* ── Drag-and-drop ────────────────────────────────────────── */
  const dropZone3 = document.getElementById('dropZone3');
  if (dropZone3) {
    dropZone3.addEventListener('dragover', e => {
      e.preventDefault();
      dropZone3.classList.add('dragover');
    });
    dropZone3.addEventListener('dragleave', () => {
      dropZone3.classList.remove('dragover');
    });
    dropZone3.addEventListener('drop', e => {
      e.preventDefault();
      dropZone3.classList.remove('dragover');
      const file = e.dataTransfer.files[0];
      if (file && fastaFile3) {
        fastaFile3.files = e.dataTransfer.files;
        if (fileName3) fileName3.textContent = file.name;
        const errBox = document.getElementById('fastaError3');
        if (errBox) errBox.classList.add('d-none');
      }
    });
  }

  /* ── Require a FASTA file or pasted sequence ──────────────── */
  const timelineForm = document.getElementById('simulationForm');
  const fastaText2   = document.querySelector('#textTab3 textarea');
  const fastaError3  = document.getElementById('fastaError3');

  function hasGenomeInput() {
    const fileChosen = fastaFile3 && fastaFile3.files && fastaFile3.files.length > 0;
    const textTyped  = fastaText2 && fastaText2.value.trim().length > 0;
    return fileChosen || textTyped;
  }

  function clearGenomeError() {
    if (fastaError3) fastaError3.classList.add('d-none');
  }

  if (timelineForm) {
    timelineForm.addEventListener('submit', function (e) {
      if (hasGenomeInput()) return;
      e.preventDefault();
      if (fastaError3) {
        fastaError3.classList.remove('d-none');
        fastaError3.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
      const textTabVisible = !document.getElementById('textTab3').classList.contains('d-none');
      if (textTabVisible && fastaText2) fastaText2.focus();
      else if (fastaFile3) fastaFile3.focus();
    });
  }
  if (fastaFile3) fastaFile3.addEventListener('change', clearGenomeError);
  if (fastaText2) fastaText2.addEventListener('input', clearGenomeError);

  /* ── Timeline chart ───────────────────────────────────────── */
  function renderTimelineChart(tlData, failWeek) {
    if (!tlData || !tlData.length) return;

    const weeks        = tlData.map(d => d.week);
    const narrow       = window.innerWidth < 576;
    const resistant    = tlData.map(d => d.resistant_fraction);
    const susceptible  = tlData.map(d => d.susceptible_fraction);
    const intermediate = tlData.map(d => d.intermediate_fraction);

    const traces = [
      {
        name: 'Resistant', x: weeks, y: resistant,
        mode: 'lines+markers',
        line: { color: '#ef4444', width: 3 },
        marker: { size: 6 },
        fill: 'tozeroy', fillcolor: 'rgba(239,68,68,0.1)',
        hovertemplate: 'Week %{x}<br>Resistant: %{y:.1f}%<extra></extra>',
      },
      {
        name: 'Intermediate', x: weeks, y: intermediate,
        mode: 'lines',
        line: { color: '#f59e0b', width: 2, dash: 'dot' },
        hovertemplate: 'Week %{x}<br>Intermediate: %{y:.1f}%<extra></extra>',
      },
      {
        name: 'Susceptible', x: weeks, y: susceptible,
        mode: 'lines+markers',
        line: { color: '#22c55e', width: 3 },
        marker: { size: 6 },
        hovertemplate: 'Week %{x}<br>Susceptible: %{y:.1f}%<extra></extra>',
      },
    ];

    const shapes = [{
      type: 'line',
      x0: weeks[0], x1: weeks[weeks.length - 1], y0: 50, y1: 50,
      line: { color: 'rgba(239,68,68,0.5)', width: 1.5, dash: 'dash' },
      xref: 'x', yref: 'y',
    }];

    if (failWeek !== null && failWeek !== undefined) {
      shapes.push({
        type: 'line',
        x0: failWeek, x1: failWeek, y0: 0, y1: 100,
        line: { color: 'rgba(239,68,68,0.7)', width: 2, dash: 'dash' },
        xref: 'x', yref: 'y',
      });
    }

    const t = AMR.plotLayout();

    Plotly.newPlot('timelineChart', traces, {
      paper_bgcolor: t.paper_bgcolor,
      plot_bgcolor:  t.plot_bgcolor,
      margin: { t: 30, b: 50, l: 50, r: 16 },
      legend: {
        font: { color: t.tickColor },
        orientation: 'h', x: 0, y: 1.02, yanchor: 'bottom',
      },
      xaxis: {
        tickfont: { color: t.tickColor, size: 11 },
        gridcolor: t.gridColor,
        linecolor: t.gridColor,
        title: { text: 'Week', font: { color: t.tickColor, size: 12 } },
        dtick: narrow && weeks.length > 13 ? 2 : 1,
        automargin: true,
      },
      yaxis: {
        tickfont: { color: t.tickColor },
        gridcolor: t.gridColor,
        range: [0, 105],
        ticksuffix: '%',
        title: { text: 'Population %', font: { color: t.tickColor, size: 12 } },
      },
      shapes: shapes,
      annotations: [{
        x: weeks[Math.floor(weeks.length / 2)],
        y: 53,
        text: narrow ? '50% failure' : '50% — Treatment Failure Threshold',
        font: { color: 'rgba(239,68,68,0.8)', size: 10 },
        showarrow: false,
      }],
      font: { family: t.fontFamily },
      hovermode: 'x unified',
    }, { responsive: true, displayModeBar: false });
  }

  /* ── RL panel (format §4): policies against each other ──────
     Data from <script id="rl-data">. Week w's value is the resistant share
     of the drug given in week w at the end of that week
     (resistant_fraction[drug][w]); first-failure weeks are the data's own. */
  const DRUG_COLOURS = ['#6366f1', '#f59e0b', '#10b981', '#ec4899', '#0ea5e9', '#a855f7'];
  const POLICY_COLOURS = ['#7c3aed', '#ef4444', '#0ea5e9', '#f59e0b', '#10b981', '#64748b'];

  function rlLayout(t, narrow, n, extra) {
    return Object.assign({
      paper_bgcolor: t.paper_bgcolor, plot_bgcolor: t.plot_bgcolor,
      margin: { t: 10, b: 50, l: 50, r: 16 },
      legend: { font: { color: t.tickColor, size: 11 }, orientation: 'h', x: 0, y: 1.02, yanchor: 'bottom' },
      xaxis: { tickfont: { color: t.tickColor, size: 11 }, gridcolor: t.gridColor, linecolor: t.gridColor,
               title: { text: 'Week', font: { color: t.tickColor, size: 12 } },
               dtick: narrow && n > 13 ? 2 : 1, automargin: true },
      yaxis: { tickfont: { color: t.tickColor }, gridcolor: t.gridColor, range: [0, 105], ticksuffix: '%',
               title: { text: 'Resistant %', font: { color: t.tickColor, size: 12 } } },
      shapes: [{ type: 'line', xref: 'paper', x0: 0, x1: 1, y0: 50, y1: 50,
                 line: { color: 'rgba(239,68,68,0.5)', width: 1.5, dash: 'dash' } }],
      font: { family: t.fontFamily },
      hovermode: 'x unified',
    }, extra || {});
  }

  function givenResistance(p) {
    /* resistance of the drug given in week w, at the end of week w (the lines) */
    return p.policy.map((drug, i) => (p.resistant_fraction[drug] || [])[i + 1]);
  }

  function startResistance(p) {
    /* at the start of week w: a week fails on this (format §4, answer 4),
       as failure_week counts it, so a failed week follows the line crossing 50 */
    return p.policy.map((drug, i) => (p.resistant_fraction[drug] || [])[i]);
  }

  function renderRl(rl) {
    if (!rl || !rl.policies || !rl.policies.length || !document.getElementById('rlChart')) return;
    const t = AMR.plotLayout();
    const narrow = window.innerWidth < 576;
    const n = rl.n_weeks || rl.policies[0].policy.length;
    const weeks = Array.from({ length: n }, (_, i) => i + 1);
    const drugColour = d => DRUG_COLOURS[Math.max(0, rl.drugs.indexOf(d)) % DRUG_COLOURS.length];

    /* 1. One line per policy: how resistant the drug it gave was */
    const traces = rl.policies.map((p, i) => ({
      name: p.label + (p.name === rl.best ? ' (best)' : ''),
      x: weeks, y: givenResistance(p), customdata: p.policy,
      mode: 'lines+markers',
      line: { color: POLICY_COLOURS[i % POLICY_COLOURS.length], width: p.name === rl.best ? 3.5 : 2,
              dash: p.name === 'rl' || p.name === rl.best ? 'solid' : 'dot' },
      marker: { size: p.name === rl.best ? 7 : 5 },
      hovertemplate: '%{customdata}: %{y:.1f}%<extra>' + p.label + '</extra>',
    }));
    Plotly.newPlot('rlChart', traces, rlLayout(t, narrow, n), { responsive: true, displayModeBar: false });

    /* 2. The chosen policy: the drug given each week, and every drug's resistance */
    const select = document.getElementById('rlPolicySelect');
    function showPolicy(i) {
      const p = rl.policies[i];
      const chips = document.getElementById('rlChips');
      if (chips) {
        chips.innerHTML = '';
        const given = givenResistance(p);
        const start = startResistance(p);
        p.policy.forEach((drug, w) => {
          const chip = document.createElement('span');
          chip.className = 'rl-chip' + (start[w] >= 50 ? ' rl-chip-failed' : '');
          chip.style.borderLeftColor = drugColour(drug);
          chip.title = `Week ${w + 1}: ${drug}, ${start[w] !== undefined ? start[w].toFixed(1) + '% resistant at the start' : ''}`
            + (given[w] !== undefined ? `, ${given[w].toFixed(1)}% at the end` : '');
          const wk = document.createElement('span');
          wk.className = 'rl-chip-week';
          wk.textContent = 'W' + (w + 1);
          const name = document.createElement('span');
          name.textContent = drug.length > 8 ? drug.slice(0, 7) + '.' : drug;
          chip.appendChild(wk);
          chip.appendChild(name);
          chips.appendChild(chip);
        });
      }
      const all = Array.from({ length: n + 1 }, (_, k) => k);
      const perDrug = rl.drugs.map(d => ({
        name: d, x: all, y: p.resistant_fraction[d] || [], mode: 'lines',
        line: { color: drugColour(d), width: 2.5 },
        hovertemplate: d + ': %{y:.1f}%<extra></extra>',
      }));
      Plotly.react('rlDrugChart', perDrug,
        rlLayout(t, narrow, n, { xaxis: Object.assign(rlLayout(t, narrow, n).xaxis, { range: [0, n] }) }),
        { responsive: true, displayModeBar: false });
    }
    if (select) {
      select.addEventListener('change', () => showPolicy(parseInt(select.value, 10)));
      showPolicy(parseInt(select.value, 10) || 0);
    }
  }

  const rlEl = document.getElementById('rl-data');
  if (rlEl) {
    try { renderRl(JSON.parse(rlEl.textContent)); } catch (_) {}
  }

  /* ── Dynamic bar widths (gene contribution bars) ─────────── */
  document.querySelectorAll('.prob-bar-fill[data-prob]').forEach(function (el) {
    el.style.width = parseFloat(el.dataset.prob).toFixed(1) + '%';
  });

  /* Auto-init from data islands */
  const tlEl   = document.getElementById('timeline-chart-data');
  const fwEl   = document.getElementById('timeline-fail-week');
  if (tlEl) {
    try {
      const tlData   = JSON.parse(tlEl.textContent);
      const failWeek = fwEl ? JSON.parse(fwEl.textContent) : null;
      renderTimelineChart(tlData, failWeek);
    } catch (_) {}
  }

})();

