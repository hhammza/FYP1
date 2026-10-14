/* What "Fill from Genome ID" found: the organism, whether the forecaster
   trained on this genome, and its lab result for the chosen drug beside the
   model's call (showGenome in the old forecast.js). */
import { Link } from 'react-router';
import type { GenomeLookup, LabResult } from './types';

function Line({ icon, cls, children }: { icon: string; cls?: string; children: React.ReactNode }) {
  return <div className={'genome-info-line' + (cls ? ' ' + cls : '')}><i className={`bi bi-${icon} me-1`}></i>{children}</div>;
}

export function micText(r: LabResult): string {
  if (!r.value) return '';
  const sign = r.sign && r.sign !== '=' ? r.sign + ' ' : '';
  if (r.is_mic || (r.unit || '').toLowerCase() === 'mg/l') return ` (MIC ${sign}${r.value} mg/L)`;
  return ` (${r.value}${r.unit ? ' ' + r.unit : ''}, not a MIC)`;
}

/** true / false when the model's call and the lab can be compared, else null.
    The model has two classes, so a lab "Intermediate" counts as Resistant. */
export function agrees(prediction: string | undefined, phenotype: string | undefined): boolean | null {
  if (!prediction || !phenotype) return null;
  return prediction === (phenotype === 'Intermediate' ? 'Resistant' : phenotype);
}

interface Props {
  data: GenomeLookup;
  antibiotic: string;
  /** the prediction on the page, if any */
  prediction?: string;
  onUseMic: (r: LabResult) => void;
}

export default function GenomeInfo({ data: d, antibiotic, prediction, onUseMic }: Props) {
  const o = d.organism || {};
  const filled = [o.genus, o.species, o.taxon_id].filter(Boolean).length;
  const role = d.models?.forecast;
  const labs = d.lab_for_antibiotic || [];
  const r = labs[0];
  const agree = r ? agrees(prediction, r.phenotype) : null;
  const n = (d.lab_results || []).length;

  return (
    <>
      <Line icon="bacteria">
        {(o.name || `Taxon ${d.taxon_id}`) + (filled ? '' : ': not an organism the model knows, so nothing was filled')}
      </Line>
      {role && role.role === 'train' && (
        <Line icon="exclamation-triangle" cls="genome-info-warn">
          The forecaster was trained on this genome, so its prediction will look better than on a new genome.
        </Line>
      )}
      {role && role.role === 'test' && (
        <Line icon="check-circle" cls="genome-info-ok">Not used in training: a fair test of the forecaster.</Line>
      )}
      {role && role.role !== 'train' && role.role !== 'test' && (
        <Line icon="dash-circle">Not in the forecaster's data.</Line>
      )}
      {antibiotic && r ? (
        <Line icon="clipboard2-pulse">
          {`Lab result for ${antibiotic}: ${r.phenotype || 'no phenotype recorded'}${micText(r)}`
            + (r.method ? `, ${r.method}` : '') + (labs.length > 1 ? ` (${labs.length} results)` : '')
            + (agree === null ? '' : agree ? '. The model agrees.' : `. The model said ${prediction}.`)}
          {r.is_mic && r.value && (
            <button type="button" className="btn btn-link btn-sm p-0 ms-1 genome-use-mic" onClick={() => onUseMic(r)}>
              Use this MIC
            </button>
          )}
        </Line>
      ) : (
        <Line icon="clipboard2">
          {n ? `${n} lab result${n === 1 ? '' : 's'} for this genome, ${antibiotic ? 'none for ' + antibiotic : 'choose an antibiotic to see one'}.`
             : 'No laboratory result for this genome in our data.'}
        </Line>
      )}
      <Link className="genome-info-link" to={d.genes_url}>Resistance genes for this genome</Link>
    </>
  );
}
