/* The timeline ML model's forecast on /timeline (format §8, Hamza's
   backend/ml_models/timeline_ml.py): the organism's observed yearly resistant
   share from BV-BRC lab results, and the model's next years with an 80% band. */
import { useCallback } from 'react';
import type { Data } from 'plotly.js-dist-min';
import Plot, { type Figure, type PlotTheme } from '../../components/Plot';
import { pyFixed } from '../../lib/metrics';
import type { MlForecast } from './types';

const OBSERVED = '#6366f1', FORECAST = '#ef4444', BAND = 'rgba(239,68,68,0.15)';

/** The baselines the model is measured against, in the order to show them. */
const BASELINES: [string, string][] = [['last_value', 'last year’s value'], ['linear_trend', 'a straight-line trend'],
                                        ['historical_mean', 'the average so far']];

export function forecastFigure(ml: MlForecast, t: PlotTheme): Figure {
  const last = ml.history[ml.history.length - 1];
  // the forecast and its band start from the last observed year, so the lines join
  const fx = [last.year, ...ml.forecast.map(f => f.year)];
  const traces: Data[] = [
    { type: 'scatter', mode: 'lines', x: fx, y: [last.resistant_pct, ...ml.forecast.map(f => f.lo)],
      line: { width: 0 }, hoverinfo: 'skip', showlegend: false },
    { type: 'scatter', mode: 'lines', name: '80% band', x: fx, y: [last.resistant_pct, ...ml.forecast.map(f => f.hi)],
      fill: 'tonexty', fillcolor: BAND, line: { width: 0 }, hoverinfo: 'skip', legendrank: 3 },
    { type: 'scatter', mode: 'lines+markers', name: 'Observed (lab results)', x: ml.history.map(h => h.year),
      y: ml.history.map(h => h.resistant_pct), customdata: ml.history.map(h => h.n),
      line: { color: OBSERVED, width: 2.5 }, marker: { size: 6 }, legendrank: 1,
      hovertemplate: '%{x}: %{y:.1f}% resistant<br>%{customdata} lab results<extra></extra>' },
    { type: 'scatter', mode: 'lines+markers', name: 'ML forecast', x: fx, y: [last.resistant_pct, ...ml.forecast.map(f => f.resistant_pct)],
      customdata: [[last.resistant_pct, last.resistant_pct], ...ml.forecast.map(f => [f.lo, f.hi])],
      line: { color: FORECAST, width: 2.5, dash: 'dash' }, marker: { size: 6 }, legendrank: 2,
      hovertemplate: '%{x}: %{y:.1f}% forecast<br>80% band %{customdata[0]:.1f} to %{customdata[1]:.1f}%<extra></extra>' },
  ];
  return {
    data: traces,
    layout: {
      paper_bgcolor: t.paper_bgcolor, plot_bgcolor: t.plot_bgcolor,
      margin: { t: 30, b: 50, l: 50, r: 16 },
      legend: { font: { color: t.tickColor }, orientation: 'h', x: 0, y: 1.02, yanchor: 'bottom' },
      xaxis: { tickfont: { color: t.tickColor, size: 11 }, gridcolor: t.gridColor, linecolor: t.gridColor,
               title: { text: 'Year', font: { color: t.tickColor, size: 12 } }, dtick: 2, automargin: true },
      yaxis: { tickfont: { color: t.tickColor }, gridcolor: t.gridColor, range: [0, 105], ticksuffix: '%',
               title: { text: 'Resistant isolates', font: { color: t.tickColor, size: 12 } } },
      shapes: [{ type: 'line', xref: 'x', yref: 'paper', x0: last.year + 0.5, x1: last.year + 0.5, y0: 0, y1: 1,
                 line: { color: t.gridColor, width: 1.5, dash: 'dot' } }],
      font: { family: t.fontFamily },
      hovermode: 'closest',
    },
  };
}

/** "13.98 pp, against 14.33 for last year's value, ..." from the held-out metrics. */
export function errorSentence(metrics: MlForecast['metrics']): string {
  const m = metrics?.model;
  if (!m) return '';
  const others = BASELINES.filter(([k]) => metrics?.[k]).map(([k, name]) => `${pyFixed(metrics![k].mae_pct, 2)} for ${name}`);
  return `On years it never saw, the model is off by ${pyFixed(m.mae_pct, 2)} percentage points on average`
    + (others.length ? `, against ${others.join(', ')}.` : '.');
}

interface Props {
  ml: MlForecast | null | undefined;
  antibiotic: string;
  /** the genus asked for, if any (else the genome's was tried) */
  genus?: string;
}

export default function MlForecastCard({ ml, antibiotic, genus }: Props) {
  const figure = useCallback((t: PlotTheme) => forecastFigure(ml!, t), [ml]);
  if (!ml || !ml.history?.length || !ml.forecast?.length) {
    return (
      <div className="alert alert-info-custom mb-4" role="status" id="mlForecastNone">
        <i className="bi bi-graph-up me-2"></i><strong>No ML forecast for this request.</strong>{' '}
        {genus
          ? `${genus} has too little yearly lab history for ${antibiotic}.`
          : 'Choose an organism above, or upload a complete genome so its genus can be identified.'}
        {' '}The simulation below still runs.
      </div>
    );
  }
  const last = ml.history[ml.history.length - 1];
  const end = ml.forecast[ml.forecast.length - 1];
  const first = ml.history[0];
  return (
    <div className="info-card mb-4" id="mlForecast">
      <div className="d-flex align-items-start flex-wrap gap-2 mb-1">
        <h6 className="card-section-title mb-0 me-auto"><i className="bi bi-graph-up-arrow text-accent me-2"></i>
          Resistance forecast: <em>{ml.organism}</em> and {ml.antibiotic}</h6>
        <span className="status-badge trained"><i className="bi bi-cpu"></i>{ml.label}</span>
      </div>
      <p className="small text-muted mb-2">
        The share of {ml.organism} isolates resistant to {ml.antibiotic} in BV-BRC laboratory results, year by year
        ({first.year} to {last.year}), and the ML model's forecast for the next {ml.forecast.length} years. The shaded
        band is an 80% interval from the model's errors on held-out years; it widens the further ahead it looks.
      </p>
      <Plot id="mlForecastChart" className="chart-350" figure={figure} />
      <div className="row g-2 text-center mt-2">
        <div className="col-6 col-md-4"><div className="stat-mini">
          <div className="stat-mini-value stat-mini-static">{pyFixed(last.resistant_pct, 1)}%</div>
          <div className="stat-mini-label">Observed in {last.year} ({last.n} lab results)</div>
        </div></div>
        <div className="col-6 col-md-4"><div className="stat-mini">
          <div className="stat-mini-value stat-mini-static text-rose2">{pyFixed(end.resistant_pct, 1)}%</div>
          <div className="stat-mini-label">Forecast for {end.year} (80%: {pyFixed(end.lo, 1)} to {pyFixed(end.hi, 1)})</div>
        </div></div>
        <div className="col-12 col-md-4"><div className="stat-mini">
          <div className="stat-mini-value stat-mini-static">{ml.history.length} years</div>
          <div className="stat-mini-label">of history the forecast rests on</div>
        </div></div>
      </div>
      {ml.metrics?.model && <p className="caption-text mt-2 mb-0">{errorSentence(ml.metrics)} Model run <code>{ml.model_run}</code>.</p>}
    </div>
  );
}
