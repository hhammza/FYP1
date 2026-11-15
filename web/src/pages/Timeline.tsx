/* /timeline (frontend/templates/mutation_timeline.html), two tabs:
   - "ML trend forecast", the default: the timeline ML model (POST /api/timeline/,
     format §8). An antibiotic and an organism, chosen or identified from an
     uploaded genome, give the yearly resistant share and the model's forecast.
   - "What-if simulation": the logistic-growth simulation, not a trained model,
     week by week under treatment, with Ali's RL panel (POST /api/timeline/simulate/,
     format §4).
   /timeline/sample opens the what-if tab on the agreed sample response, on a
   development run only. */
import { useEffect, useRef, useState } from 'react';
import BioIcon from '../components/BioIcon';
import ExportBar from '../components/ExportBar';
import type { PlotElement } from '../components/Plot';
import { apiPost, apiUpload, errorText } from '../lib/api';
import { usePageEffects, useTitle } from '../lib/pageEffects';
import MlForecastCard from './timeline/MlForecastCard';
import SimulationForm, { type SimulationSubmit } from './timeline/SimulationForm';
import SimulationResult from './timeline/SimulationResult';
import TimelineForm, { type TimelineSubmit } from './timeline/TimelineForm';
import { ContextStrip, ModelGuides, SimulationEmpty, SimulationGuides, TimelineBackground, TimelineEmpty,
         TimelineHeader } from './timeline/static';
import type { SimulationInputs, SimulationResult as SimResult, TimelineResult } from './timeline/types';

const MAX_FASTA_MB = 20;      // settings.MAX_FASTA_BYTES in the backend
const NAVBAR_PX = 64;

type Mode = 'forecast' | 'simulation';
type Forecast = { result: TimelineResult; inputs: { antibiotic: string; years_ahead: string; genus?: string } } | null;
type Simulated = { result: SimResult; inputs: SimulationInputs; sample?: boolean } | null;

const tooBig = (genome: { file: File } | { text: string }) =>
  'file' in genome && genome.file.size > MAX_FASTA_MB * 1024 * 1024;

/** The agreed sample response (progress/formats/), for /timeline/sample on a dev run. */
async function loadSample(): Promise<SimResult | null> {
  if (!import.meta.env.DEV) return null;
  const mod = await import('../../../progress/formats/timeline_response.sample.json');
  const { _comment, ml_forecast, ...result } = mod.default as unknown as SimResult & { _comment?: string; ml_forecast?: unknown };
  void _comment; void ml_forecast;
  return result;
}

export default function Timeline({ sample = false }: { sample?: boolean }) {
  useTitle('Mutation Timeline');
  const [mode, setMode] = useState<Mode>(sample ? 'simulation' : 'forecast');
  const [forecastShown, setForecastShown] = useState<Forecast>(null);
  const [simShown, setSimShown] = useState<Simulated>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [root, setRoot] = useState<HTMLDivElement | null>(null);
  const [answered, setAnswered] = useState(0);
  const results = useRef<HTMLDivElement>(null);
  const chart = useRef<PlotElement | null>(null);
  usePageEffects(root, [forecastShown, simShown, mode]);

  useEffect(() => {
    if (!sample) return;
    loadSample().then(r => {
      if (r) setSimShown({ result: r, inputs: { antibiotic: r.antibiotic, n_weeks: String(r.n_weeks ?? 8) }, sample: true });
      else setError('The sample preview is only available on a local run.');
    }).catch(() => setError('The sample preview is only available on a local run.'));
  }, [sample]);

  /* A new result or error opens where it can be seen, as the Flask page's reload did */
  useEffect(() => {
    const el = results.current;
    if (!answered || !el) return;
    const top = el.getBoundingClientRect().top;
    if (top < NAVBAR_PX || top > window.innerHeight / 2) {
      window.scrollTo({ top: Math.max(0, window.scrollY + top - NAVBAR_PX - 16), behavior: 'smooth' });
    }
  }, [answered]);

  async function run<T>(call: () => Promise<T>, done: (r: T) => void, failed: () => void) {
    setError('');
    setBusy(true);
    try {
      done(await call());
    } catch (e) {
      failed();
      setError(errorText(e));
    } finally {
      setBusy(false);
      setAnswered(n => n + 1);
    }
  }

  function forecast({ antibiotic, years_ahead, organism }: TimelineSubmit) {
    if ('genome' in organism && tooBig(organism.genome)) {
      setForecastShown(null);
      setError(`The file is too large: the limit is ${MAX_FASTA_MB} MB.`);
      setAnswered(n => n + 1);
      return;
    }
    run(() => {
      if ('genus' in organism) return apiPost<TimelineResult>('timeline/', { antibiotic, genus: organism.genus, years_ahead });
      if ('file' in organism.genome) {
        const form = new FormData();
        form.append('fasta_file', organism.genome.file, organism.genome.file.name);
        form.append('antibiotic', antibiotic);
        form.append('years_ahead', years_ahead);
        return apiUpload<TimelineResult>('timeline/', form);
      }
      return apiPost<TimelineResult>('timeline/', { fasta_text: organism.genome.text, antibiotic, years_ahead });
    }, result => setForecastShown({ result, inputs: { antibiotic, years_ahead, genus: result.ml_forecast.organism } }),
    () => setForecastShown(null));
  }

  function simulate({ antibiotic, n_weeks, genome }: SimulationSubmit) {
    if (tooBig(genome)) {
      setSimShown(null);
      setError(`The file is too large: the limit is ${MAX_FASTA_MB} MB.`);
      setAnswered(n => n + 1);
      return;
    }
    run(() => {
      if ('file' in genome) {
        const form = new FormData();
        form.append('fasta_file', genome.file, genome.file.name);
        form.append('antibiotic', antibiotic);
        form.append('n_weeks', n_weeks);
        return apiUpload<SimResult>('timeline/simulate/', form);
      }
      // n_weeks as typed: the backend checks it
      return apiPost<SimResult>('timeline/simulate/', { fasta_text: genome.text, antibiotic, n_weeks });
    }, result => setSimShown({ result, inputs: { antibiotic, n_weeks } }), () => setSimShown(null));
  }

  const shown = mode === 'forecast' ? forecastShown : simShown;
  const tab = (which: Mode, icon: string, label: string) => (
    <li className="nav-item" role="presentation">
      <button className={'nav-link' + (mode === which ? ' active' : '')} type="button" role="tab"
              aria-selected={mode === which} onClick={() => { setMode(which); setError(''); }}>
        <BioIcon icon={`bi-${icon}`} className="me-1" />{label}
      </button>
    </li>
  );

  return (
    <>
      <TimelineHeader />
      <div className="container-xl py-4" ref={setRoot}>
        <ContextStrip />
        <div className="row g-4">
          <div className="col-lg-4">
            <div className="form-card">
              <h5 className="form-card-title"><i className="bi bi-calendar-week me-2"></i>Timeline Parameters</h5>
              <ul className="nav nav-pills nav-custom mb-3" role="tablist" aria-label="Timeline mode">
                {tab('forecast', 'graph-up-arrow', 'ML trend forecast')}
                {tab('simulation', 'sliders', 'What-if simulation')}
              </ul>
              {/* both stay mounted, so switching modes keeps what was chosen */}
              <div className={mode === 'forecast' ? '' : 'd-none'} role="tabpanel" id="trendPane">
                <TimelineForm busy={busy} onSubmit={forecast} />
              </div>
              <div className={mode === 'simulation' ? '' : 'd-none'} role="tabpanel" id="simulationPane">
                <div className="alert alert-warning-custom py-2 small mb-3">
                  <i className="bi bi-info-circle me-1"></i><strong>Simulation, not a trained model.</strong> Hand-set
                  constants; use the ML trend forecast for a measured answer.
                </div>
                <SimulationForm busy={busy} onSubmit={simulate} initial={simShown?.sample ? simShown.inputs : undefined} />
              </div>
            </div>
            {mode === 'forecast' ? <ModelGuides /> : <SimulationGuides />}
          </div>

          {/* results come first below 992px once there is one */}
          <div className={'col-lg-8' + (shown ? ' order-first order-lg-0' : '')} ref={results}>
            {error && <div className="alert alert-danger-custom"><i className="bi bi-exclamation-circle me-2"></i>{error}</div>}
            {mode === 'forecast'
              ? (forecastShown
                  ? <>
                      <MlForecastCard ml={forecastShown.result.ml_forecast} source={forecastShown.result.organism_source} chartRef={chart} />
                      <ExportBar page="timeline" result={forecastShown.result} inputs={forecastShown.inputs} chart={chart} />
                    </>
                  : <TimelineEmpty />)
              : (simShown
                  ? <SimulationResult result={simShown.result} inputs={simShown.inputs} sample={simShown.sample} />
                  : <SimulationEmpty />)}
          </div>
        </div>
        <TimelineBackground />
      </div>
    </>
  );
}
