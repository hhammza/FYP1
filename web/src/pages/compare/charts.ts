/* The charts of /compare (compare.js in the Flask frontend). */
import type { Annotations, Data } from 'plotly.js-dist-min';
import type { Figure, PlotTheme } from '../../components/Plot';
import { legendName, palette, pct, reportLayout, type ModelReport } from '../../lib/report';

export interface Profile {
  rows: number;
  genomes: number;
  genera: number;
  taxa?: number;
  antibiotics?: number;
  prevalence: number;
  lab_share: number;
  mic_share?: number;
  shared_genomes?: number;
  genus_rows: Record<string, number>;
}

export type Profiles = Record<string, Profile | undefined>;

const profiles = (r: ModelReport) => (r.training_profiles || {}) as Profiles;
const kmLabel = (r: ModelReport) => 'Deployed ' + (r.shipped!.kmer.short_name || 'K-mer RF');
const lgProfile = (r: ModelReport) => r.shipped!.lightgbm.train_profile as Profile;
const kmProfile = (r: ModelReport) => r.shipped!.kmer.train_profile as Profile;

/** The training sets worth comparing; colour marks deployed vs experiment. */
function sets(r: ModelReport) {
  const tp = profiles(r);
  return [
    { label: kmLabel(r), prof: kmProfile(r), deployed: true },
    { label: 'Deployed LightGBM', prof: lgProfile(r), deployed: true },
    { label: 'LC_50k (50k sample)', prof: tp.LC_50k, deployed: false },
    { label: 'LC_200k (200k sample)', prof: tp.LC_200k, deployed: false },
    { label: 'A6 (lab labels only)', prof: tp.A6_lab_only, deployed: false },
    { label: 'A3 to A5 (400k sample)', prof: tp.A3b_lgbm_same_sample, deployed: false },
    { label: 'A12 (no Klebsiella)', prof: tp.A12_species_holdout, deployed: false },
    { label: `${r.best_run} (all data)`, prof: tp[r.best_run], deployed: false },
  ].filter((s): s is { label: string; prof: Profile; deployed: boolean } => !!s.prof);
}

/** Rows each model learned from, on a log scale. */
export function sizeFigure(r: ModelReport, t: PlotTheme): Figure {
  const p = palette();
  const all = sets(r);
  const traces = [{ deployed: true, name: 'Deployed', color: p.c4 }, { deployed: false, name: 'Experiment', color: p.c1 }].map((k): Data => {
    const ss = all.filter(s => s.deployed === k.deployed);
    return {
      type: 'bar', orientation: 'h', name: legendName(k.name),
      x: ss.map(s => s.prof.rows), y: ss.map(s => s.label),
      marker: { color: k.color },
      text: ss.map(s => s.prof.rows.toLocaleString()), textposition: 'outside', cliponaxis: false,
      textfont: { color: p.text2, size: 11 },
      customdata: ss.map(s => [s.prof.genomes.toLocaleString(), s.prof.genera]),
      hovertemplate: '<b>%{y}</b><br>%{x:,} rows<br>%{customdata[0]} genomes<br>%{customdata[1]} genera<extra></extra>',
    } as Data;
  });
  return {
    data: traces,
    layout: reportLayout(t, {
      barmode: 'overlay', bargap: 0.3,
      xaxis: { type: 'log', range: [3, 6.55], title: { text: 'Training rows (log scale)' },
               tickvals: [1e3, 1e4, 1e5, 1e6], ticktext: ['1k', '10k', '100k', '1M'] },
      yaxis: { categoryorder: 'array', categoryarray: all.map(s => s.label), tickfont: { size: 11, color: t.tickColor } },
      margin: { t: 10, r: 70, b: 90, l: 170 },
      legend: { orientation: 'h', x: 0, xanchor: 'left', y: -0.22, font: { color: p.text2, size: 11 } },
    }),
  };
}

/** The AUC each model was reported with against its AUC on new genomes. */
export function claimFigure(r: ModelReport, t: PlotTheme): Figure {
  const p = palette();
  const lg = r.shipped!.lightgbm, km = r.shipped!.kmer;
  const models = [
    // the claimed AUC as the report has it (Plotly reads a number written as text too)
    { label: 'Deployed LightGBM', claimed: lg.claimed_auc as number, real: lg.results[1].auc_roc },
    { label: kmLabel(r), claimed: km.claimed_auc as number, real: km.results[1].auc_roc },
    ...['A3_logistic', 'A4_random_forest', 'A5_xgboost', 'A5b_catboost', r.best_run]
      .map(id => r.runs.find(x => x.id === id)).filter(x => !!x)
      .map(x => ({ label: x!.id, claimed: x!.auc_roc, real: x!.auc_roc })),
  ];
  const order = models.map(m => m.label);
  const dots = (name: string, key: 'claimed' | 'real', color: string, symbol: string): Data => ({
    type: 'scatter', mode: 'markers', name: legendName(name),
    x: models.map(m => m[key]), y: order,
    marker: { color, size: 12, symbol, line: { color: p.card, width: 2 } },
    hovertemplate: `<b>%{y}</b><br>${name}: %{x:.3f}<extra></extra>`,
  } as Data);
  return {
    data: [
      { type: 'scatter', mode: 'lines', showlegend: false, hoverinfo: 'skip',
        x: models.flatMap(m => [m.claimed, m.real, null]), y: models.flatMap(m => [m.label, m.label, null]),
        line: { color: p.other, width: 2 } } as Data,
      dots('AUC as reported', 'claimed', p.c2, 'diamond'),
      dots('AUC on genomes never seen', 'real', p.c1, 'circle'),
    ],
    layout: reportLayout(t, {
      xaxis: { range: [0.6, 1.0], title: { text: 'AUC-ROC' } },
      yaxis: { categoryorder: 'array', categoryarray: order.slice().reverse(),
               tickfont: { family: "'JetBrains Mono',monospace", size: 11, color: t.tickColor } },
      margin: { t: 10, r: 16, b: 90, l: 150 },
      legend: { orientation: 'h', x: 0, xanchor: 'left', y: -0.22, font: { color: p.text2, size: 11 } },
      hovermode: 'closest',
    }),
  };
}

/** Share of training rows per genus, a heatmap. */
export function genusFigure(r: ModelReport, t: PlotTheme): Figure {
  const p = palette();
  const tp = profiles(r);
  const cols = [
    { label: 'All data', prof: tp.full_data },
    { label: `${r.best_run}`, prof: tp[r.best_run] },
    { label: 'A6 lab only', prof: tp.A6_lab_only },
    { label: 'A12 no Klebsiella', prof: tp.A12_species_holdout },
    { label: 'Deployed LightGBM', prof: lgProfile(r) },
    { label: kmLabel(r), prof: kmProfile(r) },
  ].filter((c): c is { label: string; prof: Profile } => !!c.prof);
  const share = (prof: Profile, g: string) => (prof.genus_rows[g] || 0) / prof.rows;
  // genera holding at least 1% of any training set, ordered by the full data
  const genera = new Set<string>();
  cols.forEach(c => Object.keys(c.prof.genus_rows).forEach(g => {
    if (g !== 'Other' && share(c.prof, g) >= 0.01) genera.add(g);
  }));
  const full = tp.full_data!;
  const rows = [...genera].sort((a, b) => share(full, b) - share(full, a));
  const z = rows.map(g => cols.map(c => share(c.prof, g)));
  z.push(cols.map(c => 1 - rows.reduce((s, g) => s + share(c.prof, g), 0)));
  const yLabels = rows.concat(['All other genera']);
  // sequential: one hue, light to dark (dark mode: dark to light)
  const scale: [number, string][] = p.dark ? [[0, '#1c2b40'], [1, '#a5b4fc']] : [[0, '#f5f5ff'], [1, '#3730a3']];
  const label = (v: number) => (v === 0 ? '0' : v < 0.005 ? '<1%' : Math.round(100 * v) + '%');
  const inkFor = (v: number) => {
    const strong = v > 0.35;
    return p.dark ? (strong ? '#0f172a' : p.text) : (strong ? '#ffffff' : p.text);
  };
  const annotations: Partial<Annotations>[] = [];
  z.forEach((row, i) => row.forEach((v, j) => annotations.push({
    x: cols[j].label, y: yLabels[i], text: label(v), showarrow: false,
    font: { size: 11, color: v === 0 ? p.danger : inkFor(v), family: "'JetBrains Mono',monospace" },
  })));
  return {
    data: [{
      type: 'heatmap', x: cols.map(c => c.label), y: yLabels, z,
      colorscale: scale, zmin: 0, zmax: 0.7, xgap: 2, ygap: 2, showscale: false,
      hovertemplate: '<b>%{y}</b> in %{x}<br>%{z:.1%} of training rows<extra></extra>',
    } as Data],
    layout: reportLayout(t, {
      xaxis: { side: 'top', tickfont: { size: 11, color: t.tickColor }, showgrid: false },
      yaxis: { autorange: 'reversed', tickfont: { size: 11, color: t.tickColor }, showgrid: false },
      margin: { t: 40, r: 10, b: 10, l: 120 },
      annotations,
    }),
  };
}

/** Resistant share, lab-confirmed share and MIC share of each training set. */
export function labelFigure(r: ModelReport, t: PlotTheme): Figure {
  const p = palette();
  const tp = profiles(r);
  const ss = [
    { label: 'All data', prof: tp.full_data },
    { label: r.best_run, prof: tp[r.best_run] },
    { label: 'A6 lab only', prof: tp.A6_lab_only },
    { label: 'Deployed LightGBM', prof: lgProfile(r) },
    { label: kmLabel(r), prof: kmProfile(r) },
  ].filter((s): s is { label: string; prof: Profile } => !!s.prof);
  const series = [
    { key: 'prevalence', name: 'Resistant rows', color: p.c1 },
    { key: 'lab_share', name: 'Lab-confirmed labels', color: p.c2 },
    { key: 'mic_share', name: 'Rows with an MIC value', color: p.c3 },
  ] as const;
  return {
    data: series.map((s): Data => ({
      type: 'bar', name: legendName(s.name),
      x: ss.map(d => d.label), y: ss.map(d => (d.prof[s.key] === undefined ? null : d.prof[s.key]!)),
      marker: { color: s.color },
      text: ss.map(d => (d.prof[s.key] === undefined ? 'n/a' : pct(d.prof[s.key]!))),
      textposition: 'outside', cliponaxis: false, textfont: { color: p.text2, size: 10.5 },
      hovertemplate: `<b>%{x}</b><br>${s.name}: %{y:.1%}<extra></extra>`,
    } as Data)),
    layout: reportLayout(t, {
      barmode: 'group', bargap: 0.3, bargroupgap: 0.1,
      yaxis: { tickformat: '.0%', range: [0, 1.12], title: { text: 'Share of training rows' } },
      margin: { t: 16, r: 16, b: 80, l: 60 },
      legend: { orientation: 'h', x: 0, xanchor: 'left', y: -0.2, font: { color: p.text2, size: 11 } },
    }),
  };
}
