/* /timeline's "ML trend forecast" mode: the timeline ML model on its own
   (POST /api/timeline/forecast/), from an organism and an antibiotic, no genome. */
import { useEffect, useState, type FormEvent } from 'react';
import AntibioticOptions from '../../components/AntibioticOptions';
import { useVocabulary } from '../../lib/vocab';
import { forecastGenera } from './TimelineForm';

export interface TrendSubmit {
  antibiotic: string;
  genus: string;
  years_ahead: string;
}

interface Props {
  busy: boolean;
  onSubmit: (s: TrendSubmit) => void;
}

export default function TrendForecastForm({ busy, onSubmit }: Props) {
  const vocab = useVocabulary();
  const byDrug = vocab.state === 'ready' ? vocab.data.timeline?.genera : undefined;
  const drugs = byDrug ? Object.keys(byDrug).sort() : [];
  const [antibiotic, setAntibiotic] = useState('');
  const [genus, setGenus] = useState('');
  const [years, setYears] = useState('5');
  const genera = forecastGenera(byDrug, antibiotic);

  // a genus with no history for the newly chosen drug is let go
  useEffect(() => { if (genus && !genera.includes(genus)) setGenus(''); }, [genus, genera]);

  function submit(e: FormEvent) {
    e.preventDefault();
    onSubmit({ antibiotic, genus, years_ahead: years });
  }

  return (
    <form id="trendForm" onSubmit={submit}>
      <p className="small text-muted">
        A LightGBM model trained on BV-BRC laboratory results forecasts the yearly share of resistant isolates.
        No genome needed.
      </p>
      <div className="mb-3">
        <label className="form-label-custom" htmlFor="trendAntibiotic">Antibiotic <span className="required">*</span></label>
        <select id="trendAntibiotic" className="form-select form-select-custom" required value={antibiotic}
                onChange={e => setAntibiotic(e.target.value)} disabled={!drugs.length}>
          <option value="">{vocab.state === 'loading' ? 'Loading…'
            : drugs.length ? '-- Select Antibiotic --' : 'Failed to load — check backend'}</option>
          <AntibioticOptions names={drugs} />
        </select>
        <div className="form-hint">{drugs.length ? `${drugs.length} antibiotics have yearly lab history` : ''}</div>
      </div>

      <div className="mb-3">
        <label className="form-label-custom" htmlFor="trendGenus">Organism (genus) <span className="required">*</span></label>
        <select id="trendGenus" className="form-select form-select-custom" required value={genus}
                onChange={e => setGenus(e.target.value)} disabled={!genera.length}>
          <option value="">{antibiotic ? '-- Select Organism --' : '-- Choose an antibiotic first --'}</option>
          {genera.map(g => <option key={g} value={g}>{g}</option>)}
        </select>
        <div className="form-hint">{antibiotic && genera.length ? `${genera.length} genera have history for ${antibiotic}` : ''}</div>
      </div>

      <div className="mb-3">
        <label className="form-label-custom" htmlFor="trendYears">Years ahead: <span>{years}</span></label>
        <input type="range" id="trendYears" className="form-range" min="1" max="10" step="1" value={years}
               onChange={e => setYears(e.target.value)} aria-label="Years ahead" />
        <div className="d-flex justify-content-between">
          <small className="text-muted">1 year</small>
          <small className="text-muted">10 years</small>
        </div>
        <div className="form-hint">The band widens with each year: the far future is less certain.</div>
      </div>

      <button type="submit" className="btn btn-primary-custom w-100 btn-lg" disabled={busy || !antibiotic || !genus}>
        {busy
          ? <><span className="spinner-border spinner-border-sm me-2" role="status"></span>Forecasting…</>
          : <><i className="bi bi-graph-up-arrow me-2"></i>Forecast Resistance Trend</>}
      </button>
    </form>
  );
}
