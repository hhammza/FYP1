/* /predict: resistance from a complete genome, by the served genome model
   (frontend/templates/resistance_prediction.html). /predict/sample shows the
   agreed sample response, on a development run only, as the Flask site did. */
import { useEffect, useRef, useState } from 'react';
import { apiPost, apiUpload, errorText, PREDICT_TIMEOUT_S } from '../lib/api';
import { usePageEffects, useTitle } from '../lib/pageEffects';
import PredictForm, { type PredictSubmit } from './predict/PredictForm';
import PredictResult from './predict/PredictResult';
import { ContextStrip, PipelineGuides, PredictBackground, PredictEmpty, PredictHeader } from './predict/static';
import type { PredictInputs, PredictResult as Result } from './predict/types';

const MAX_FASTA_MB = 20;      // settings.MAX_FASTA_BYTES in the backend
const NAVBAR_PX = 64;

type Shown = { result: Result; inputs: PredictInputs; sample?: boolean } | null;

/** The agreed sample response (progress/formats/), for /predict/sample on a dev run. */
async function loadSample(): Promise<Result | null> {
  if (!import.meta.env.DEV) return null;
  const mod = await import('../../../progress/formats/genome_response.sample.json');
  const { _comment, ...result } = mod.default as Result & { _comment?: string };
  void _comment;
  return result;
}

export default function Predict({ sample = false }: { sample?: boolean }) {
  useTitle('Resistance Prediction');
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
      if (r) setShown({ result: r, inputs: { antibiotic: r.antibiotic, threshold: '' }, sample: true });
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

  async function predict({ antibiotic, threshold, genome }: PredictSubmit) {
    setError('');
    const inputs = { antibiotic, threshold };
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
        if (threshold) form.append('threshold', threshold);
        result = await apiUpload<Result>('predict/', form, { timeoutS: PREDICT_TIMEOUT_S });
      } else {
        // the threshold as typed: the backend checks it and answers a bad value with a 400
        result = await apiPost<Result>('predict/', { fasta_text: genome.text, antibiotic, ...(threshold ? { threshold } : {}) },
                                       { timeoutS: PREDICT_TIMEOUT_S });
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
      <PredictHeader />
      <div className="container-xl py-4" ref={setRoot}>
        <ContextStrip />
        <div className="row g-4">
          <div className="col-lg-5">
            <div className="form-card">
              <h5 className="form-card-title"><i className="bi bi-upload me-2"></i>Genome Input</h5>
              <PredictForm busy={busy} onSubmit={predict} initialAntibiotic={sample ? 'ciprofloxacin' : ''} />
            </div>
            <PipelineGuides />
          </div>

          {/* results come first below 992px once there is one */}
          <div className={'col-lg-7' + (shown ? ' order-first order-lg-0' : '')} ref={results}>
            {error && <div className="alert alert-danger-custom"><i className="bi bi-exclamation-circle me-2"></i>{error}</div>}
            {shown ? <PredictResult result={shown.result} inputs={shown.inputs} sample={shown.sample} /> : <PredictEmpty />}
          </div>
        </div>
        <PredictBackground />
      </div>
    </>
  );
}
