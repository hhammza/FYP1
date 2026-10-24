/* The "One isolate" form on /forecast (forecast.js in the Flask frontend).

   Genus first: species and taxon ID offer only what belongs to that genus,
   from /api/vocabulary's `organisms` (backend/api/organisms.py), so 'coli'
   is offered under Escherichia and under Campylobacter, never mixed up. The
   MIC field suggests values recorded for the chosen drug and organism
   (/api/mic-values/). Everything offered is something the model knows. */
import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';
import { apiGet, errorText } from '../../lib/api';
import { useMetrics } from '../../lib/health';
import { capitalise, MIC_SIGNS, useAntibiotics, useVocabulary, type OrganismGenus } from '../../lib/vocab';
import { useToast } from '../../components/Toasts';
import GenomeInfo from './GenomeInfo';
import type { ForecastInputs, GenomeLookup, LabResult } from './types';

const GENOME_ID = /^\d{1,9}\.\d{1,9}$/;

const QUICK = ['Escherichia:coli', 'Pseudomonas:aeruginosa', 'Staphylococcus:aureus', 'Salmonella:enterica',
  'Acinetobacter:baumannii', 'Streptococcus:pneumoniae', 'Campylobacter:jejuni', 'Shigella:flexneri',
  'Mycobacterium:tuberculosis'];

const LEVEL_ALL = 'all organisms';

type Option = [value: string, label: string];

/** The species and taxon ID options for a genus (and species). */
export function organismOptions(g: OrganismGenus | undefined, species: string) {
  if (!g) return { species: [] as Option[], taxa: [] as Option[] };
  const sp = g.species.find(s => s.name === species);
  const ofSpecies = (s: OrganismGenus['species'][number]): Option[] =>
    s.taxon_ids.map(id => [String(id), `${id} · ${s.label}`]);
  return {
    // the genus is shown beside it, so the species name alone fits the narrow box
    species: g.species.map(s => [s.name, s.name] as Option),
    taxa: sp ? ofSpecies(sp)
             : g.species.flatMap(ofSpecies).concat(g.other_taxon_ids.map(o => [String(o.id), `${o.id} · ${o.label}`] as Option)),
  };
}

/** The warning above the button: what the result will actually represent. */
export function recognitionMessage(hasMic: boolean, hasOrg: boolean): string {
  if (!hasMic && !hasOrg) {
    return 'With no MIC value and no recognised organism, the result will be the '
      + 'population resistance rate for the selected drug — the same number for any isolate.';
  }
  if (!hasMic) {
    return 'Without an MIC value, the result reflects historical rates for this '
      + 'organism and drug, not this particular isolate.';
  }
  if (!hasOrg) {
    return 'No recognised organism: the MIC drives the result, with population '
      + 'rates standing in for the species.';
  }
  return '';
}

const pick = (items: Option[], wanted: string | number | undefined) =>
  items.find(([v]) => v.toLowerCase() === String(wanted ?? '').toLowerCase())?.[0] ?? '';

interface Props {
  busy: boolean;
  /** the prediction on the page, for the Genome ID box */
  prediction?: string;
  onSubmit: (inputs: ForecastInputs) => void;
}

export default function ForecastForm({ busy, prediction, onSubmit }: Props) {
  const m = useMetrics();
  const toast = useToast();
  const antibiotics = useAntibiotics('lgbm');
  const vocab = useVocabulary();
  const tree: OrganismGenus[] = useMemo(
    () => (vocab.state === 'ready' && vocab.data.lgbm?.organisms) || [], [vocab]);

  const [antibiotic, setAntibiotic] = useState('');
  const [genus, setGenus] = useState('');
  const [species, setSpecies] = useState('');
  const [taxon, setTaxon] = useState('');
  const [micSign, setMicSign] = useState('');
  const [micValue, setMicValue] = useState('');
  /** null: follow the model's validated threshold once /api/health/ gives it */
  const [threshold, setThreshold] = useState<string | null>(null);
  const [quick, setQuick] = useState('');
  const [genomeId, setGenomeId] = useState('');
  const [genome, setGenome] = useState<{ data?: GenomeLookup; error?: string } | null>(null);
  const [mic, setMic] = useState<{ values: string[]; hint: string }>({ values: [], hint: '' });

  const g = tree.find(x => x.genus === genus);
  const opts = organismOptions(g, species);
  const thr = threshold ?? String(m.lgbm.threshold ?? 0.5);

  useEffect(() => {
    if (antibiotics.state === 'failed') {
      toast('Could not load antibiotic list. Make sure the backend is running.', 'error', 'Connection Error');
    }
  }, [antibiotics.state, toast]);

  /* Choosing a genus or species: everything below it starts again */
  function chooseGenus(value: string, wantedSpecies?: string, wantedTaxon?: string | number) {
    const ng = tree.find(x => x.genus.toLowerCase() === value.toLowerCase());
    setGenus(ng ? ng.genus : '');
    const sp = pick(organismOptions(ng, '').species, wantedSpecies);
    setSpecies(sp);
    setTaxon(pick(organismOptions(ng, sp).taxa, wantedTaxon));
  }
  function chooseSpecies(value: string) {
    setSpecies(value);
    setTaxon('');
  }

  /* MIC suggestions for the chosen drug and organism */
  useEffect(() => {
    if (!antibiotic) { setMic({ values: [], hint: '' }); return; }
    const ctrl = new AbortController();
    const q = new URLSearchParams({ antibiotic, genus, species });
    apiGet<{ antibiotic: string; values: string[]; level: string | null }>(`mic-values/?${q}`, { signal: ctrl.signal })
      .then(d => {
        const who = d.level === 'species' && species ? `${genus} ${species}` : d.level === 'genus' ? genus : LEVEL_ALL;
        setMic({
          values: d.values || [],
          hint: d.values?.length
            ? `Suggested: MICs recorded in BV-BRC for ${who} and ${d.antibiotic}. Any value can be typed.`
            : 'No recorded MICs to suggest for this choice; any value can be typed.',
        });
      })
      .catch(() => { if (!ctrl.signal.aborted) setMic({ values: [], hint: '' }); });
    return () => ctrl.abort();
  }, [antibiotic, genus, species]);

  /* Fill from Genome ID: the organism to fill, the genome's lab results and
     whether the forecaster trained on it. The ID is never sent to the model. */
  const genomeRequest = useRef(0);
  function lookupGenome(fill: boolean, ab = antibiotic) {
    const id = genomeId.trim();
    if (!id) { setGenome(null); return; }
    if (!GENOME_ID.test(id)) {
      setGenome({ error: 'A BV-BRC Genome ID looks like 562.1234 (taxon ID, a dot, a number).' });
      return;
    }
    const mine = ++genomeRequest.current;
    apiGet<GenomeLookup>(`genome/${encodeURIComponent(id)}/?${new URLSearchParams({ antibiotic: ab })}`)
      .then(d => {
        if (mine !== genomeRequest.current) return;
        if (fill && d.organism?.genus) chooseGenus(d.organism.genus, d.organism.species, d.organism.taxon_id);
        setGenome({ data: d });
      })
      .catch(e => { if (mine === genomeRequest.current) setGenome({ error: errorText(e) }); });
  }

  function chooseAntibiotic(value: string) {
    setAntibiotic(value);
    // the lab result shown follows the chosen drug
    if (genomeId.trim() && genome?.data) lookupGenome(false, value);
  }

  function useMic(r: LabResult) {
    setMicValue(r.value || '');
    setMicSign(r.sign || '=');
  }

  function quickFill(value: string) {
    setQuick(value);
    if (!value) return;
    const [qg, qs] = value.split(':');
    chooseGenus(qg, qs);
  }

  const preview = recognitionMessage(micValue.trim() !== '', !!genus || !!taxon);

  function submit(e: FormEvent) {
    e.preventDefault();
    onSubmit({ antibiotic, genus: genus || 'unknown', species: species || 'unknown', taxon_id: taxon,
               mic_value: micValue, mic_sign: micSign, threshold: thr, genome_id: genomeId.trim() });
  }

  const select = (items: Option[], placeholder: string, value: string, onChange: (v: string) => void,
                  props: { id: string; name: string; disabled?: boolean }) => (
    <select className="form-select form-select-custom" value={value} onChange={e => onChange(e.target.value)} {...props}>
      <option value="">{placeholder}</option>
      {items.map(([v, label]) => <option key={v} value={v}>{label}</option>)}
    </select>
  );

  return (
    <form id="forecastForm" onSubmit={submit}>
      <div className="mb-3">
        <label className="form-label-custom" htmlFor="antibioticSelect">Antibiotic <span className="required">*</span>{' '}
          <i className="bi bi-info-circle text-muted ms-1" data-bs-toggle="tooltip" data-bs-placement="right"
             data-bs-title={`Select the antibiotic to test resistance against. Only the ${m.lgbm.antibiotics} antibiotics the model was trained on are listed.`}></i>
        </label>
        <select name="antibiotic" id="antibioticSelect" className="form-select form-select-custom" required
                value={antibiotic} onChange={e => chooseAntibiotic(e.target.value)}>
          {antibiotics.state === 'failed'
            ? <option value="" disabled>Failed to load — check backend</option>
            : <option value="">-- Select Antibiotic --</option>}
          {antibiotics.state === 'ready' && antibiotics.data.map(a => <option key={a} value={a}>{capitalise(a)}</option>)}
        </select>
      </div>

      <div className="mb-3" id="genomeFill">
        <label className="form-label-custom" htmlFor="genomeIdInput">Fill from Genome ID <span className="text-muted">(optional)</span>{' '}
          <i className="bi bi-info-circle text-muted ms-1" data-bs-toggle="tooltip" data-bs-placement="right"
             data-bs-title="A BV-BRC Genome ID, e.g. 106654.148. Fills genus, species and taxon ID, and shows the genome's laboratory results. The model does not use the ID itself."></i>
        </label>
        <div className="input-group">
          <input type="text" name="genome_id" id="genomeIdInput" className="form-control form-control-custom font-mono"
                 placeholder="e.g. 106654.148" value={genomeId} onChange={e => setGenomeId(e.target.value)}
                 onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); lookupGenome(true); } }}
                 inputMode="decimal" autoComplete="off" spellCheck="false" aria-describedby="genomeInfo" />
          <button type="button" className="btn btn-outline-custom" id="genomeFillBtn" onClick={() => lookupGenome(true)}>
            <i className="bi bi-search me-1"></i>Fill
          </button>
        </div>
        <div id="genomeInfo" className={'genome-info mt-2' + (genome ? '' : ' d-none')} role="status" aria-live="polite">
          {genome?.error && (
            <div className="genome-info-line genome-info-warn"><i className="bi bi-exclamation-circle me-1"></i>{genome.error}</div>
          )}
          {genome?.data && <GenomeInfo data={genome.data} antibiotic={antibiotic} prediction={prediction} onUseMic={useMic} />}
        </div>
      </div>

      <div className="row g-2 mb-3">
        <div className="col-6">
          <label className="form-label-custom" htmlFor="genusSelect">Genus{' '}
            <i className="bi bi-info-circle text-muted ms-1" data-bs-toggle="tooltip" data-bs-placement="right"
               data-bs-title="Bacterial genus. Only genera the model was trained on are listed; choosing one fills the species and taxon ID lists."></i>
          </label>
          {select(tree.map(x => [x.genus, x.genus]), '-- Any genus --', genus, v => chooseGenus(v), { id: 'genusSelect', name: 'genus' })}
          <div className="form-hint" id="genusHint">
            {vocab.state === 'loading' ? '' : tree.length ? `${tree.length} genera the model was trained on`
              : 'The organism lists need the backend; the result uses population rates without them.'}
          </div>
        </div>
        <div className="col-6">
          <label className="form-label-custom" htmlFor="speciesSelect">Species{' '}
            <i className="bi bi-info-circle text-muted ms-1" data-bs-toggle="tooltip" data-bs-placement="right"
               data-bs-title="Only the species of the chosen genus that the model was trained on."></i>
          </label>
          {select(opts.species, !g ? '-- Choose a genus first --' : opts.species.length ? '-- Any species --' : '-- None listed for this genus --',
                  species, chooseSpecies, { id: 'speciesSelect', name: 'species', disabled: opts.species.length === 0 })}
          <div className="form-hint" id="speciesHint">{g && opts.species.length ? `${opts.species.length} species of ${g.genus}` : ''}</div>
        </div>
      </div>

      <div className="mb-3">
        <label className="form-label-custom" htmlFor="taxonSelect">Taxon ID <span className="text-muted">(optional)</span>{' '}
          <i className="bi bi-info-circle text-muted ms-1" data-bs-toggle="tooltip" data-bs-placement="right"
             data-bs-title="NCBI Taxonomy ID of the organism (e.g. 562 for E. coli). Only IDs the model has a resistance rate for, for the chosen genus and species."></i>
        </label>
        {select(opts.taxa, !g ? '-- Choose a genus first --' : opts.taxa.length ? '-- None --' : '-- No ID for this choice --',
                taxon, setTaxon, { id: 'taxonSelect', name: 'taxon_id', disabled: opts.taxa.length === 0 })}
        <div className="form-hint" id="taxonHint">{opts.taxa.length ? 'Only IDs the model has a resistance rate for' : ''}</div>
      </div>

      <div className="row g-2 mb-3">
        <div className="col-5">
          <label className="form-label-custom" htmlFor="micSign">MIC Sign{' '}
            <i className="bi bi-info-circle text-muted ms-1" data-bs-toggle="tooltip" data-bs-placement="right"
               data-bs-title="Comparison operator for the MIC value. '=' is exact; '<=' means resistance not detected at this level; '>=' means MIC exceeded the measurable range."></i>
          </label>
          <select name="mic_sign" id="micSign" className="form-select form-select-custom" value={micSign}
                  onChange={e => setMicSign(e.target.value)}>
            <option value="">Select</option>
            {MIC_SIGNS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
        </div>
        <div className="col-7">
          <label className="form-label-custom" htmlFor="micInput">MIC Value (mg/L){' '}
            <i className="bi bi-info-circle text-muted ms-1" data-bs-toggle="tooltip" data-bs-placement="right"
               data-bs-title="Minimum Inhibitory Concentration in mg/L: the lowest antibiotic concentration that prevents visible bacterial growth."></i>
          </label>
          <input type="number" step="any" min="0" name="mic_value" id="micInput" className="form-control form-control-custom"
                 placeholder="e.g. 4.0" value={micValue} onChange={e => setMicValue(e.target.value)} list="micList" autoComplete="off" />
          <datalist id="micList">
            {mic.values.map(v => <option key={v} value={v}>{`${v} mg/L`}</option>)}
          </datalist>
        </div>
        <div className="col-12"><div className="form-hint" id="micHint">{mic.hint}</div></div>
      </div>

      <div className="mb-3">
        <label className="form-label-custom" htmlFor="threshSlider">Decision Threshold: <span id="threshVal">{thr}</span>{' '}
          <i className="bi bi-info-circle text-muted ms-1" data-bs-toggle="tooltip" data-bs-placement="right"
             data-bs-title={`Probability cutoff for Resistant classification. Lower values catch more resistance (higher recall) but increase false alarms. Starts at the model's validated threshold, ${m.lgbm.threshold || 'not measured'}: ${m.lgbm.threshold_rule || 'no rule recorded'}.`}></i>
        </label>
        <input type="range" name="threshold" className="form-range" min="0.1" max="0.9" step="0.01"
               value={thr} id="threshSlider" onChange={e => setThreshold(e.target.value)}
               aria-label="Decision Threshold" aria-valuemin={0.1} aria-valuemax={0.9} aria-valuenow={Number(thr)} />
        <div className="d-flex justify-content-between"><small className="text-muted">0.1 (Liberal)</small><small className="text-muted">0.9 (Conservative)</small></div>
      </div>

      <div className="mb-3">
        <label className="form-label-custom" htmlFor="orgSelect">Quick Select Organism{' '}
          <i className="bi bi-info-circle text-muted ms-1" data-bs-toggle="tooltip" data-bs-placement="right"
             data-bs-title="Pre-fills Genus and Species for common clinical pathogens. You can then change any of the lists."></i>
        </label>
        <select className="form-select form-select-custom" id="orgSelect" value={quick} onChange={e => quickFill(e.target.value)}>
          <option value="">-- Organisms the model was trained on --</option>
          {QUICK.map(q => <option key={q} value={q}>{q.replace(':', ' ')}</option>)}
        </select>
        <div className="form-hint">Fills the genus and species lists above</div>
      </div>

      <div className={'alert alert-warning-custom mb-3' + (preview ? '' : ' d-none')} id="evidencePreview" role="status" aria-live="polite">
        <i className="bi bi-info-circle me-2"></i><span id="evidencePreviewText">{preview}</span>
      </div>

      <button type="submit" className="btn btn-primary-custom w-100 btn-lg" id="predictBtn" disabled={busy}>
        {busy
          ? <><span className="spinner-border spinner-border-sm me-2" role="status"></span>Processing…</>
          : <><i className="bi bi-cpu me-2"></i>Predict Resistance</>}
      </button>
    </form>
  );
}
