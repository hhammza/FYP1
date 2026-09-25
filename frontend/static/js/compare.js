/* ============================================================
   AMRPredict — Model Comparison page (/compare)
   Expects: window.AMR (main.js), AMRReport (report-charts.js), Plotly,
            #report-data JSON embedded by compare.html
   ============================================================ */
(function () {
  'use strict';

  const report = AMRReport.readData('report-data');
  if (!report || !report.shipped || !report.training_profiles) return;
  const { config, palette, layout, pct, legendName } = AMRReport;

  const tp = report.training_profiles;
  const lg = report.shipped.lightgbm, km = report.shipped.kmer;
  const run = id => report.runs.find(r => r.id === id);

  /* The training sets worth comparing. Colour marks deployed vs experiment. */
  const SETS = [
    { key: 'deployed_kmer', label: 'Deployed K-mer RF', prof: km.train_profile, deployed: true },
    { key: 'deployed_lgbm', label: 'Deployed LightGBM', prof: lg.train_profile, deployed: true },
    { key: 'LC_50k', label: 'LC_50k (50k sample)', prof: tp.LC_50k },
    { key: 'LC_200k', label: 'LC_200k (200k sample)', prof: tp.LC_200k },
    { key: 'A6_lab_only', label: 'A6 (lab labels only)', prof: tp.A6_lab_only },
    { key: 'A3b_lgbm_same_sample', label: 'A3 to A5 (400k sample)', prof: tp.A3b_lgbm_same_sample },
    { key: 'A12_species_holdout', label: 'A12 (no Klebsiella)', prof: tp.A12_species_holdout },
    { key: report.best_run, label: `${report.best_run} (all data)`, prof: tp[report.best_run] },
  ].filter(s => s.prof);

  /* ── Training set size ─────────────────────────────────────── */
  function renderSizeChart() {
    const p = palette();
    const kinds = [
      { deployed: true, name: 'Deployed', color: p.c4 },
      { deployed: false, name: 'Experiment', color: p.c1 },
    ];
    const order = SETS.map(s => s.label);
    const traces = kinds.map(k => {
      const sets = SETS.filter(s => !!s.deployed === k.deployed);
      return {
        type: 'bar', orientation: 'h', name: legendName(k.name),
        x: sets.map(s => s.prof.rows), y: sets.map(s => s.label),
        marker: { color: k.color },
        text: sets.map(s => s.prof.rows.toLocaleString()), textposition: 'outside', cliponaxis: false,
        textfont: { color: p.text2, size: 11 },
        customdata: sets.map(s => [s.prof.genomes.toLocaleString(), s.prof.genera]),
        hovertemplate: '<b>%{y}</b><br>%{x:,} rows<br>%{customdata[0]} genomes'
                     + '<br>%{customdata[1]} genera<extra></extra>',
      };
    });
    Plotly.react('sizeChart', traces, layout({
      barmode: 'overlay', bargap: 0.3,
      xaxis: { type: 'log', range: [3, 6.55], title: { text: 'Training rows (log scale)' },
               tickvals: [1e3, 1e4, 1e5, 1e6], ticktext: ['1k', '10k', '100k', '1M'] },
      yaxis: { categoryorder: 'array', categoryarray: order, tickfont: { size: 11, color: AMR.plotLayout().tickColor } },
      margin: { t: 10, r: 70, b: 90, l: 170 },
      legend: { orientation: 'h', x: 0, xanchor: 'left', y: -0.22, font: { color: p.text2, size: 11 } },
    }), config);
  }

  /* ── Reported vs new-genome AUC ────────────────────────────── */
  function renderClaimChart() {
    const p = palette();
    const models = [
      { label: 'Deployed LightGBM', claimed: lg.claimed_auc, real: lg.results[1].auc_roc },
      { label: 'Deployed K-mer RF', claimed: km.claimed_auc, real: km.results[1].auc_roc },
      ...['A3_logistic', 'A4_random_forest', 'A5_xgboost', 'A5b_catboost', report.best_run]
        .map(run).filter(Boolean)
        .map(r => ({ label: r.id, claimed: r.auc_roc, real: r.auc_roc })),
    ];
    const order = models.map(m => m.label);
    const connectors = {
      type: 'scatter', mode: 'lines', showlegend: false, hoverinfo: 'skip',
      x: models.flatMap(m => [m.claimed, m.real, null]),
      y: models.flatMap(m => [m.label, m.label, null]),
      line: { color: p.other, width: 2 },
    };
    const dots = (name, key, color, symbol) => ({
      type: 'scatter', mode: 'markers', name: legendName(name),
      x: models.map(m => m[key]), y: order,
      marker: { color, size: 12, symbol, line: { color: p.card, width: 2 } },
      hovertemplate: `<b>%{y}</b><br>${name}: %{x:.3f}<extra></extra>`,
    });
    Plotly.react('claimChart', [
      connectors,
      dots('AUC as reported', 'claimed', p.c2, 'diamond'),
      dots('AUC on genomes never seen', 'real', p.c1, 'circle'),
    ], layout({
      xaxis: { range: [0.6, 1.0], title: { text: 'AUC-ROC' } },
      yaxis: { categoryorder: 'array', categoryarray: order.slice().reverse(),
               tickfont: { family: "'JetBrains Mono',monospace", size: 11, color: AMR.plotLayout().tickColor } },
      margin: { t: 10, r: 16, b: 90, l: 150 },
      legend: { orientation: 'h', x: 0, xanchor: 'left', y: -0.22, font: { color: p.text2, size: 11 } },
      hovermode: 'closest',
    }), config);
  }

  /* ── Genus mix heatmap ─────────────────────────────────────── */
  function renderGenusChart() {
    const p = palette();
    const cols = [
      { label: 'All data', prof: tp.full_data },
      { label: `${report.best_run}`, prof: tp[report.best_run] },
      { label: 'A6 lab only', prof: tp.A6_lab_only },
      { label: 'A12 no Klebsiella', prof: tp.A12_species_holdout },
      { label: 'Deployed LightGBM', prof: lg.train_profile },
      { label: 'Deployed K-mer RF', prof: km.train_profile },
    ].filter(c => c.prof);
    const share = (prof, g) => (prof.genus_rows[g] || 0) / prof.rows;

    /* Genera holding at least 1% of any training set, ordered by the full data */
    const genera = new Set();
    cols.forEach(c => Object.keys(c.prof.genus_rows).forEach(g => {
      if (g !== 'Other' && share(c.prof, g) >= 0.01) genera.add(g);
    }));
    const rows = [...genera].sort((a, b) => share(tp.full_data, b) - share(tp.full_data, a));
    const z = rows.map(g => cols.map(c => share(c.prof, g)));
    z.push(cols.map(c => 1 - rows.reduce((s, g) => s + share(c.prof, g), 0)));
    const yLabels = rows.concat(['All other genera']);

    /* Sequential: one hue, light to dark (dark mode: dark to light) */
    const scale = p.dark ? [[0, '#1c2b40'], [1, '#a5b4fc']] : [[0, '#f5f5ff'], [1, '#3730a3']];
    const label = v => (v === 0 ? '0' : v < 0.005 ? '<1%' : Math.round(100 * v) + '%');
    const inkFor = v => {
      const strong = v > 0.35;
      return p.dark ? (strong ? '#0f172a' : p.text) : (strong ? '#ffffff' : p.text);
    };
    const annotations = [];
    z.forEach((row, i) => row.forEach((v, j) => annotations.push({
      x: cols[j].label, y: yLabels[i], text: label(v), showarrow: false,
      font: { size: 11, color: v === 0 ? p.danger : inkFor(v), family: "'JetBrains Mono',monospace" },
    })));
    Plotly.react('genusChart', [{
      type: 'heatmap', x: cols.map(c => c.label), y: yLabels, z,
      colorscale: scale, zmin: 0, zmax: 0.7, xgap: 2, ygap: 2, showscale: false,
      hovertemplate: '<b>%{y}</b> in %{x}<br>%{z:.1%} of training rows<extra></extra>',
    }], layout({
      xaxis: { side: 'top', tickfont: { size: 11, color: AMR.plotLayout().tickColor }, showgrid: false },
      yaxis: { autorange: 'reversed', tickfont: { size: 11, color: AMR.plotLayout().tickColor }, showgrid: false },
      margin: { t: 40, r: 10, b: 10, l: 120 },
      annotations,
    }), config);
  }

  /* ── Label mix ─────────────────────────────────────────────── */
  function renderLabelChart() {
    const p = palette();
    const sets = [
      { label: 'All data', prof: tp.full_data },
      { label: report.best_run, prof: tp[report.best_run] },
      { label: 'A6 lab only', prof: tp.A6_lab_only },
      { label: 'Deployed LightGBM', prof: lg.train_profile },
      { label: 'Deployed K-mer RF', prof: km.train_profile },
    ].filter(s => s.prof);
    const series = [
      { key: 'prevalence', name: 'Resistant rows', color: p.c1 },
      { key: 'lab_share', name: 'Lab-confirmed labels', color: p.c2 },
      { key: 'mic_share', name: 'Rows with an MIC value', color: p.c3 },
    ];
    Plotly.react('labelChart', series.map(s => ({
      type: 'bar', name: legendName(s.name),
      x: sets.map(d => d.label), y: sets.map(d => (d.prof[s.key] === undefined ? null : d.prof[s.key])),
      marker: { color: s.color },
      text: sets.map(d => (d.prof[s.key] === undefined ? 'n/a' : pct(d.prof[s.key]))),
      textposition: 'outside', cliponaxis: false, textfont: { color: p.text2, size: 10.5 },
      hovertemplate: `<b>%{x}</b><br>${s.name}: %{y:.1%}<extra></extra>`,
    })), layout({
      barmode: 'group', bargap: 0.3, bargroupgap: 0.1,
      yaxis: { tickformat: '.0%', range: [0, 1.12], title: { text: 'Share of training rows' } },
      margin: { t: 16, r: 16, b: 80, l: 60 },
      legend: { orientation: 'h', x: 0, xanchor: 'left', y: -0.2, font: { color: p.text2, size: 11 } },
    }), config);
  }

  AMRReport.draw(function renderAll() {
    renderSizeChart();
    renderClaimChart();
    renderGenusChart();
    renderLabelChart();
  });
})();
