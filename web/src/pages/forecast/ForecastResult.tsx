/* One isolate's result on /forecast: the verdict, downloads, what the
   prediction was based on, drug details and the comparison chart. */
import { Fragment, useCallback, useRef } from 'react';
import type { Data } from 'plotly.js-dist-min';
import ExportBar from '../../components/ExportBar';
import { pyFixed, pyFloat } from '../../lib/metrics';
import Plot, { type Figure, type PlotElement, type PlotTheme } from '../../components/Plot';
import type { EvidenceInput, ForecastInputs, ForecastResult as Result } from './types';

const RED = 'rgba(239,68,68,0.82)', AMBER = 'rgba(245,158,11,0.82)', GREEN = 'rgba(34,197,94,0.82)';

/** A bar is red exactly when the model would call that drug Resistant. */
export function barColour(pct: number, thresholdPct: number): string {
  return pct >= thresholdPct ? RED : pct >= thresholdPct * 0.6 ? AMBER : GREEN;
}

function ComparisonChart({ data, threshold, chartRef }: {
  data: NonNullable<Result['comparison_chart']>; threshold: number; chartRef: React.Ref<PlotElement | null>;
}) {
  const thresholdPct = Number.isFinite(threshold) ? threshold * 100 : 50;
  const figure = useCallback((t: PlotTheme): Figure => {
    const labels = data.map(d => d.antibiotic);
    const values = data.map(d => d.resistance_probability);
    const traces: Data[] = [{
      type: 'bar', x: labels, y: values,
      marker: { color: values.map(v => barColour(v, thresholdPct)), line: { color: t.lineColor, width: 1 } },
      text: values.map(v => v.toFixed(1) + '%'),
      textposition: 'outside',
      textfont: { color: t.tickColor, size: 11 },
      hovertemplate: '%{x}<br>Resistance: %{y:.1f}%<extra></extra>',
    }];
    return {
      data: traces,
      layout: {
        paper_bgcolor: t.paper_bgcolor,
        plot_bgcolor: t.plot_bgcolor,
        margin: { t: 20, b: 100, l: 44, r: 20 },
        xaxis: { tickangle: -35, tickfont: { color: t.tickColor, size: 11 }, gridcolor: t.gridColor, linecolor: t.gridColor, automargin: true },
        yaxis: { tickfont: { color: t.tickColor }, gridcolor: t.gridColor, range: [0, 115], ticksuffix: '%' },
        shapes: [{
          type: 'line', x0: -0.5, x1: labels.length - 0.5, y0: thresholdPct, y1: thresholdPct,
          line: { color: 'rgba(239,68,68,0.55)', width: 1.5, dash: 'dash' },
        }],
        annotations: [{
          x: labels.length - 1, y: thresholdPct + 3, text: Math.round(thresholdPct) + '% threshold',
          font: { color: 'rgba(239,68,68,0.75)', size: 10 }, showarrow: false,
        }],
        font: { family: t.fontFamily },
      },
    };
  }, [data, thresholdPct]);
  return <Plot id="comparisonChart" className="chart-300" figure={figure} ref={chartRef} />;
}

function StateIcon({ state }: { state: EvidenceInput['state'] }) {
  if (state === 'used') return <i className="bi bi-check-circle-fill text-emerald2" title="Used by the model"></i>;
  if (state === 'normalized') return <i className="bi bi-arrow-repeat text-amber2" title="Adjusted before use"></i>;
  if (state === 'unrecognized') return <i className="bi bi-exclamation-triangle-fill text-amber2" title="Not recognised — ignored"></i>;
  return <i className="bi bi-dash-circle text-muted" title="Not provided"></i>;
}

/** A value with a break point after each "/", so drug pairs can wrap. */
function Breakable({ text }: { text: string }) {
  const parts = text.split('/');
  return <>{parts.map((p, i) => <Fragment key={i}>{p}{i < parts.length - 1 && <>/<wbr /></>}</Fragment>)}</>;
}

const spaced = (s: string | undefined) => (s || '').replace(/_/g, ' ');

export default function ForecastResult({ result, inputs }: { result: Result; inputs: ForecastInputs }) {
  const chart = useRef<PlotElement | null>(null);
  const resistant = result.prediction === 'Resistant';
  const ev = result.evidence;
  const heuristic = result.model_used?.startsWith('Heuristic');

  return (
    <>
      {heuristic && (
        <div className="alert alert-warning-custom mb-3" role="status">
          <i className="bi bi-exclamation-triangle me-2"></i><strong>This is not a model prediction.</strong>{' '}
          {result.model_used === 'Heuristic fallback' ? 'The trained model failed on this input' : 'No trained model is loaded'},
          so the result comes from per-antibiotic resistance rates. Do not rely on it.
        </div>
      )}
      <div className={`result-hero ${resistant ? 'result-resistant' : 'result-susceptible'} mb-4`}>
        <div className="result-hero-content">
          <div className="result-icon-large">
            <i className={resistant ? 'bi bi-shield-x' : 'bi bi-shield-check'}></i>
          </div>
          <div>
            <div className="result-label">LightGBM Prediction Result</div>
            <div className="result-main-label">{result.prediction}</div>
            <div className="result-sub">{result.antibiotic} | Confidence: {pyFloat(result.confidence)}%</div>
          </div>
          <div className="ms-auto text-end">
            <div className="result-prob-label">Resistance Probability</div>
            <div className="result-prob-val">{pyFixed(result.probability * 100, 1)}%</div>
            <div className="small text-muted">Threshold: {result.threshold}</div>
          </div>
        </div>
        <div className="prob-bar-wrap mt-3">
          <div className="prob-bar-bg">
            <div className={`prob-bar-fill ${resistant ? 'resistant-fill' : 'susceptible-fill'}`}
                 style={{ width: `${(result.probability * 100).toFixed(1)}%` }}></div>
          </div>
          <div className="d-flex justify-content-between mt-1">
            <small className="text-success fw-500">Susceptible</small>
            <small className="text-danger fw-500">Resistant</small>
          </div>
        </div>
      </div>

      <ExportBar page="forecast" result={result} inputs={inputs} chart={result.comparison_chart?.length ? chart : undefined} />

      {ev && (
        <div className={`info-card mb-4 evidence-card evidence-${ev.level}`}>
          <div className="d-flex align-items-center flex-wrap gap-2 mb-2">
            <h6 className="card-section-title mb-0">
              <i className="bi bi-clipboard-check me-2 text-accent"></i>What this prediction is based on
            </h6>{' '}
            <span className={`status-badge evidence-badge evidence-badge-${ev.level} ms-auto`}>{ev.label}</span>{' '}
            <span className="feature-tag">{ev.used_count} of {ev.total_count} inputs used</span>
          </div>
          <p className="text-muted fs-13 mb-3">{ev.summary}</p>
          <div className="table-responsive">
            <table className="table table-custom table-sm mb-0 evidence-table">
              <tbody>
                {ev.inputs.map((item, i) => (
                  <tr key={i}>
                    <td className="evidence-state-cell"><StateIcon state={item.state} /></td>
                    <td className="text-muted" style={{ width: '22%' }}>{item.field}</td>
                    <td className="fw-500 text-capitalize" style={{ width: '26%' }}>
                      <Breakable text={item.field === 'MIC' && typeof item.value === 'number' ? pyFloat(item.value) : String(item.value ?? '—')} />
                    </td>
                    <td className={'fs-12 ' + (item.state === 'used' ? 'text-2' : item.state === 'missing' ? 'text-muted' : 'text-amber2')}>
                      {item.detail}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {ev.level === 'drug_only' && (
            <div className="alert alert-warning-custom mt-3 mb-0">
              <i className="bi bi-exclamation-triangle me-2"></i>
              This number would be identical for every isolate tested against {result.antibiotic}.
              Add an MIC value to make it specific to your sample.
            </div>
          )}
        </div>
      )}

      <div className="row g-4 mb-4">
        <div className="col-md-6">
          <div className="info-card h-100">
            <h6 className="card-section-title"><i className="bi bi-info-circle me-2 text-accent"></i>Drug Information</h6>
            <table className="table table-custom table-sm">
              <tbody>
                <tr><td className="text-muted">Antibiotic</td><td className="fw-500 text-capitalize">{result.antibiotic}</td></tr>
                <tr><td className="text-muted">Drug Class</td><td className="fw-500 text-capitalize">{spaced(result.drug_class)}</td></tr>
                <tr><td className="text-muted">Model Used</td><td className="fw-500">{result.model_used}</td></tr>
                {result.related_antibiotics?.length ? (
                  <tr><td className="text-muted">Related Drugs</td><td className="fw-500">{result.related_antibiotics.join(', ')}</td></tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </div>
        <div className="col-md-6">
          <div className="info-card h-100">
            <h6 className="card-section-title"><i className="bi bi-clipboard2-pulse me-2 text-accent"></i>Clinical Interpretation</h6>
            {resistant ? (
              <div className="interp-box interp-resistant">
                <i className="bi bi-exclamation-triangle-fill me-2"></i>
                <strong>Treatment Concern</strong><br />
                This organism shows high likelihood of resistance. Consider alternative antibiotics
                from a different drug class. Cross-resistance within {spaced(result.drug_class)} class is possible.
              </div>
            ) : (
              <div className="interp-box interp-susceptible">
                <i className="bi bi-check-circle-fill me-2"></i>
                <strong>Treatment Likely Effective</strong><br />
                This organism is predicted susceptible. Standard dosing of {result.antibiotic} should
                be effective. Monitor MIC values during treatment.
              </div>
            )}
          </div>
        </div>
      </div>

      {result.comparison_chart?.length ? (
        <div className="info-card mb-4">
          <h6 className="card-section-title"><i className="bi bi-bar-chart me-2 text-accent"></i>Resistance Probability Comparison (Common Antibiotics)</h6>
          <ComparisonChart data={result.comparison_chart} threshold={result.threshold} chartRef={chart} />
        </div>
      ) : null}
    </>
  );
}
