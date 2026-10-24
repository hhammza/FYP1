/* The charts of /genes (genes.js in the Flask frontend). */
import type { Data } from 'plotly.js-dist-min';
import type { Figure, PlotTheme } from '../../components/Plot';
import { legendName, palette, reportLayout } from '../../lib/report';
import type { GeneReport } from './types';

/** 'BETA-LACTAM' -> 'Beta-Lactam', as genes.js titled AMRFinderPlus classes. */
export const geneTitle = (s: string | undefined | null) =>
  String(s || '').toLowerCase().replace(/(^|[/\s-])\w/g, m => m.toUpperCase());

/** A long combined class wraps onto two lines at a '/' instead of being clipped. */
export function wrapLabel(label: string): string {
  if (label.length <= 22) return label;
  const cut = label.lastIndexOf('/', 22);
  return cut > 0 ? label.slice(0, cut + 1) + '<br>' + label.slice(cut + 1) : label;
}

/* Colour follows the kind of element, never its rank */
const KINDS = { gene: { label: 'Acquired gene', color: 'c1' }, point_mutation: { label: 'Point mutation', color: 'c2' } } as const;

/** The most common genes and mutations. */
export function topFigure(r: GeneReport, t: PlotTheme): Figure {
  const p = palette();
  const rows = r.top_genes;
  const traces = Object.entries(KINDS).map(([kind, k]): Data => {
    const sub = rows.filter(x => x.type === kind);
    return {
      type: 'bar', orientation: 'h', name: legendName(k.label),
      x: sub.map(x => 100 * x.share), y: sub.map(x => x.gene),
      marker: { color: p[k.color], line: { width: 0 } },
      customdata: sub.map(x => [x.name || '', geneTitle(x.class), geneTitle(x.subclass), x.genomes]),
      hovertemplate: '<b>%{y}</b><br>%{customdata[0]}<br>%{customdata[1]} · %{customdata[2]}<br>%{customdata[3]:,} genomes (%{x:.1f}%)<extra></extra>',
    } as Data;
  }).filter(tr => (tr as { x: unknown[] }).x.length);
  return {
    data: traces,
    layout: reportLayout(t, {
      barmode: 'relative', bargap: 0.35,
      margin: { t: 10, r: 16, b: 70, l: 110 },
      xaxis: { title: { text: 'Genomes carrying it' }, ticksuffix: '%', rangemode: 'tozero' },
      // most common at the top
      yaxis: { categoryorder: 'array', categoryarray: rows.map(x => x.gene).reverse(), automargin: true, gridcolor: 'rgba(0,0,0,0)' },
      showlegend: traces.length > 1,
    }),
  };
}

/** How many genes each genome carries. */
export function perGenomeFigure(r: GeneReport, t: PlotTheme): Figure {
  const p = palette();
  const rows = r.genes_per_genome;
  return {
    data: [{
      type: 'bar', x: rows.map(x => (x.capped ? x.genes + '+' : String(x.genes))), y: rows.map(x => x.genomes),
      marker: { color: p.c1, line: { width: 0 } },
      hovertemplate: '%{x} genes: %{y:,} genomes<extra></extra>',
    } as Data],
    layout: reportLayout(t, {
      bargap: 0.25, showlegend: false,
      xaxis: { title: { text: 'Resistance genes and mutations in the genome' }, type: 'category' },
      yaxis: { title: { text: 'Genomes' }, rangemode: 'tozero' },
    }),
  };
}

/** Genomes with a gene for each drug class (the 14 largest). */
export function classFigure(r: GeneReport, t: PlotTheme): Figure {
  const p = palette();
  const rows = r.classes.slice(0, 14);
  return {
    data: [{
      type: 'bar', orientation: 'h',
      x: rows.map(x => 100 * x.share), y: rows.map(x => wrapLabel(geneTitle(x.class))),
      marker: { color: p.c1, line: { width: 0 } },
      customdata: rows.map(x => [x.genomes, x.symbols]),
      hovertemplate: '<b>%{y}</b><br>%{customdata[0]:,} genomes (%{x:.1f}%)<br>%{customdata[1]} different genes or mutations<extra></extra>',
    } as Data],
    layout: reportLayout(t, {
      bargap: 0.35, showlegend: false,
      margin: { t: 10, r: 16, b: 48, l: 10 },
      xaxis: { title: { text: 'Genomes with a gene for this class' }, ticksuffix: '%', rangemode: 'tozero' },
      yaxis: { autorange: 'reversed', automargin: true, gridcolor: 'rgba(0,0,0,0)' },
    }),
  };
}

/** Genus by gene, the share of genomes carrying it (one hue, light to dark). */
export function heatFigure(r: GeneReport, t: PlotTheme): Figure {
  const p = palette();
  const h = r.heatmap;
  return {
    data: [{
      type: 'heatmap', x: h.genes, y: h.genera, z: h.share.map(row => row.map(v => 100 * v)),
      colorscale: [[0, p.card], [1, p.c1]], zmin: 0, zmax: 100, xgap: 2, ygap: 2,
      colorbar: { ticksuffix: '%', thickness: 10, outlinewidth: 0, tickfont: { color: p.text2, size: 11 } },
      hovertemplate: '<b>%{y}</b> · %{x}<br>%{z:.1f}% of genomes<extra></extra>',
    } as Data],
    layout: reportLayout(t, {
      margin: { t: 10, r: 16, b: 110, l: 110 },
      xaxis: { tickangle: -40, gridcolor: 'rgba(0,0,0,0)' },
      yaxis: { autorange: 'reversed', gridcolor: 'rgba(0,0,0,0)', tickfont: { color: p.text2, size: 12 } },
    }),
  };
}
