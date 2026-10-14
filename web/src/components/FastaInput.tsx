/* A genome for /predict or /timeline: an uploaded FASTA file or a pasted
   sequence, with a sample to paste (switchTab / loadSampleFasta in the old
   prediction.js and timeline.js). */
import FileDrop from './FileDrop';

export type FastaTab = 'file' | 'text';

export interface FastaValue {
  tab: FastaTab;
  file: File | null;
  text: string;
}

export const EMPTY_FASTA: FastaValue = { tab: 'file', file: null, text: '' };

/** What will be sent: the file when one is chosen, else the pasted text (as the Flask pages did). */
export function chosenGenome(v: FastaValue): { file: File } | { text: string } | null {
  if (v.file) return { file: v.file };
  if (v.text.trim()) return { text: v.text.trim() };
  return null;
}

interface Props {
  /** '' on /predict, '2' on /timeline (the element IDs of the Flask pages) */
  suffix: '' | '2';
  value: FastaValue;
  onChange: (v: FastaValue) => void;
  accept: string;
  fileTooltip: string;
  textTooltip: string;
  placeholder: string;
  rows: number;
  sample: string;
  missingText: string;
  showMissing: boolean;
  compact?: boolean;
}

export default function FastaInput({ suffix, value, onChange, accept, fileTooltip, textTooltip, placeholder, rows,
                                     sample, missingText, showMissing, compact }: Props) {
  const tab = (which: FastaTab, icon: string, label: string) => (
    <li className="nav-item">
      <button className={'nav-link' + (value.tab === which ? ' active' : '')} type="button"
              onClick={() => onChange({ ...value, tab: which })}>
        <i className={`bi bi-${icon} me-1`}></i>{label}
      </button>
    </li>
  );

  return (
    <>
      <ul className="nav nav-pills nav-custom mb-3" id={`fastaTab${suffix}`}>
        {tab('file', 'file-earmark-arrow-up', 'Upload FASTA')}
        {tab('text', 'code', 'Paste Sequence')}
      </ul>

      <div id={`fileTab${suffix}`} className={(compact ? '' : 'tab-content-custom ') + 'mb-3' + (value.tab === 'file' ? '' : ' d-none')}>
        <label className="form-label-custom" htmlFor={`fastaFile${suffix}`}>FASTA File <span className="required">*</span>{' '}
          <i className="bi bi-info-circle text-muted ms-1" data-bs-toggle="tooltip" data-bs-placement="right" data-bs-title={fileTooltip}></i>
        </label>
        <FileDrop id={`fastaFile${suffix}`} name="fasta_file" accept={accept} file={value.file} compact={compact}
                  onFile={file => onChange({ ...value, file })} />
        {!compact && <div className="form-hint">Accepts .fasta, .fa, .fna formats; a complete assembly (at least 100K bp), read in full</div>}
      </div>

      <div id={`textTab${suffix}`} className={(compact ? '' : 'tab-content-custom ') + 'mb-3' + (value.tab === 'text' ? '' : ' d-none')}>
        <label className="form-label-custom" htmlFor={`fastaText${suffix}`}>FASTA Sequence <span className="required">*</span>{' '}
          <i className="bi bi-info-circle text-muted ms-1" data-bs-toggle="tooltip" data-bs-placement="right" data-bs-title={textTooltip}></i>
        </label>
        <textarea name="fasta_text" id={`fastaText${suffix}`} className="form-control form-control-custom mono-font"
                  rows={rows} placeholder={placeholder} value={value.text} onChange={e => onChange({ ...value, text: e.target.value })}></textarea>
        <div className={'d-flex mt-1 ' + (compact ? 'justify-content-end' : 'justify-content-between')}>
          {!compact && <small className="form-hint">Paste your FASTA sequence here</small>}
          <button type="button" className="btn btn-link btn-sm p-0" onClick={() => onChange({ ...value, tab: 'text', text: sample })}>
            Load Sample
          </button>
        </div>
      </div>

      <div id={`fastaError${suffix}`} className={'alert alert-danger-custom mb-3' + (showMissing ? '' : ' d-none')} role="alert" aria-live="polite">
        <i className="bi bi-exclamation-circle me-2"></i>{missingText}
      </div>
    </>
  );
}
