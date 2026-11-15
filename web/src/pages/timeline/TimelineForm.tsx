/* The form on /timeline: the timeline ML model (POST /api/timeline/, format §8).
   An antibiotic, the organism (chosen from the genera with yearly lab history
   for that drug, or identified from an uploaded genome) and how many years to
   look ahead. */
import { useEffect, useState, type FormEvent } from 'react';
import AntibioticOptions from '../../components/AntibioticOptions';
import BioIcon from '../../components/BioIcon';
import FastaInput, { chosenGenome, EMPTY_FASTA, type FastaValue } from '../../components/FastaInput';
import { useVocabulary } from '../../lib/vocab';

export type OrganismFrom = 'choose' | 'genome';

export interface TimelineSubmit {
  antibiotic: string;
  years_ahead: string;
  /** a chosen genus, or a genome whose genus the backend identifies */
  organism: { genus: string } | { genome: { file: File } | { text: string } };
}

/** The genera the timeline ML model forecasts for a drug (format §8). */
export function forecastGenera(genera: Record<string, string[]> | undefined, antibiotic: string): string[] {
  return (genera && antibiotic && genera[antibiotic.toLowerCase()]) || [];
}

interface Props {
  busy: boolean;
  onSubmit: (s: TimelineSubmit) => void;
}

export default function TimelineForm({ busy, onSubmit }: Props) {
  const vocab = useVocabulary();
  const byDrug = vocab.state === 'ready' ? vocab.data.timeline?.genera : undefined;
  const drugs = byDrug ? Object.keys(byDrug).sort() : [];
  const [antibiotic, setAntibiotic] = useState('');
  const [from, setFrom] = useState<OrganismFrom>('choose');
  const [genus, setGenus] = useState('');
  const [years, setYears] = useState('5');
  const [fasta, setFasta] = useState<FastaValue>(EMPTY_FASTA);
  const [missing, setMissing] = useState(false);
  const genera = forecastGenera(byDrug, antibiotic);

  // a genus with no history for the newly chosen drug is let go
  useEffect(() => { if (genus && !genera.includes(genus)) setGenus(''); }, [genus, genera]);

  function submit(e: FormEvent) {
    e.preventDefault();
    if (from === 'choose') {
      onSubmit({ antibiotic, years_ahead: years, organism: { genus } });
      return;
    }
    const genome = chosenGenome(fasta);
    if (!genome) {
      setMissing(true);
      document.getElementById(fasta.tab === 'text' ? 'fastaText2' : 'fastaFile2')?.focus();
      return;
    }
    onSubmit({ antibiotic, years_ahead: years, organism: { genome } });
  }

  const fromTab = (which: OrganismFrom, icon: string, label: string) => (
    <li className="nav-item">
      <button className={'nav-link' + (from === which ? ' active' : '')} type="button"
              aria-pressed={from === which} onClick={() => setFrom(which)}>
        <i className={`bi bi-${icon} me-1`}></i>{label}
      </button>
    </li>
  );

  return (
    <form id="timelineForm" onSubmit={submit}>
      <p className="small text-muted">
        A LightGBM model trained on BV-BRC laboratory results forecasts the yearly share of resistant isolates
        for one organism and one antibiotic.
      </p>
      <div className="mb-3">
        <label className="form-label-custom" htmlFor="antibioticSelect">Antibiotic <span className="required">*</span></label>
        <select id="antibioticSelect" className="form-select form-select-custom" required value={antibiotic}
                onChange={e => setAntibiotic(e.target.value)} disabled={!drugs.length}>
          <option value="">{vocab.state === 'loading' ? 'Loading…'
            : drugs.length ? '-- Select Antibiotic --' : 'Failed to load — check backend'}</option>
          <AntibioticOptions names={drugs} />
        </select>
        <div className="form-hint">{drugs.length ? `${drugs.length} antibiotics have yearly lab history` : ''}</div>
      </div>

      <div className="mb-3">
        <span className="form-label-custom d-block">Organism <span className="required">*</span></span>
        <ul className="nav nav-pills nav-custom mb-2" aria-label="Where the organism comes from">
          {fromTab('choose', 'list-ul', 'Choose it')}
          {fromTab('genome', 'file-earmark-binary', 'From a genome')}
        </ul>
        {from === 'choose' ? (
          <>
            <label className="visually-hidden" htmlFor="genusSelect">Organism (genus)</label>
            <select id="genusSelect" className="form-select form-select-custom" required value={genus}
                    onChange={e => setGenus(e.target.value)} disabled={!genera.length}>
              <option value="">{antibiotic ? '-- Select Organism --' : '-- Choose an antibiotic first --'}</option>
              {genera.map(g => <option key={g} value={g}>{g}</option>)}
            </select>
            <div className="form-hint">{antibiotic && genera.length ? `${genera.length} genera have history for ${antibiotic}` : ''}</div>
          </>
        ) : (
          <>
            <div className="form-hint mb-2">The genus is identified from the genome's 6-mer profile. It needs a
              complete assembly of at least 100 kb.</div>
            <FastaInput suffix="2" compact value={fasta} onChange={v => { setFasta(v); setMissing(false); }}
                        accept=".fasta,.fa,.fna" rows={5}
                        fileTooltip="Upload a genome assembly (.fasta, .fa, .fna). Only its genus is used: the forecast is for that genus and the chosen antibiotic."
                        textTooltip="Paste a complete genome assembly in FASTA format. Only its genus is used."
                        placeholder={'>genome_header\nATGCATGCATGCATGCATGC...'} showMissing={missing}
                        missingText="Upload a FASTA file or paste a sequence, or choose the organism instead." />
          </>
        )}
      </div>

      <div className="mb-3">
        <label className="form-label-custom" htmlFor="yearsSlider">Years ahead: <span>{years}</span></label>
        <input type="range" id="yearsSlider" className="form-range" min="1" max="10" step="1" value={years}
               onChange={e => setYears(e.target.value)} aria-label="Years ahead" />
        <div className="d-flex justify-content-between">
          <small className="text-muted">1 year</small>
          <small className="text-muted">10 years</small>
        </div>
        <div className="form-hint">The band widens with each year: the far future is less certain.</div>
      </div>

      <button type="submit" className="btn btn-primary-custom w-100 btn-lg"
              disabled={busy || !antibiotic || (from === 'choose' && !genus)}>
        {busy
          ? <><span className="spinner-border spinner-border-sm me-2" role="status"></span>Forecasting…</>
          : <><BioIcon icon="bi-graph-up-arrow" className="me-2" />Forecast Resistance Trend</>}
      </button>
    </form>
  );
}
