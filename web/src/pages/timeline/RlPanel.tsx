/* The RL panel on /timeline (_rl_panel.html; format §4, "RL panel").
     result.rl absent -> RL was not run (agent not trained, or not for this drug): no panel
     result.rl         -> the agent and the fixed baselines on the same simulation
   Week w's value is the resistant share of the drug given in week w at the
   end of that week (resistant_fraction[drug][w]); first-failure weeks are
   the data's own. */
import { useCallback, useState } from 'react';
import type { Data, Layout } from 'plotly.js-dist-min';
import Plot, { type Figure, type PlotTheme } from '../../components/Plot';
import type { RlBlock, RlPolicy } from './types';

const DRUG_COLOURS = ['#6366f1', '#f59e0b', '#10b981', '#ec4899', '#0ea5e9', '#a855f7'];
const POLICY_COLOURS = ['#7c3aed', '#ef4444', '#0ea5e9', '#f59e0b', '#10b981', '#64748b'];
const NARROW_PX = 576;

/** Resistance of the drug given in week w, at the end of week w. */
export function givenResistance(p: RlPolicy): (number | undefined)[] {
  return p.policy.map((drug, i) => (p.resistant_fraction[drug] || [])[i + 1]);
}

/** 'trimethoprim' -> 'trimeth.', so a chip fits. */
export const shortDrug = (d: string) => (d.length > 8 ? d.slice(0, 7) + '.' : d);

function layout(t: PlotTheme, n: number, xRange?: [number, number]): Partial<Layout> {
  const narrow = window.innerWidth < NARROW_PX;
  return {
    paper_bgcolor: t.paper_bgcolor, plot_bgcolor: t.plot_bgcolor,
    margin: { t: 10, b: 50, l: 50, r: 16 },
    legend: { font: { color: t.tickColor, size: 11 }, orientation: 'h', x: 0, y: 1.02, yanchor: 'bottom' },
    xaxis: { tickfont: { color: t.tickColor, size: 11 }, gridcolor: t.gridColor, linecolor: t.gridColor,
             title: { text: 'Week', font: { color: t.tickColor, size: 12 } },
             dtick: narrow && n > 13 ? 2 : 1, automargin: true, ...(xRange ? { range: xRange } : {}) },
    yaxis: { tickfont: { color: t.tickColor }, gridcolor: t.gridColor, range: [0, 105], ticksuffix: '%',
             title: { text: 'Resistant %', font: { color: t.tickColor, size: 12 } } },
    shapes: [{ type: 'line', xref: 'paper', x0: 0, x1: 1, y0: 50, y1: 50,
               line: { color: 'rgba(239,68,68,0.5)', width: 1.5, dash: 'dash' } }],
    font: { family: t.fontFamily },
    hovermode: 'x unified',
  };
}

export default function RlPanel({ rl, nWeeks }: { rl: RlBlock | null | undefined; nWeeks: number }) {
  const policies = rl?.policies ?? [];
  const bestIndex = Math.max(0, policies.findIndex(p => p.name === rl?.best));
  const [chosen, setChosen] = useState(bestIndex);
  const n = rl?.n_weeks || nWeeks;
  const chartWeeks = rl?.n_weeks || policies[0]?.policy.length || nWeeks;
  const drugColour = useCallback(
    (d: string) => DRUG_COLOURS[Math.max(0, (rl?.drugs ?? []).indexOf(d)) % DRUG_COLOURS.length], [rl]);

  /* One line per policy: how resistant the drug it gave was */
  const policiesFigure = useCallback((t: PlotTheme): Figure => {
    const weeks = Array.from({ length: chartWeeks }, (_, i) => i + 1);
    return {
      data: policies.map((p, i): Data => ({
        name: p.label + (p.name === rl?.best ? ' (best)' : ''),
        x: weeks, y: givenResistance(p) as number[], customdata: p.policy,
        mode: 'lines+markers',
        line: { color: POLICY_COLOURS[i % POLICY_COLOURS.length], width: p.name === rl?.best ? 3.5 : 2,
                dash: p.name === 'rl' || p.name === rl?.best ? 'solid' : 'dot' },
        marker: { size: p.name === rl?.best ? 7 : 5 },
        hovertemplate: '%{customdata}: %{y:.1f}%<extra>' + p.label + '</extra>',
      })),
      layout: layout(t, chartWeeks),
    };
  }, [policies, rl, chartWeeks]);

  /* The chosen policy: every drug's resistance */
  const p = policies[chosen];
  const drugsFigure = useCallback((t: PlotTheme): Figure => {
    const all = Array.from({ length: chartWeeks + 1 }, (_, k) => k);
    return {
      data: (rl?.drugs ?? []).map((d): Data => ({
        name: d, x: all, y: p?.resistant_fraction[d] || [], mode: 'lines',
        line: { color: drugColour(d), width: 2.5 },
        hovertemplate: d + ': %{y:.1f}%<extra></extra>',
      })),
      layout: layout(t, chartWeeks, [0, chartWeeks]),
    };
  }, [rl, p, chartWeeks, drugColour]);

  if (!rl || !policies.length) return null;
  const given = givenResistance(p);

  return (
    <div className="info-card mb-4" id="rlPanel">
      <h6 className="card-section-title mb-1">
        <i className="bi bi-shuffle text-accent me-2"></i>Simulation + RL policy <span className="text-muted fw-normal">(not trained on patient data)</span>
      </h6>
      <p className="small text-muted mb-3">
        Which drug to give each week so that one of them keeps working longest. The{' '}
        {rl.agent ? `agent (${rl.agent})` : 'fixed baselines'} and the policies it is compared with run on the
        same simulation, from the same starting resistance: {rl.drugs.join(', ')}. A week fails when the drug given is at
        50% resistance or more. Weeks and resistance levels are illustrative, not a treatment plan.
      </p>

      <div className="rl-chart-wrap mb-2">
        <div className="small fw-600 mb-1">Resistance to the drug given each week</div>
        <div role="img" aria-label="Resistance to the drug given each week, one line per policy">
          <Plot id="rlChart" className="chart-300" figure={policiesFigure} />
        </div>
      </div>

      <div className="d-flex flex-wrap align-items-center gap-2 mb-2">
        <label className="small text-muted mb-0" htmlFor="rlPolicySelect">Drugs given by</label>
        <select id="rlPolicySelect" className="form-select form-select-custom form-select-sm w-auto"
                value={chosen} onChange={e => setChosen(Number(e.target.value))}>
          {policies.map((q, i) => <option key={q.name} value={i}>{q.label}{q.name === rl.best ? ' (best)' : ''}</option>)}
        </select>
      </div>
      <div id="rlChips" className="rl-chips mb-3" aria-label="Drug given each week">
        {p.policy.map((drug, w) => (
          <span key={w} className={'rl-chip' + ((given[w] ?? 0) >= 50 ? ' rl-chip-failed' : '')}
                style={{ borderLeftColor: drugColour(drug) }}
                title={`Week ${w + 1}: ${drug}, ${given[w] !== undefined ? given[w]!.toFixed(1) + '% resistant' : ''}`}>
            <span className="rl-chip-week">W{w + 1}</span><span>{shortDrug(drug)}</span>
          </span>
        ))}
      </div>
      <div role="img" aria-label="Resistance to each drug under the selected policy">
        <Plot id="rlDrugChart" className="chart-250 mb-3" figure={drugsFigure} />
      </div>

      <div className="table-responsive">
        <table className="table table-custom table-sm mb-0 rl-table">
          <thead><tr>
            <th>Policy</th><th>First failed week</th>
            <th>Effective weeks</th><th>Mean resistance of the drug given</th><th>Reward</th>
          </tr></thead>
          <tbody>
            {policies.map(q => (
              <tr key={q.name} className={q.name === rl.best ? 'report-best-row' : undefined}>
                <td className="small">{q.label}{q.name === rl.best && <> <span className="status-badge trained ms-1">Best</span></>}</td>
                <td className="small">{q.failure_week == null ? `Never in ${n} weeks` : `Week ${q.failure_week}`}</td>
                <td className="font-mono small">{q.effective_weeks != null ? `${q.effective_weeks} / ${n}` : '—'}</td>
                <td className="font-mono small">{q.mean_burden != null ? `${q.mean_burden.toFixed(1)}%` : '—'}</td>
                <td className="font-mono small">{typeof q.total_reward === 'number' ? q.total_reward.toFixed(2) : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="caption-text mt-2">
        Best: the latest first failure (never failing beats any week), then the higher reward. Effective weeks: weeks the drug
        given was under 50% resistance.
      </div>
    </div>
  );
}
