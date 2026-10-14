/* /forecast: the LightGBM forecaster, one isolate or a CSV of them
   (frontend/templates/resistance_forecast.html). */
import { useEffect, useRef, useState } from 'react';
import { apiPost, apiUpload, errorText } from '../lib/api';
import { usePageEffects, useTitle } from '../lib/pageEffects';
import ForecastForm from './forecast/ForecastForm';
import ForecastResult from './forecast/ForecastResult';
import { BatchForm, BatchResult } from './forecast/Batch';
import { ContextStrip, ForecastBackground, ForecastEmpty, ForecastHeader, MicGuide } from './forecast/static';
import type { BatchResult as Batch, ForecastInputs, ForecastResult as Result } from './forecast/types';

const BATCH_TIMEOUT_S = 120;
const BATCH_MAX_MB = 2;
const NAVBAR_PX = 64;   // layout.css: .main-content padding-top

type Shown =
  | { kind: 'none' }
  | { kind: 'result'; result: Result; inputs: ForecastInputs }
  | { kind: 'batch'; batch: Batch };

/** What /api/forecast/ is sent: the form's filled fields, never the Genome ID
    (it only drives the "fill from Genome ID" helper). */
export function forecastPayload(inputs: ForecastInputs): Record<string, string> {
  return Object.fromEntries(Object.entries(inputs)
    .filter(([k, v]) => v && v !== 'unknown' && k !== 'genome_id'));
}

export default function Forecast() {
  useTitle('AMR Resistance Forecasting');
  const [mode, setMode] = useState<'single' | 'batch'>('single');
  const [shown, setShown] = useState<Shown>({ kind: 'none' });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [root, setRoot] = useState<HTMLDivElement | null>(null);
  usePageEffects(root, [shown]);

  /* A new result or error opens where it can be seen, as the Flask page's
     reload did: the top of the results column, below the fixed navbar */
  const results = useRef<HTMLDivElement>(null);
  const [answered, setAnswered] = useState(0);
  useEffect(() => {
    const el = results.current;
    if (!answered || !el) return;
    const top = el.getBoundingClientRect().top;
    if (top < NAVBAR_PX || top > window.innerHeight / 2) {
      window.scrollTo({ top: Math.max(0, window.scrollY + top - NAVBAR_PX - 16), behavior: 'smooth' });
    }
  }, [answered]);

  async function predict(inputs: ForecastInputs) {
    setBusy(true);
    setError('');
    try {
      const result = await apiPost<Result>('forecast/', forecastPayload(inputs));
      setShown({ kind: 'result', result, inputs });
    } catch (e) {
      setShown({ kind: 'none' });
      setError(errorText(e));
    } finally {
      setBusy(false);
      setAnswered(n => n + 1);
    }
  }

  async function predictBatch(file: File) {
    setError('');
    if (file.size > BATCH_MAX_MB * 1024 * 1024) {
      setError(`The file is too large: the limit is ${BATCH_MAX_MB} MB.`);
      setAnswered(n => n + 1);
      return;
    }
    setBusy(true);
    const form = new FormData();
    form.append('file', file, file.name);
    try {
      setShown({ kind: 'batch', batch: await apiUpload<Batch>('forecast/batch/', form, { timeoutS: BATCH_TIMEOUT_S }) });
    } catch (e) {
      setShown({ kind: 'none' });
      setError(errorText(e));
    } finally {
      setBusy(false);
      setAnswered(n => n + 1);
    }
  }

  const tab = (which: 'single' | 'batch', icon: string, label: string) => (
    <li className="nav-item" role="presentation">
      <button className={'nav-link' + (mode === which ? ' active' : '')} type="button" role="tab"
              aria-selected={mode === which} onClick={() => setMode(which)}>
        <i className={`bi bi-${icon} me-1`}></i>{label}
      </button>
    </li>
  );

  return (
    <>
      <ForecastHeader />
      <div className="container-xl py-4" ref={setRoot}>
        <ContextStrip />
        <div className="row g-4">
          <div className="col-lg-4">
            <div className="form-card">
              <h5 className="form-card-title"><i className="bi bi-sliders me-2"></i>Prediction Parameters</h5>
              <ul className="nav nav-pills nav-custom mb-3" role="tablist">
                {tab('single', '1-circle', 'One isolate')}
                {tab('batch', 'filetype-csv', 'Upload CSV')}
              </ul>
              <div className="tab-content">
                {/* both stay mounted, so switching tabs keeps what was typed */}
                <div className={'tab-pane fade' + (mode === 'single' ? ' show active' : '')} id="singlePane" role="tabpanel">
                  <ForecastForm busy={busy} onSubmit={predict}
                                prediction={shown.kind === 'result' ? shown.result.prediction : undefined} />
                </div>
                <div className={'tab-pane fade' + (mode === 'batch' ? ' show active' : '')} id="batchPane" role="tabpanel">
                  <BatchForm busy={busy} onSubmit={predictBatch} />
                </div>
              </div>
            </div>
            <MicGuide />
          </div>

          {/* results come first below 992px once there is one */}
          <div className={'col-lg-8' + (shown.kind !== 'none' ? ' order-first order-lg-0' : '')} ref={results}>
            {error && <div className="alert alert-danger-custom"><i className="bi bi-exclamation-circle me-2"></i>{error}</div>}
            {shown.kind === 'batch' && <BatchResult batch={shown.batch} />}
            {shown.kind === 'result' && <ForecastResult result={shown.result} inputs={shown.inputs} />}
            {shown.kind === 'none' && <ForecastEmpty />}
          </div>
        </div>
        <ForecastBackground />
      </div>
    </>
  );
}
