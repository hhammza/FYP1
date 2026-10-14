/* One simulation on /timeline: the summary, the week-by-week chart,
   downloads, the RL panel, hotspots, gene activation and the weekly table. */
import { useCallback, useRef, useState } from 'react';
import type { Data, Shape } from 'plotly.js-dist-min';
import ExportBar from '../../components/ExportBar';
import Plot, { type Figure, type PlotElement, type PlotTheme } from '../../components/Plot';
import { jinjaTitle, pyFloat, thousands } from '../../lib/metrics';
import RlPanel from './RlPanel';
import type { TimelineInputs, TimelineResult as Result, Week } from './types';

const NARROW_PX = 576;

function TimelineChart({ weeks: data, failWeek, chartRef }: {
  weeks: Week[]; failWeek: number | null; chartRef: React.Ref<PlotElement | null>;
}) {
  const figure = useCallback((t: PlotTheme): Figure => {
    const weeks = data.map(d => d.week);
    const narrow = window.innerWidth < NARROW_PX;
    const traces: Data[] = [
      { name: 'Resistant', x: weeks, y: data.map(d => d.resistant_fraction), mode: 'lines+markers',
        line: { color: '#ef4444', width: 3 }, marker: { size: 6 }, fill: 'tozeroy', fillcolor: 'rgba(239,68,68,0.1)',
        hovertemplate: 'Week %{x}<br>Resistant: %{y:.1f}%<extra></extra>' },
      { name: 'Intermediate', x: weeks, y: data.map(d => d.intermediate_fraction), mode: 'lines',
        line: { color: '#f59e0b', width: 2, dash: 'dot' },
        hovertemplate: 'Week %{x}<br>Intermediate: %{y:.1f}%<extra></extra>' },
      { name: 'Susceptible', x: weeks, y: data.map(d => d.susceptible_fraction), mode: 'lines+markers',
        line: { color: '#22c55e', width: 3 }, marker: { size: 6 },
        hovertemplate: 'Week %{x}<br>Susceptible: %{y:.1f}%<extra></extra>' },
    ];
    const shapes: Partial<Shape>[] = [{
      type: 'line', x0: weeks[0], x1: weeks[weeks.length - 1], y0: 50, y1: 50,
      line: { color: 'rgba(239,68,68,0.5)', width: 1.5, dash: 'dash' }, xref: 'x', yref: 'y',
    }];
    if (failWeek !== null && failWeek !== undefined) {
      shapes.push({ type: 'line', x0: failWeek, x1: failWeek, y0: 0, y1: 100,
                    line: { color: 'rgba(239,68,68,0.7)', width: 2, dash: 'dash' }, xref: 'x', yref: 'y' });
    }
    return {
      data: traces,
      layout: {
        paper_bgcolor: t.paper_bgcolor, plot_bgcolor: t.plot_bgcolor,
        margin: { t: 30, b: 50, l: 50, r: 16 },
        legend: { font: { color: t.tickColor }, orientation: 'h', x: 0, y: 1.02, yanchor: 'bottom' },
        xaxis: { tickfont: { color: t.tickColor, size: 11 }, gridcolor: t.gridColor, linecolor: t.gridColor,
                 title: { text: 'Week', font: { color: t.tickColor, size: 12 } },
                 dtick: narrow && weeks.length > 13 ? 2 : 1, automargin: true },
        yaxis: { tickfont: { color: t.tickColor }, gridcolor: t.gridColor, range: [0, 105], ticksuffix: '%',
                 title: { text: 'Population %', font: { color: t.tickColor, size: 12 } } },
        shapes,
        annotations: [{ x: weeks[Math.floor(weeks.length / 2)], y: 53,
                        text: narrow ? '50% failure' : '50% — Treatment Failure Threshold',
                        font: { color: 'rgba(239,68,68,0.8)', size: 10 }, showarrow: false }],
        font: { family: t.fontFamily },
        hovermode: 'x unified',
      },
    };
  }, [data, failWeek]);
  return <Plot id="timelineChart" className="chart-350" figure={figure} ref={chartRef} />;
}

interface Props {
  result: Result;
  inputs: TimelineInputs;
  /** the agreed sample response, not a simulation (/timeline/sample) */
  sample?: boolean;
}

export default function TimelineResult({ result, inputs, sample }: Props) {
  const chart = useRef<PlotElement | null>(null);
  const [table, setTable] = useState(false);
  const failed = !!result.failure_week;
  const cal = result.calibration;

  return (
    <>
      {sample && (
        <div className="alert alert-warning-custom mb-3" role="status">
          <i className="bi bi-eye me-2"></i><strong>Sample response, not a real simulation.</strong>{' '}
          This is <code>progress/formats/timeline_response.sample.json</code>, shown to preview the layout and the RL panel.
        </div>
      )}

      <div className="timeline-summary-card mb-4">
        <div className="row g-3 align-items-center">
          <div className="col-md-8">
            <div className="d-flex align-items-center gap-3 mb-2">
              <div className={`timeline-icon-sm ${failed ? 'danger-icon' : 'warning-icon'}`}>
                <i className={`bi bi-${failed ? 'exclamation-triangle' : 'check-circle'}`}></i>
              </div>
              <div>
                <div className="fw-700 fs-5 text-white">{jinjaTitle(result.antibiotic)}</div>
                <div className="text-muted small">{jinjaTitle(result.antibiotic_class || '')} | {result.n_weeks}-week simulation</div>
              </div>
            </div>
            <p className="text-muted mb-0">{result.summary}</p>
          </div>
          <div className="col-md-4">
            <div className="row g-2 text-center">
              <div className="col-6">
                <div className={`timeline-stat ${failed ? 'stat-danger' : 'stat-warning'}`}>
                  <div className="timeline-stat-val">{failed ? `Week ${result.failure_week}` : 'Not reached'}</div>
                  <div className="timeline-stat-lbl">Treatment Failure</div>
                </div>
              </div>
              <div className="col-6">
                <div className="timeline-stat stat-info">
                  <div className="timeline-stat-val">{pyFloat(result.final_resistant_percent)}%</div>
                  <div className="timeline-stat-lbl">Final Resistance</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="info-card mb-4">
        <h6 className="card-section-title"><i className="bi bi-graph-up text-accent me-2"></i>Week-by-Week Resistance Evolution</h6>
        <TimelineChart weeks={result.timeline} failWeek={result.failure_week} chartRef={chart} />
      </div>

      <ExportBar page="timeline" result={result} inputs={inputs} chart={chart} />

      <RlPanel rl={result.rl} nWeeks={result.n_weeks} />

      <div className="row g-4 mb-4">
        <div className="col-md-6">
          <div className="info-card h-100">
            <h6 className="card-section-title"><i className="bi bi-geo-alt text-accent me-2"></i>Mutation Hotspots</h6>
            <div className="table-responsive max-h-280">
              <table className="table table-custom table-sm">
                <thead><tr><th>Position</th><th>Orig→Mut</th><th>Type</th></tr></thead>
                <tbody>
                  {(result.mutation_hotspots || []).slice(0, 10).map((hs, i) => (
                    <tr key={i}>
                      <td className="font-mono text-accent">{thousands(hs.position)}</td>
                      <td className="font-mono fw-500">{hs.original_nucleotide}→{hs.mutated_nucleotide}</td>
                      <td className="small text-muted">{hs.mutation_type}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="col-md-6">
          <div className="info-card h-100">
            <h6 className="card-section-title"><i className="bi bi-bezier2 text-accent me-2"></i>Resistance Gene Activation</h6>
            {(result.resistance_genes || []).map(g => (
              <div className="gene-row" key={g.gene}>
                <div className="d-flex justify-content-between mb-1">
                  <span className="font-mono fw-500 text-accent">{g.gene}</span>
                  <span className="text-muted small">Week {g.activation_week}</span>
                </div>
                <div className="prob-bar-bg">
                  <div className="prob-bar-fill gene-fill" style={{ width: `${g.resistance_contribution.toFixed(1)}%` }}></div>
                </div>
                <div className="text-muted small mt-1">{pyFloat(g.resistance_contribution)}% resistance contribution</div>
              </div>
            ))}
            <div className="mt-3 pt-3 border-top border-dark">
              <div className="d-flex justify-content-between text-muted small">
                <span>Genome Length: <span className="text-white">{thousands(result.sequence_length)} bp</span></span>
                <span>GC: <span className="text-white">{pyFloat(result.gc_content)}%</span></span>
              </div>
              <div className="text-muted small mt-1">Model: <span className="text-white">{result.model_used}</span></div>
              <div className="text-muted small mt-1">
                {cal ? (
                  <>
                    Checked against <span className="text-white">{cal.curves} published curves</span>{' '}
                    (fit error &plusmn;{cal.rmse.toFixed(1)} points on {cal.surveillance_curves} hospital series).{' '}
                    {!cal.drugs.includes(result.antibiotic) && `${jinjaTitle(result.antibiotic)} was not among the drugs fitted. `}
                    Weeks are illustrative.
                  </>
                ) : 'Not calibrated against published data.'}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="info-card">
        <div className="d-flex justify-content-between align-items-center gap-2 mb-3">
          <h6 className="card-section-title mb-0"><i className="bi bi-table text-accent me-2"></i>Weekly Resistance Data</h6>
          <button className="btn btn-outline-custom btn-sm" type="button" aria-expanded={table} aria-controls="timelineTable"
                  onClick={() => setTable(v => !v)}>
            <i className={table ? 'bi bi-chevron-up' : 'bi bi-chevron-down'} id="tableChevron"></i> Toggle
          </button>
        </div>
        <div id="timelineTable" className={table ? '' : 'd-none'}>
          <div className="table-responsive">
            <table className="table table-custom table-sm">
              <thead><tr>
                <th>Week</th><th>Resistant %</th><th>Susceptible %</th>
                <th>Intermediate %</th><th>Cum. Mutations</th><th>MIC Fold</th><th>Effective?</th>
              </tr></thead>
              <tbody>
                {result.timeline.map(w => (
                  <tr key={w.week} className={w.treatment_effective ? undefined : 'text-danger-muted'}>
                    <td className="fw-500">{w.week}</td>
                    <td className={w.resistant_fraction > 50 ? 'text-danger' : w.resistant_fraction > 30 ? 'text-warning' : 'text-success'}>
                      {pyFloat(w.resistant_fraction)}%</td>
                    <td className="text-success">{pyFloat(w.susceptible_fraction)}%</td>
                    <td className="text-warning">{pyFloat(w.intermediate_fraction)}%</td>
                    <td className="font-mono">{w.cumulative_mutations}</td>
                    <td>{pyFloat(w.mic_fold_change)}x</td>
                    <td>
                      {w.treatment_effective
                        ? <span className="badge-yes"><i className="bi bi-check-lg"></i> Yes</span>
                        : <span className="badge-no"><i className="bi bi-x-lg"></i> No</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </>
  );
}
