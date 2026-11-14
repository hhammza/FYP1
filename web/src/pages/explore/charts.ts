/* Plotly figures for the dashboard (/explore). */
import type { Data, Layout } from 'plotly.js-dist-min';
import type { Figure, PlotTheme } from '../../components/Plot';
import type { CountryRow, SummaryRow } from './types';

/* Sequential, one hue light to dark, for resistance %: the legend bins 0-20 ... 80-100 */
export const BINS = ['#fde6d8', '#f8b08a', '#ec7a45', '#c84a1c', '#8a2c0d'];
export const NO_DATA = '#c9ccd1';
/* Categorical slots, fixed order (identity: resistance types, split series) */
export const SERIES = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948'];

const pct = (v: number | null) => (v === null || v === undefined ? 'n/a' : `${v.toFixed(1)}%`);
const LOW = 0.35;   // opacity of a low-sample mark

function base(t: PlotTheme, extra: Partial<Layout> = {}): Partial<Layout> {
  return {
    paper_bgcolor: t.paper_bgcolor, plot_bgcolor: t.plot_bgcolor,
    font: { family: t.fontFamily, color: t.tickColor, size: 12 }, margin: { l: 10, r: 10, t: 10, b: 30 },
    hoverlabel: { font: { family: t.fontFamily } }, ...extra,
  };
}

const geo = (t: PlotTheme): Partial<Layout['geo']> => ({
  showframe: false, showcoastlines: false, showland: true, landcolor: NO_DATA, showcountries: true,
  countrycolor: t.lineColor, projection: { type: 'natural earth' }, bgcolor: 'rgba(0,0,0,0)',
});

const stepped = BINS.flatMap((c, i) => [[i / 5, c], [(i + 1) / 5, c]] as [number, string][]);

function tooltip(c: CountryRow): string {
  const types = c.top_types.length
    ? c.top_types.map(t => `${t.type}: ${pct(t.resistant_pct)} (n=${t.n.toLocaleString()}${t.low_sample ? ', low sample' : ''})`).join('<br>')
    : 'none with data';
  return `<b>${c.country}</b><br>Resistant: ${pct(c.resistant_pct)} of ${c.n.toLocaleString()} isolates tested`
    + (c.low_sample ? ' <i>(low sample)</i>' : '')
    + `<br><br><b>Top resistance types</b><br>${types}<br><br>Top resistant organism: ${c.top_organism || 'n/a'}<extra></extra>`;
}

/** Point 10 (rate) and point 6: resistance % per country, binned 0-20 ... 80-100. */
export function rateMap(rows: CountryRow[], t: PlotTheme): Figure {
  const withData = rows.filter(r => r.resistant_pct !== null);
  const trace = (sub: CountryRow[], low: boolean, legend: boolean): Data => ({
    type: 'choropleth', locationmode: 'ISO-3', locations: sub.map(r => r.iso3), z: sub.map(r => r.resistant_pct as number),
    zmin: 0, zmax: 100, colorscale: stepped, marker: { line: { color: t.lineColor, width: 0.5 }, opacity: low ? LOW : 1 },
    showscale: legend, customdata: sub.map(r => r.iso3), hovertemplate: sub.map(tooltip),
    colorbar: { title: { text: 'Resistant %' }, tickvals: [0, 20, 40, 60, 80, 100], thickness: 12, len: 0.75 },
  } as Data);
  return {
    data: [trace(withData.filter(r => !r.low_sample), false, true), trace(withData.filter(r => r.low_sample), true, false)],
    layout: base(t, { geo: geo(t), margin: { l: 0, r: 0, t: 0, b: 0 } }),
  };
}

/** Point 10 (dominant): which resistance type is highest in each country. */
export function dominantMap(rows: CountryRow[], types: string[], t: PlotTheme): Figure {
  const data: Data[] = types.map((type, i) => {
    const sub = rows.filter(r => r.dominant_type === type);
    return {
      type: 'choropleth', locationmode: 'ISO-3', locations: sub.map(r => r.iso3), z: sub.map(() => 1),
      colorscale: [[0, SERIES[i % SERIES.length]], [1, SERIES[i % SERIES.length]]], showscale: false, showlegend: true,
      name: type, marker: { line: { color: t.lineColor, width: 0.5 }, opacity: sub.map(r => (r.low_sample ? LOW : 1)) },
      customdata: sub.map(r => r.iso3), hovertemplate: sub.map(tooltip),
    } as unknown as Data;
  }).filter(d => (d as { locations: string[] }).locations.length);
  return { data, layout: base(t, { geo: geo(t), margin: { l: 0, r: 0, t: 0, b: 0 }, showlegend: true,
    legend: { orientation: 'h', y: -0.02, x: 0 } }) };
}

/** Points 7, 8 and 9: horizontal bars of resistance %, highest first, small samples faded. */
export function rateBars(rows: SummaryRow[], t: PlotTheme, label = (r: SummaryRow) => String(r.label || r.value)): Figure {
  const shown = [...rows].reverse();
  return {
    data: [{
      type: 'bar', orientation: 'h', y: shown.map(label), x: shown.map(r => r.resistant_pct ?? 0),
      marker: { color: shown.map(() => SERIES[0]), opacity: shown.map(r => (r.low_sample ? LOW : 1)) },
      text: shown.map(r => `${pct(r.resistant_pct)}  n=${r.n.toLocaleString()}`), textposition: 'outside', cliponaxis: false,
      customdata: shown.map(r => String(r.value)),
      hovertemplate: shown.map(r => `<b>${label(r)}</b><br>${pct(r.resistant_pct)} resistant<br>${r.r.toLocaleString()} of ${r.n.toLocaleString()} isolates`
        + (r.low_sample ? '<br><i>low sample</i>' : '') + '<extra></extra>'),
    } as Data],
    layout: base(t, {
      xaxis: { range: [0, 115], title: { text: 'Resistant %' }, gridcolor: t.gridColor, zeroline: false, tickvals: [0, 20, 40, 60, 80, 100] },
      yaxis: { automargin: true }, margin: { l: 10, r: 30, t: 10, b: 40 }, bargap: 0.25,
    }),
  };
}

/** Point 7 split: one bar series per split value (at most 4; the rest is folded away). */
export function splitBars(rows: SummaryRow[], t: PlotTheme, splitLabel: (s: string) => string = s => s): Figure {
  const bySplit = new Map<string, number>();
  for (const r of rows) bySplit.set(String(r.split), (bySplit.get(String(r.split)) || 0) + r.n);
  const series = [...bySplit.entries()].sort((a, b) => b[1] - a[1]).slice(0, 4).map(e => e[0]);
  const groups = [...new Set(rows.map(r => String(r.value)))];
  const data: Data[] = series.map((s, i) => {
    const mine = new Map(rows.filter(r => String(r.split) === s).map(r => [String(r.value), r]));
    const ys = [...groups].reverse();
    return {
      type: 'bar', orientation: 'h', name: splitLabel(s), y: ys, x: ys.map(g => mine.get(g)?.resistant_pct ?? null),
      marker: { color: SERIES[i], opacity: ys.map(g => (mine.get(g)?.low_sample ? LOW : 1)) },
      hovertemplate: ys.map(g => { const r = mine.get(g); return r ? `<b>${g}</b>, ${splitLabel(s)}<br>${pct(r.resistant_pct)} of ${r.n.toLocaleString()}<extra></extra>` : ''; }),
    } as Data;
  });
  return { data, layout: base(t, {
    barmode: 'group', xaxis: { range: [0, 105], title: { text: 'Resistant %' }, gridcolor: t.gridColor, tickvals: [0, 20, 40, 60, 80, 100] },
    yaxis: { automargin: true }, legend: { orientation: 'h', y: 1.06, x: 0 }, margin: { l: 10, r: 10, t: 30, b: 40 }, bargap: 0.2,
  }) };
}

/** Point 8: yearly resistance per drug (lines), small years hidden. */
export function trendLines(rows: SummaryRow[], t: PlotTheme, minN: number): Figure {
  const drugs = [...new Set(rows.map(r => String(r.split)))].slice(0, 8);
  const data: Data[] = drugs.map((d, i) => {
    // from 1990: earlier BV-BRC years are a handful of isolates, some with a mistyped year (1922)
    const pts = rows.filter(r => String(r.split) === d && r.n >= minN && Number(r.value) >= 1990).sort((a, b) => Number(a.value) - Number(b.value));
    return {
      type: 'scatter', mode: 'lines+markers', name: d, x: pts.map(p => Number(p.value)), y: pts.map(p => p.resistant_pct),
      line: { color: SERIES[i], width: 2 }, marker: { size: 8, color: SERIES[i] },
      hovertemplate: pts.map(p => `<b>${d}</b> ${p.value}<br>${pct(p.resistant_pct)} of ${p.n.toLocaleString()}<extra></extra>`),
    } as Data;
  });
  return { data, layout: base(t, {
    xaxis: { title: { text: 'Collection year' }, gridcolor: t.gridColor }, hovermode: 'closest',
    yaxis: { title: { text: 'Resistant %' }, range: [0, 100], gridcolor: t.gridColor },
    legend: { orientation: 'h', y: 1.1, x: 0 }, margin: { l: 50, r: 10, t: 30, b: 40 },
  }) };
}
