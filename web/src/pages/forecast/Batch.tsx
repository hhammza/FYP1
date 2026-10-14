/* "Upload CSV" on /forecast: many isolates at once through
   /api/forecast/batch/, a summary, a chart per antibiotic and the rows. */
import { useCallback, useRef, useState, type FormEvent } from 'react';
import type { Data } from 'plotly.js-dist-min';
import ExportBar from '../../components/ExportBar';
import Plot, { type Figure, type PlotElement, type PlotTheme } from '../../components/Plot';
import { thousands } from '../../lib/metrics';
import type { BatchResult as Result } from './types';

const SHOWN_ROWS = 200;
const CHART_DRUGS = 20;

export function BatchForm({ busy, onSubmit }: { busy: boolean; onSubmit: (file: File) => void }) {
  const [file, setFile] = useState<File | null>(null);
  function submit(e: FormEvent) {
    e.preventDefault();
    if (file) onSubmit(file);
  }
  return (
    <form id="batchForm" onSubmit={submit}>
      <p className="text-muted fs-13">Predict many isolates at once. One row per isolate; only{' '}
        <code>antibiotic</code> is required.</p>
      <div className="mb-3">
        <label htmlFor="batchFile" className="form-label-custom">CSV file <span className="required">*</span></label>
        <input type="file" name="batch_file" id="batchFile" className="form-control form-control-custom"
               accept=".csv,text/csv" required onChange={e => setFile(e.target.files?.[0] ?? null)} />
        <div className="form-hint">Columns: antibiotic, genus, species, taxon_id, mic_value, mic_sign.
          Up to 10,000 rows and 2 MB. Rows with a problem are marked, not dropped.</div>
      </div>
      <a href="/amr-batch-template.csv" download="amr-batch-template.csv" className="btn btn-outline-custom btn-sm w-100 mb-3">
        <i className="bi bi-download me-1"></i>Download a sample CSV
      </a>
      <button type="submit" className="btn btn-primary-custom w-100 btn-lg" disabled={busy}>
        {busy
          ? <><span className="spinner-border spinner-border-sm me-2" role="status"></span>Processing…</>
          : <><i className="bi bi-cpu me-2"></i>Predict All Rows</>}
      </button>
    </form>
  );
}

function BatchChart({ byAb, chartRef }: { byAb: Result['summary']['by_antibiotic']; chartRef: React.Ref<PlotElement | null> }) {
  const figure = useCallback((t: PlotTheme): Figure => {
    const shown = byAb.slice(0, CHART_DRUGS);
    const labels = shown.map(d => d.antibiotic);
    const bar = (name: string, values: number[], color: string): Data => ({
      type: 'bar', name, x: labels, y: values, marker: { color },
      hovertemplate: '%{x}<br>' + name + ': %{y}<extra></extra>',
    });
    return {
      data: [bar('Resistant', shown.map(d => d.resistant), 'rgba(239,68,68,0.82)'),
             bar('Susceptible', shown.map(d => d.n - d.resistant), 'rgba(34,197,94,0.82)')],
      layout: {
        barmode: 'stack',
        paper_bgcolor: t.paper_bgcolor,
        plot_bgcolor: t.plot_bgcolor,
        margin: { t: 20, b: 100, l: 50, r: 20 },
        xaxis: { tickangle: -35, tickfont: { color: t.tickColor, size: 11 }, gridcolor: t.gridColor, linecolor: t.gridColor },
        yaxis: { title: { text: 'Rows', font: { color: t.tickColor } }, tickfont: { color: t.tickColor }, gridcolor: t.gridColor },
        legend: { orientation: 'h', y: 1.12, font: { color: t.tickColor } },
        font: { family: t.fontFamily },
      },
    };
  }, [byAb]);
  return <Plot id="batchChart" className="chart-300" figure={figure} ref={chartRef} />;
}

export function BatchResult({ batch }: { batch: Result }) {
  const chart = useRef<PlotElement | null>(null);
  const s = batch.summary;
  const hasChart = s.by_antibiotic?.length > 0;
  return (
    <>
      <div className="info-card mb-4">
        <h6 className="card-section-title"><i className="bi bi-table me-2 text-accent"></i>Batch results</h6>
        <div className="row g-2 text-center mb-2">
          <div className="col-6 col-md-3"><div className="stat-mini"><div className="stat-mini-value">{thousands(s.rows)}</div><div className="stat-mini-label">Rows</div></div></div>
          <div className="col-6 col-md-3"><div className="stat-mini"><div className="stat-mini-value text-rose2">{thousands(s.resistant)}</div><div className="stat-mini-label">Resistant</div></div></div>
          <div className="col-6 col-md-3"><div className="stat-mini"><div className="stat-mini-value text-emerald2">{thousands(s.susceptible)}</div><div className="stat-mini-label">Susceptible</div></div></div>
          <div className="col-6 col-md-3"><div className="stat-mini"><div className={'stat-mini-value' + (s.errors ? ' text-amber2' : '')}>{thousands(s.errors)}</div><div className="stat-mini-label">Rows with a problem</div></div></div>
        </div>
        <div className="text-muted fs-12">Model {batch.model_run}{batch.calibrated ? ', calibrated' : ''},
          threshold {batch.threshold}: a row is called Resistant at or above it.</div>
      </div>

      <ExportBar page="batch" result={batch} chart={hasChart ? chart : undefined} />

      {hasChart && (
        <div className="info-card mb-4">
          <h6 className="card-section-title"><i className="bi bi-bar-chart me-2 text-accent"></i>Resistant and susceptible, per antibiotic</h6>
          <BatchChart byAb={s.by_antibiotic} chartRef={chart} />
        </div>
      )}

      <div className="info-card mb-4">
        <h6 className="card-section-title"><i className="bi bi-list-ul me-2 text-accent"></i>Rows{' '}
          {batch.rows.length > SHOWN_ROWS && (
            <span className="text-muted fs-12">(first {SHOWN_ROWS} of {thousands(batch.rows.length)}; the CSV has all)</span>
          )}</h6>
        <div className="table-responsive">
          <table className="table table-custom table-sm mb-0">
            <thead><tr><th>Row</th><th>Antibiotic</th><th>Organism</th><th>Taxon</th><th>MIC</th><th>Prediction</th><th>P(R)</th></tr></thead>
            <tbody>
              {batch.rows.slice(0, SHOWN_ROWS).map(r => (
                <tr key={r.row}>
                  <td className="font-mono">{r.row}</td>
                  <td>{r.antibiotic}</td>
                  <td>{r.genus} {r.species}</td>
                  <td className="font-mono">{r.taxon_id}</td>
                  <td className="font-mono">{r.mic_sign}{r.mic_value}</td>
                  {r.error ? (
                    <td colSpan={2} className="text-amber2 fs-12"><i className="bi bi-exclamation-triangle me-1"></i>{r.error}</td>
                  ) : (
                    <>
                      <td className={(r.prediction === 'Resistant' ? 'text-rose2' : 'text-emerald2') + ' fw-500'}>{r.prediction}</td>
                      <td className="font-mono">{((r.probability ?? 0) * 100).toFixed(1)}%</td>
                    </>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
