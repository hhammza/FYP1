/* /timeline: the resistance simulation and, when Ali's agent answers, the RL
   panel (frontend/templates/mutation_timeline.html). /timeline/sample shows
   the agreed sample response, on a development run only, as the Flask site did. */
import { useEffect, useRef, useState } from 'react';
import { apiPost, apiUpload, errorText } from '../lib/api';
import { usePageEffects, useTitle } from '../lib/pageEffects';
import TimelineForm, { type TimelineSubmit } from './timeline/TimelineForm';
import TimelineResult from './timeline/TimelineResult';
import { ContextStrip, SimulationGuides, TimelineBackground, TimelineEmpty, TimelineHeader } from './timeline/static';
import type { TimelineInputs, TimelineResult as Result } from './timeline/types';

const MAX_FASTA_MB = 20;      // settings.MAX_FASTA_BYTES in the backend
const NAVBAR_PX = 64;

type Shown = { result: Result; inputs: TimelineInputs; sample?: boolean } | null;

/** The agreed sample response (progress/formats/), for /timeline/sample on a dev run. */
async function loadSample(): Promise<Result | null> {
  if (!import.meta.env.DEV) return null;
  const mod = await import('../../../progress/formats/timeline_response.sample.json');
  const { _comment, ...result } = mod.default as unknown as Result & { _comment?: string };
  void _comment;
  return result;
}

export default function Timeline({ sample = false }: { sample?: boolean }) {
  useTitle('Mutation Timeline');
  const [shown, setShown] = useState<Shown>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [root, setRoot] = useState<HTMLDivElement | null>(null);
  const [answered, setAnswered] = useState(0);
  const results = useRef<HTMLDivElement>(null);
  usePageEffects(root, [shown]);

  useEffect(() => {
    if (!sample) return;
    loadSample().then(r => {
      if (r) setShown({ result: r, inputs: { antibiotic: r.antibiotic, n_weeks: String(r.n_weeks ?? 8) }, sample: true });
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

  async function simulate({ antibiotic, n_weeks, genome }: TimelineSubmit) {
    setError('');
    const inputs = { antibiotic, n_weeks };
    if ('file' in genome && genome.file.size > MAX_FASTA_MB * 1024 * 1024) {
      setShown(null);
      setError(`The file is too large: the limit is ${MAX_FASTA_MB} MB.`);
      setAnswered(n => n + 1);
      return;
    }
    setBusy(true);
    try {
      let result: Result;
      if ('file' in genome) {
        const form = new FormData();
        form.append('fasta_file', genome.file, genome.file.name);
        form.append('antibiotic', antibiotic);
        form.append('n_weeks', n_weeks);
        result = await apiUpload<Result>('timeline/', form);
      } else {
        // n_weeks as typed: the backend checks it
        result = await apiPost<Result>('timeline/', { fasta_text: genome.text, antibiotic, n_weeks });
      }
      setShown({ result, inputs });
    } catch (e) {
      setShown(null);
      setError(errorText(e));
    } finally {
      setBusy(false);
      setAnswered(n => n + 1);
    }
  }

  return (
    <>
      <TimelineHeader />
      <div className="container-xl py-4" ref={setRoot}>
        <ContextStrip />
        <div className="row g-4">
          <div className="col-lg-4">
            <div className="form-card">
              <h5 className="form-card-title"><i className="bi bi-calendar-week me-2"></i>Timeline Parameters</h5>
              <TimelineForm busy={busy} onSubmit={simulate} initial={shown?.sample ? shown.inputs : undefined} />
            </div>
            <SimulationGuides />
          </div>

          {/* results come first below 992px once there is one */}
          <div className={'col-lg-8' + (shown ? ' order-first order-lg-0' : '')} ref={results}>
            {error && <div className="alert alert-danger-custom"><i className="bi bi-exclamation-circle me-2"></i>{error}</div>}
            {shown ? <TimelineResult result={shown.result} inputs={shown.inputs} sample={shown.sample} /> : <TimelineEmpty />}
          </div>
        </div>
        <TimelineBackground />
      </div>
    </>
  );
}
