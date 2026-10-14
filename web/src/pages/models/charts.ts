/* The charts of /models (models.js in the Flask frontend), each a figure
   built from the report for the current theme. */
import type { Data } from 'plotly.js-dist-min';
import type { Figure, PlotTheme } from '../../components/Plot';
import { fmt, legendName, palette, pct, reportLayout, shownGenomeRuns, type ModelReport, type Run } from '../../lib/report';

const NARROW = () => window.innerWidth < 576;

/* Colour follows the group, never the rank */
const GROUPS: Record<string, { label: string; color: 'c1' | 'c2' | 'c3' | 'c4' | 'c5' | 'other' }> = {
  baseline: { label: 'Best model (A2, A9)', color: 'c1' },
  algorithm: { label: 'Algorithm comparison', color: 'c2' },
  protocol: { label: 'Split and encoding checks', color: 'c3' },
  shipped: { label: 'Deployed models (new genomes)', color: 'c4' },
  special: { label: 'Special cases', color: 'c5' },
  other: { label: 'Ablations and learning curve', color: 'other' },
};
const groupOf = (run: Run) => (run.group && GROUPS[run.group] ? run.group : 'other');

/** The /predict model's name, from the report (the old RandomForest has none). */
export const kmerLabel = (r: ModelReport) => 'Deployed ' + (r.shipped?.kmer?.short_name || 'K-mer RF');

const bestRun = (r: ModelReport) => r.runs.find(x => x.id === r.best_run);

/** AUC on genomes seen in training vs never seen. */
export function seenFigure(report: ModelReport, t: PlotTheme): Figure {
  const p = palette();
  const sh = report.shipped!;
  const best = bestRun(report)!;
  const names = ['Deployed LightGBM', kmerLabel(report), `Best experiment (${best.id})`];
  const seen = [sh.lightgbm.results[0], sh.kmer.results[0]];
  const unseen = [sh.lightgbm.results[1], sh.kmer.results[1],
                  { auc_roc: best.auc_roc, auc_ci: best.auc_ci, rows: best.test_rows ?? 0 }];
  const trace = (rows: { auc_roc: number; auc_ci: [number, number]; rows: number }[], name: string, color: string): Data => ({
    type: 'bar', name: legendName(name), x: names.slice(0, rows.length), y: rows.map(r => r.auc_roc),
    base: 0, marker: { color, line: { width: 0 } },
    error_y: { type: 'data', symmetric: false, color: p.text2, thickness: 1.2, width: 4,
               array: rows.map(r => r.auc_ci[1] - r.auc_roc), arrayminus: rows.map(r => r.auc_roc - r.auc_ci[0]) },
    text: rows.map(r => fmt(r.auc_roc)), textposition: 'outside',
    textfont: { color: p.text, size: 12 }, cliponaxis: false,
    customdata: rows.map(r => r.rows.toLocaleString()),
    hovertemplate: `<b>%{x}</b><br>${name}<br>AUC %{y:.3f}<br>%{customdata} rows<extra></extra>`,
  } as Data);
  return {
    data: [trace(seen, 'Genomes seen in training', p.c2), trace(unseen, 'Genomes never seen', p.c1)],
    layout: reportLayout(t, {
      barmode: 'group', bargap: 0.35, bargroupgap: 0.08,
      yaxis: { range: [0.5, 1.02], title: { text: 'AUC-ROC (0.5 = guessing)' } },
      margin: { t: 16, r: 16, b: 70, l: 60 },
      legend: { orientation: 'h', x: 0, xanchor: 'left', y: -0.2, font: { color: p.text2, size: 11 } },
    }),
  };
}

/** Every run's AUC with its interval, the deployed models too. */
export function aucFigure(report: ModelReport, t: PlotTheme): Figure {
  const p = palette();
  const sh = report.shipped;
  const rows = report.runs.map(r => ({
    label: r.id, auc: r.auc_roc, ci: r.auc_ci, group: groupOf(r),
    detail: `${r.model}, ${r.split} split, ${r.rows.toLocaleString()} rows`,
  }));
  if (sh) {
    rows.push({ label: 'Deployed LightGBM', auc: sh.lightgbm.results[1].auc_roc, ci: sh.lightgbm.results[1].auc_ci,
                group: 'shipped', detail: 'backend model, tested on genomes it never saw' });
    rows.push({ label: kmerLabel(report), auc: sh.kmer.results[1].auc_roc, ci: sh.kmer.results[1].auc_ci,
                group: 'shipped', detail: 'backend model, tested on genomes it never saw' });
  }
  rows.sort((a, b) => a.auc - b.auc);
  const traces = Object.keys(GROUPS).map((key): Data => {
    const g = rows.filter(r => r.group === key);
    return {
      type: 'scatter', mode: 'markers', name: legendName(GROUPS[key].label),
      x: g.map(r => r.auc), y: g.map(r => r.label),
      marker: { color: p[GROUPS[key].color], size: 10, line: { color: p.card, width: 2 } },
      error_x: { type: 'data', symmetric: false, color: p[GROUPS[key].color], thickness: 2, width: 0,
                 array: g.map(r => r.ci[1] - r.auc), arrayminus: g.map(r => r.auc - r.ci[0]) },
      customdata: g.map(r => [r.ci[0], r.ci[1], r.detail]),
      hovertemplate: '<b>%{y}</b><br>AUC %{x:.3f} [%{customdata[0]:.3f} to %{customdata[1]:.3f}]<br>%{customdata[2]}<extra></extra>',
    } as Data;
  }).filter(tr => (tr as { x: unknown[] }).x.length);
  return {
    data: traces,
    layout: reportLayout(t, {
      xaxis: { range: [0.5, 1.0], title: { text: NARROW() ? 'AUC-ROC (0.5 = guessing)' : 'AUC-ROC on held-out genomes (0.5 = guessing)' } },
      yaxis: { categoryorder: 'array', categoryarray: rows.map(r => r.label),
               tickfont: { family: "'JetBrains Mono',monospace", size: 11, color: t.tickColor } },
      margin: { t: 10, r: 16, b: 90, l: 170 },
      legend: { orientation: 'h', x: 0, xanchor: 'left', y: -60 / (140 + 24 * rows.length) - 0.06, font: { color: p.text2, size: 11 } },
      hovermode: 'closest',
    }),
  };
}

/** ROC curves of the main runs and the deployed forecaster. */
export function rocFigure(report: ModelReport, t: PlotTheme): Figure {
  const p = palette();
  const auc = (id: string) => report.runs.find(r => r.id === id)?.auc_roc ?? NaN;
  const curves: { name: string; color: string; width?: number; dash?: string; pts: { fpr: number[]; tpr: number[] }; auc: number }[] = [
    { id: 'A2_oof_grouped', name: 'A2 LightGBM (best)', color: p.c1, width: 2.5 },
    { id: 'A3_logistic', name: 'A3 logistic regression', color: p.c2 },
    { id: 'A6_lab_only', name: 'A6 lab labels only', color: p.c5 },
    { id: 'A12_species_holdout', name: 'A12 unseen genus', color: p.c3 },
    { id: 'A_ablation_drug_only', name: 'Drug name only', color: p.other, dash: 'dash' },
  ].filter(c => report.roc[c.id]).map(c => ({ ...c, pts: report.roc[c.id], auc: auc(c.id) }));
  const deployed = report.shipped?.lightgbm.results[1];
  if (deployed?.roc) curves.push({ name: 'Deployed LightGBM', color: p.c4, pts: deployed.roc, auc: deployed.auc_roc });
  const traces: Data[] = curves.map(c => ({
    type: 'scatter', mode: 'lines', name: legendName(`${c.name} (${fmt(c.auc)})`),
    x: c.pts.fpr, y: c.pts.tpr,
    line: { color: c.color, width: c.width || 2, dash: (c.dash || 'solid') as 'solid', shape: 'spline' },
    hovertemplate: `<b>${c.name}</b><br>False positive rate %{x:.2f}<br>True positive rate %{y:.2f}<extra></extra>`,
  }));
  traces.push({ type: 'scatter', mode: 'lines', x: [0, 1], y: [0, 1], showlegend: false, hoverinfo: 'skip',
                line: { color: p.other, width: 1, dash: 'dot' } });
  return {
    data: traces,
    layout: reportLayout(t, {
      xaxis: { range: [0, 1], title: { text: 'False positive rate' } },
      yaxis: { range: [0, 1.01], title: { text: 'True positive rate' } },
      legend: { orientation: 'h', x: 0, xanchor: 'left', y: -0.2, font: { color: p.text2, size: 11 } },
      margin: { t: 10, r: 16, b: 110, l: 56 },
    }),
  };
}

/** LightGBM AUC as the training data grows. */
export function learningFigure(report: ModelReport, t: PlotTheme): Figure {
  const p = palette();
  const full = bestRun(report);
  const pts = report.runs.filter(r => r.id.startsWith('LC_')).concat(full ? [full] : []).sort((a, b) => a.rows - b.rows);
  const lo = Math.floor((Math.min(...pts.map(r => r.auc_ci[0])) - 0.005) * 100) / 100;
  const hi = Math.ceil((Math.max(...pts.map(r => r.auc_ci[1])) + 0.005) * 100) / 100;
  return {
    data: [{
      type: 'scatter', mode: 'lines+markers', name: 'LightGBM',
      x: pts.map(r => r.rows), y: pts.map(r => r.auc_roc),
      line: { color: p.c1, width: 2 },
      marker: { color: p.c1, size: 9, line: { color: p.card, width: 2 } },
      error_y: { type: 'data', symmetric: false, color: p.c1, thickness: 1.2, width: 4,
                 array: pts.map(r => r.auc_ci[1] - r.auc_roc), arrayminus: pts.map(r => r.auc_roc - r.auc_ci[0]) },
      customdata: pts.map(r => r.id),
      hovertemplate: '<b>%{customdata}</b><br>%{x:,} rows<br>AUC %{y:.3f}<extra></extra>',
    } as Data],
    layout: reportLayout(t, {
      xaxis: { type: 'log', title: { text: 'Rows used (log scale)' }, tickvals: pts.map(r => r.rows),
               ticktext: pts.map(r => (r.rows >= 1e6 ? (r.rows / 1e6).toFixed(1) + 'M' : Math.round(r.rows / 1e3) + 'k')) },
      // the range fits the points and their intervals, with a little room
      yaxis: { range: [lo, hi], title: { text: 'AUC-ROC' } },
      showlegend: false,
    }),
  };
}

/** VME against ME for every run. */
export function errorFigure(report: ModelReport, t: PlotTheme): Figure {
  const p = palette();
  const sh = report.shipped;
  const labelled = new Set(['A2_oof_grouped', 'A9_threshold_f1', 'A6_lab_only', 'A12_species_holdout', 'A3_logistic']);
  const pts = report.runs.map(r => ({ label: r.id, me: r.major_error, vme: r.very_major_error, thr: r.threshold, group: groupOf(r) }));
  if (sh) {
    pts.push({ label: 'Deployed LightGBM', me: sh.lightgbm.results[1].major_error, vme: sh.lightgbm.results[1].very_major_error,
               thr: sh.lightgbm.threshold ?? 0.40, group: 'shipped' });
    pts.push({ label: kmerLabel(report), me: sh.kmer.results[1].major_error, vme: sh.kmer.results[1].very_major_error,
               thr: sh.kmer.threshold ?? 0.50, group: 'shipped' });
    labelled.add('Deployed LightGBM');
    labelled.add(kmerLabel(report));
  }
  const keys = Object.keys(GROUPS);
  const traces = keys.map((key): Data => {
    const g = pts.filter(r => r.group === key);
    return {
      type: 'scatter', mode: NARROW() ? 'markers' : 'markers+text', name: legendName(GROUPS[key].label),
      x: g.map(r => r.me), y: g.map(r => r.vme),
      text: g.map(r => (labelled.has(r.label) ? r.label.replace(/_.*/, '').replace('Deployed ', '') : '')),
      textposition: 'top center', textfont: { color: p.text2, size: 10.5 },
      marker: { color: p[GROUPS[key].color], size: 11, line: { color: p.card, width: 2 } },
      customdata: g.map(r => [r.label, r.thr]),
      hovertemplate: '<b>%{customdata[0]}</b><br>VME %{y:.1%} (missed resistance)<br>ME %{x:.1%} (false alarm)<br>Threshold %{customdata[1]:.2f}<extra></extra>',
      legendrank: keys.indexOf(key) + 1,
    } as Data;
  }).filter(tr => (tr as { x: unknown[] }).x.length).reverse();   // the best model drawn last, on top
  return {
    data: traces,
    layout: reportLayout(t, {
      xaxis: { title: { text: 'ME: susceptible isolates called resistant' }, tickformat: '.0%', rangemode: 'tozero' },
      yaxis: { title: { text: 'VME: resistant isolates missed' }, tickformat: '.0%', rangemode: 'tozero' },
      margin: { t: 16, r: 16, b: 90, l: 64 },
      legend: { orientation: 'h', x: 0, xanchor: 'left', y: -0.24, font: { color: p.text2, size: 11 } },
      hovermode: 'closest',
    }),
  };
}

/** The best run's ten best and ten worst antibiotics. */
export function drugFigure(report: ModelReport, t: PlotTheme): Figure {
  const p = palette();
  const best = report.best.per_antibiotic_best, worst = report.best.per_antibiotic_worst;
  const rows = worst.slice().concat(best.slice().reverse());
  const labels = rows.map(r => r.antibiotic);
  return {
    data: [{
      type: 'bar', orientation: 'h', x: rows.map(r => r.auc_roc), y: labels, base: 0,
      marker: { color: rows.map((_, i) => (i < worst.length ? p.other : p.c1)) },
      text: rows.map(r => fmt(r.auc_roc)), textposition: 'outside', cliponaxis: false,
      textfont: { color: p.text2, size: 10.5 },
      customdata: rows.map(r => [r.rows.toLocaleString(), pct(r.prevalence)]),
      hovertemplate: '<b>%{y}</b><br>AUC %{x:.3f}<br>%{customdata[0]} test rows<br>%{customdata[1]} resistant<extra></extra>',
    } as Data],
    layout: reportLayout(t, {
      xaxis: { range: [0.5, 1.04], title: { text: 'AUC-ROC' } },
      yaxis: { categoryorder: 'array', categoryarray: labels, tickfont: { size: 11, color: t.tickColor } },
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
    }),
  };
}

/** Section 5: the genome runs' lab AUC, coloured by kind of split, the served run a star. */
export function genomeFigure(report: ModelReport, t: PlotTheme): Figure {
  const { runs } = shownGenomeRuns(report.genome_runs);
  const servedId = report.shipped?.kmer?.run_id;
  const p = palette();
  const colours = [p.c1, p.c2, p.c3, p.c4, p.c5];
  // one colour per kind of split, not per held-out genus or lineage cut
  const kind = (s: string | undefined) => String(s || 'other').split(' ')[0];
  const splits = [...new Set(runs.map(r => kind(r.split)))];
  const rows = runs.slice().sort((a, b) => (a.auc_roc_lab as number) - (b.auc_roc_lab as number));
  const traces = splits.map((split, i): Data => {
    const g = rows.filter(r => kind(r.split) === split);
    const cis = g.map(r => r.auc_roc_lab_ci);
    const colour = colours[i % colours.length];
    return {
      type: 'scatter', mode: 'markers', name: legendName(split),
      x: g.map(r => r.auc_roc_lab as number), y: g.map(r => r.id),
      marker: { color: colour, size: 10, symbol: g.map(r => (r.id === servedId ? 'star' : 'circle')), line: { color: p.card, width: 2 } },
      error_x: cis.every(c => c)
        ? { type: 'data', symmetric: false, color: colour, thickness: 2, width: 0,
            array: g.map(r => r.auc_roc_lab_ci![1] - (r.auc_roc_lab as number)),
            arrayminus: g.map(r => (r.auc_roc_lab as number) - r.auc_roc_lab_ci![0]) }
        : { visible: false },
      customdata: g.map(r => [(r.n_lab || 0).toLocaleString(), (r.features || '') + ', ' + (r.split || ''), r.description || '']),
      hovertemplate: '<b>%{y}</b><br>Lab AUC %{x:.3f} on %{customdata[0]} lab rows<br>%{customdata[1]}<br>%{customdata[2]}<extra></extra>',
    } as Data;
  });
  const narrow = NARROW();
  const low = Math.min(0.5, Math.floor((Math.min(...rows.map(r => r.auc_roc_lab as number)) - 0.03) * 20) / 20);
  return {
    data: traces,
    layout: reportLayout(t, {
      xaxis: { range: [low, 1.0], title: { text: narrow ? 'Lab AUC (0.5 = guessing)' : 'AUC on lab-tested results (0.5 = guessing)' } },
      yaxis: { categoryorder: 'array', categoryarray: rows.map(r => r.id),
               tickfont: { family: "'JetBrains Mono',monospace", size: narrow ? 9 : 11, color: t.tickColor } },
      margin: { t: 10, r: 16, b: 80, l: narrow ? 130 : 200 },
      legend: { orientation: 'h', x: 0, xanchor: 'left', y: -50 / (140 + 22 * rows.length) - 0.06, font: { color: p.text2, size: 11 } },
      hovermode: 'closest',
    }),
  };
}
