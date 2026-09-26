/* ============================================================
   AMRPredict — Model Report page (/models)
   Expects: window.AMR (main.js), AMRReport (report-charts.js), Plotly,
            #report-data JSON embedded by models.html
   ============================================================ */
(function () {
  'use strict';

  const report = AMRReport.readData('report-data');
  if (!report) return;
  const { config, palette, layout, fmt, pct, legendName } = AMRReport;
  const shipped = report.shipped;

  /* Colour follows the group, never the rank */
  const GROUPS = {
    baseline:       { label: 'Best model (A2, A9)',        color: 'c1' },
    algorithm:      { label: 'Algorithm comparison',       color: 'c2' },
    protocol:       { label: 'Split and encoding checks',  color: 'c3' },
    shipped:        { label: 'Deployed models (new genomes)', color: 'c4' },
    special:        { label: 'Special cases',              color: 'c5' },
    other:          { label: 'Ablations and learning curve', color: 'other' },
  };
  const groupOf = run => (GROUPS[run.group] ? run.group : 'other');

  /* ── Genome split illustration ─────────────────────────────── */
  function renderGenomeDemos() {
    const N_GENOMES = 6, N_ROWS = 12;
    document.querySelectorAll('.genome-demo').forEach(el => {
      const random = el.dataset.mode === 'random';
      let seed = 7;
      const rand = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
      el.innerHTML = '';
      for (let gi = 0; gi < N_GENOMES; gi++) {
        const row = document.createElement('div');
        row.className = 'genome-row';
        row.innerHTML = `<span class="genome-label">genome ${gi + 1}</span>`;
        const groupedTest = gi === 1 || gi === 4;
        let train = 0, test = 0;
        for (let ri = 0; ri < N_ROWS; ri++) {
          const isTest = random ? rand() < 0.2 : groupedTest;
          isTest ? test++ : train++;
          const cell = document.createElement('span');
          cell.className = 'genome-cell ' + (isTest ? 'test' : 'train');
          row.appendChild(cell);
        }
        const tag = document.createElement('span');
        if (train && test) { tag.className = 'genome-tag leak'; tag.textContent = 'both sides'; }
        else { tag.className = 'genome-tag'; tag.textContent = test ? 'test only' : 'train only'; }
        row.appendChild(tag);
        el.appendChild(row);
      }
    });
  }

  /* ── Seen vs never-seen genomes ────────────────────────────── */
  function renderSeenChart() {
    if (!shipped || !document.getElementById('seenChart')) return;
    const p = palette();
    const best = report.runs.find(r => r.id === report.best_run);
    const names = ['Deployed LightGBM', 'Deployed K-mer RF', `Best experiment (${best.id})`];
    const seen = [shipped.lightgbm.results[0], shipped.kmer.results[0]];
    const unseen = [shipped.lightgbm.results[1], shipped.kmer.results[1],
                    { auc_roc: best.auc_roc, auc_ci: best.auc_ci, rows: best.test_rows }];
    const trace = (rows, name, color) => ({
      type: 'bar', name: legendName(name), x: names.slice(0, rows.length), y: rows.map(r => r.auc_roc),
      base: 0, marker: { color, line: { width: 0 } },
      error_y: { type: 'data', symmetric: false, color: p.text2, thickness: 1.2, width: 4,
                 array: rows.map(r => r.auc_ci[1] - r.auc_roc),
                 arrayminus: rows.map(r => r.auc_roc - r.auc_ci[0]) },
      text: rows.map(r => fmt(r.auc_roc)), textposition: 'outside',
      textfont: { color: p.text, size: 12 }, cliponaxis: false,
      customdata: rows.map(r => r.rows.toLocaleString()),
      hovertemplate: `<b>%{x}</b><br>${name}<br>AUC %{y:.3f}<br>%{customdata} rows<extra></extra>`,
    });
    Plotly.react('seenChart', [
      trace(seen, 'Genomes seen in training', p.c2),
      trace(unseen, 'Genomes never seen', p.c1),
    ], layout({
      barmode: 'group', bargap: 0.35, bargroupgap: 0.08,
      yaxis: { range: [0.5, 1.02], title: { text: 'AUC-ROC (0.5 = guessing)' } },
      margin: { t: 16, r: 16, b: 70, l: 60 },
      legend: { orientation: 'h', x: 0, xanchor: 'left', y: -0.2, font: { color: p.text2, size: 11 } },
    }), config);
  }

  /* ── AUC with CI, every run ────────────────────────────────── */
  function renderAucChart() {
    const p = palette();
    const rows = report.runs.map(r => ({
      label: r.id, auc: r.auc_roc, ci: r.auc_ci, group: groupOf(r),
      detail: `${r.model}, ${r.split} split, ${r.rows.toLocaleString()} rows`,
    }));
    if (shipped) {
      rows.push({ label: 'Deployed LightGBM', auc: shipped.lightgbm.results[1].auc_roc,
                  ci: shipped.lightgbm.results[1].auc_ci, group: 'shipped',
                  detail: 'backend model, tested on genomes it never saw' });
      rows.push({ label: 'Deployed K-mer RF', auc: shipped.kmer.results[1].auc_roc,
                  ci: shipped.kmer.results[1].auc_ci, group: 'shipped',
                  detail: 'backend model, tested on genomes it never saw' });
    }
    rows.sort((a, b) => a.auc - b.auc);
    const order = rows.map(r => r.label);

    const traces = Object.keys(GROUPS).map(key => {
      const g = rows.filter(r => r.group === key);
      return {
        type: 'scatter', mode: 'markers', name: legendName(GROUPS[key].label),
        x: g.map(r => r.auc), y: g.map(r => r.label),
        marker: { color: p[GROUPS[key].color], size: 10, line: { color: p.card, width: 2 } },
        error_x: { type: 'data', symmetric: false, color: p[GROUPS[key].color], thickness: 2, width: 0,
                   array: g.map(r => r.ci[1] - r.auc), arrayminus: g.map(r => r.auc - r.ci[0]) },
        customdata: g.map(r => [r.ci[0], r.ci[1], r.detail]),
        hovertemplate: '<b>%{y}</b><br>AUC %{x:.3f} [%{customdata[0]:.3f} to %{customdata[1]:.3f}]'
                     + '<br>%{customdata[2]}<extra></extra>',
      };
    }).filter(t => t.x.length);

    Plotly.react('aucChart', traces, layout({
      xaxis: { range: [0.5, 1.0], title: { text: 'AUC-ROC on held-out genomes (0.5 = guessing)' } },
      yaxis: { categoryorder: 'array', categoryarray: order, tickfont: { family: "'JetBrains Mono',monospace", size: 11, color: AMR.plotLayout().tickColor } },
      margin: { t: 10, r: 16, b: 90, l: 170 },
      legend: { orientation: 'h', x: 0, xanchor: 'left', y: -60 / (140 + 24 * rows.length) - 0.06, font: { color: p.text2, size: 11 } },
      hovermode: 'closest',
    }), config);
  }

  /* ── ROC curves ────────────────────────────────────────────── */
  function renderRocChart() {
    const p = palette();
    const auc = id => (report.runs.find(r => r.id === id) || {}).auc_roc;
    const curves = [
      { id: 'A2_oof_grouped', name: 'A2 LightGBM (best)', color: p.c1, width: 2.5 },
      { id: 'A3_logistic', name: 'A3 logistic regression', color: p.c2 },
      { id: 'A6_lab_only', name: 'A6 lab labels only', color: p.c5 },
      { id: 'A12_species_holdout', name: 'A12 unseen genus', color: p.c3 },
      { id: 'A_ablation_drug_only', name: 'Drug name only', color: p.other, dash: 'dash' },
    ].filter(c => report.roc[c.id]).map(c => ({ ...c, pts: report.roc[c.id], auc: auc(c.id) }));
    if (shipped) {
      const r = shipped.lightgbm.results[1];
      curves.push({ name: 'Deployed LightGBM', color: p.c4, pts: r.roc, auc: r.auc_roc });
    }
    const traces = curves.map(c => ({
      type: 'scatter', mode: 'lines', name: legendName(`${c.name} (${fmt(c.auc)})`),
      x: c.pts.fpr, y: c.pts.tpr,
      line: { color: c.color, width: c.width || 2, dash: c.dash || 'solid', shape: 'spline' },
      hovertemplate: `<b>${c.name}</b><br>False positive rate %{x:.2f}<br>True positive rate %{y:.2f}<extra></extra>`,
    }));
    traces.push({
      type: 'scatter', mode: 'lines', x: [0, 1], y: [0, 1], showlegend: false, hoverinfo: 'skip',
      line: { color: p.other, width: 1, dash: 'dot' },
    });
    Plotly.react('rocChart', traces, layout({
      xaxis: { range: [0, 1], title: { text: 'False positive rate' } },
      yaxis: { range: [0, 1.01], title: { text: 'True positive rate' } },
      legend: { orientation: 'h', x: 0, xanchor: 'left', y: -0.2, font: { color: p.text2, size: 11 } },
      margin: { t: 10, r: 16, b: 110, l: 56 },
    }), config);
  }

  /* ── Learning curve ────────────────────────────────────────── */
  function renderLearningChart() {
    const p = palette();
    const lc = report.runs.filter(r => r.id.startsWith('LC_'));
    const full = report.runs.find(r => r.id === report.best_run);
    const pts = lc.concat(full ? [full] : []).sort((a, b) => a.rows - b.rows);
    Plotly.react('learningChart', [{
      type: 'scatter', mode: 'lines+markers', name: 'LightGBM',
      x: pts.map(r => r.rows), y: pts.map(r => r.auc_roc),
      line: { color: p.c1, width: 2 },
      marker: { color: p.c1, size: 9, line: { color: p.card, width: 2 } },
      error_y: { type: 'data', symmetric: false, color: p.c1, thickness: 1.2, width: 4,
                 array: pts.map(r => r.auc_ci[1] - r.auc_roc), arrayminus: pts.map(r => r.auc_roc - r.auc_ci[0]) },
      customdata: pts.map(r => r.id),
      hovertemplate: '<b>%{customdata}</b><br>%{x:,} rows<br>AUC %{y:.3f}<extra></extra>',
    }], layout({
      xaxis: { type: 'log', title: { text: 'Rows used (log scale)' },
               tickvals: pts.map(r => r.rows), ticktext: pts.map(r => (r.rows >= 1e6 ? (r.rows / 1e6).toFixed(1) + 'M' : Math.round(r.rows / 1e3) + 'k')) },
      yaxis: { range: [0.78, 0.85], title: { text: 'AUC-ROC' } },
      showlegend: false,
    }), config);
  }

  /* ── VME vs ME trade-off ───────────────────────────────────── */
  function renderErrorChart() {
    const p = palette();
    const LABELLED = new Set(['A2_oof_grouped', 'A9_threshold_f1', 'A6_lab_only', 'A12_species_holdout', 'A3_logistic']);
    const pts = report.runs.map(r => ({ label: r.id, me: r.major_error, vme: r.very_major_error,
                                        thr: r.threshold, group: groupOf(r) }));
    if (shipped) {
      pts.push({ label: 'Deployed LightGBM', me: shipped.lightgbm.results[1].major_error,
                 vme: shipped.lightgbm.results[1].very_major_error, thr: shipped.lightgbm.threshold ?? 0.40, group: 'shipped' });
      pts.push({ label: 'Deployed K-mer RF', me: shipped.kmer.results[1].major_error,
                 vme: shipped.kmer.results[1].very_major_error, thr: shipped.kmer.threshold ?? 0.50, group: 'shipped' });
      LABELLED.add('Deployed LightGBM'); LABELLED.add('Deployed K-mer RF');
    }
    const traces = Object.keys(GROUPS).map(key => {
      const g = pts.filter(r => r.group === key);
      return {
        type: 'scatter', mode: 'markers+text', name: legendName(GROUPS[key].label),
        x: g.map(r => r.me), y: g.map(r => r.vme),
        text: g.map(r => (LABELLED.has(r.label) ? r.label.replace(/_.*/, '').replace('Deployed ', '') : '')),
        textposition: 'top center', textfont: { color: p.text2, size: 10.5 },
        marker: { color: p[GROUPS[key].color], size: 11, line: { color: p.card, width: 2 } },
        customdata: g.map(r => [r.label, r.thr]),
        hovertemplate: '<b>%{customdata[0]}</b><br>VME %{y:.1%} (missed resistance)'
                     + '<br>ME %{x:.1%} (false alarm)<br>Threshold %{customdata[1]:.2f}<extra></extra>',
        legendrank: Object.keys(GROUPS).indexOf(key) + 1,
      };
    }).filter(t => t.x.length).reverse();  /* best model drawn last, on top */
    Plotly.react('errorChart', traces, layout({
      xaxis: { title: { text: 'ME: susceptible isolates called resistant' }, tickformat: '.0%', rangemode: 'tozero' },
      yaxis: { title: { text: 'VME: resistant isolates missed' }, tickformat: '.0%', rangemode: 'tozero' },
      margin: { t: 16, r: 16, b: 90, l: 64 },
      legend: { orientation: 'h', x: 0, xanchor: 'left', y: -0.24, font: { color: p.text2, size: 11 } },
      hovermode: 'closest',
    }), config);
  }

  /* ── Per-antibiotic AUC for the best run ───────────────────── */
  function renderDrugChart() {
    const p = palette();
    const best = report.best.per_antibiotic_best, worst = report.best.per_antibiotic_worst;
    const rows = worst.slice().concat(best.slice().reverse());
    const labels = rows.map(r => r.antibiotic);
    Plotly.react('drugChart', [{
      type: 'bar', orientation: 'h', x: rows.map(r => r.auc_roc), y: labels, base: 0,
      marker: { color: rows.map((r, i) => (i < worst.length ? p.other : p.c1)) },
      text: rows.map(r => fmt(r.auc_roc)), textposition: 'outside', cliponaxis: false,
      textfont: { color: p.text2, size: 10.5 },
      customdata: rows.map(r => [r.rows.toLocaleString(), pct(r.prevalence)]),
      hovertemplate: '<b>%{y}</b><br>AUC %{x:.3f}<br>%{customdata[0]} test rows'
                   + '<br>%{customdata[1]} resistant<extra></extra>',
    }], layout({
      xaxis: { range: [0.5, 1.04], title: { text: 'AUC-ROC' } },
      yaxis: { categoryorder: 'array', categoryarray: labels, tickfont: { size: 11, color: AMR.plotLayout().tickColor } },
      margin: { t: 24, r: 36, b: 44, l: 190 },
      bargap: 0.25, showlegend: false,
      shapes: [{ type: 'line', xref: 'paper', x0: 0, x1: 1, yref: 'y', y0: worst.length - 0.5, y1: worst.length - 0.5,
                 line: { color: p.other, width: 1, dash: 'dot' } }],
      annotations: [
        { xref: 'paper', x: 1, xanchor: 'right', yref: 'y', y: rows.length - 0.5, yanchor: 'bottom',
          text: 'Best 10', showarrow: false, font: { size: 11, color: p.text2 } },
        { xref: 'paper', x: 1, xanchor: 'right', yref: 'y', y: worst.length - 0.5, yanchor: 'top',
          text: 'Worst 10', showarrow: false, font: { size: 11, color: p.text2 } },
      ],
    }), config);
  }

  function renderAll() {
    renderSeenChart();
    renderAucChart();
    renderRocChart();
    renderLearningChart();
    renderErrorChart();
    renderDrugChart();
  }

  renderGenomeDemos();
  AMRReport.draw(renderAll);
})();
