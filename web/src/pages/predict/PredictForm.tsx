/* The genome form on /predict (prediction.js in the Flask frontend). */
import { useEffect, useState, type FormEvent } from 'react';
import FastaInput, { chosenGenome, EMPTY_FASTA, type FastaValue } from '../../components/FastaInput';
import { useToast } from '../../components/Toasts';
import { useMetrics } from '../../lib/health';
import { capitalise, useAntibiotics } from '../../lib/vocab';

/* A short E. coli snippet: the model refuses it (a complete genome is at
   least 100,000 bp), which shows what a refusal looks like */
export const SAMPLE_FASTA = `>sample_genome_E_coli_K12
ATGAAACGCATTAGCACCACCATTACCACCACCATCACCATTACCACAGGTAACGGTGCGGGCTGACGCGTACAGGAAACACAGAAAAAAGCCCGCACCTGACAGTGCGGGCTTTTTTTTTCGACCAAAGGTAACGAGGTAACAACCATGCGAGTGTTGAAGTTCGGCGGTACATCAGTGGCAAATGCAGAACGTTTTCTGCGCGTTGTTACGCGCATTTTCTGATATTCG
GCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGC
ATGAAACGCATTAGCACCACCATTACCACCACCATCACCATTACCACAGGTAACGGTGCGGGCTGACGCGTACAGGAAACACAGAAAAAAGCCCGCACCTGACAGTGCGGGCTTTTTTTTTCGACCAAAGGTAACGAGGT`;

export interface PredictSubmit {
  antibiotic: string;
  threshold: string;
  genome: { file: File } | { text: string };
}

interface Props {
  busy: boolean;
  /** the antibiotic to start on (the sample preview) */
  initialAntibiotic?: string;
  onSubmit: (s: PredictSubmit) => void;
}

export default function PredictForm({ busy, initialAntibiotic = '', onSubmit }: Props) {
  const m = useMetrics();
  const toast = useToast();
  const antibiotics = useAntibiotics('kmer');
  const [antibiotic, setAntibiotic] = useState(initialAntibiotic);
  const [threshold, setThreshold] = useState<string | null>(null);
  const [fasta, setFasta] = useState<FastaValue>(EMPTY_FASTA);
  const [missing, setMissing] = useState(false);
  const thr = threshold ?? String(m.kmer.threshold ?? 0.5);

  useEffect(() => {
    if (antibiotics.state === 'failed') {
      toast('Could not load antibiotic list. Make sure the backend is running.', 'error', 'Connection Error');
    }
  }, [antibiotics.state, toast]);

  function change(v: FastaValue) {
    setFasta(v);
    setMissing(false);
  }

  function submit(e: FormEvent) {
    e.preventDefault();
    const genome = chosenGenome(fasta);
    if (!genome) {
      setMissing(true);
      document.getElementById(fasta.tab === 'text' ? 'fastaText' : 'fastaFile')?.focus();
      return;
    }
    onSubmit({ antibiotic, threshold: thr, genome });
  }

  return (
    <form id="predictForm" onSubmit={submit}>
      <div className="mb-3">
        <label className="form-label-custom" htmlFor="antibioticSelect">Antibiotic <span className="required">*</span>{' '}
          <i className="bi bi-info-circle text-muted ms-1" data-bs-toggle="tooltip" data-bs-placement="right"
             data-bs-title={`Select the antibiotic to predict resistance against. The list holds only the ${m.kmer.antibiotics} antibiotics the model was trained on.`}></i>
        </label>
        <select name="antibiotic" id="antibioticSelect" className="form-select form-select-custom" required
                value={antibiotic} onChange={e => setAntibiotic(e.target.value)}>
          {antibiotics.state === 'failed'
            ? <option value="" disabled>Failed to load — check backend</option>
            : <option value="">-- Select Antibiotic --</option>}
          {antibiotics.state === 'ready' && antibiotics.data.map(a => <option key={a} value={a}>{capitalise(a)}</option>)}
        </select>
      </div>

      <FastaInput suffix="" value={fasta} onChange={change} accept=".fasta,.fa,.fna,.ffn,.faa" rows={8}
                  fileTooltip="Upload a whole-genome assembly (.fasta, .fa, .fna). The model reads the whole genome (at least 100,000 bp; a partial or plasmid-only file is refused) and uses its 4-mer frequencies, counted within each contig."
                  textTooltip="Paste a FASTA sequence starting with a '>' header line. Non-ATCG bases are removed automatically before k-mer extraction."
                  placeholder={'>genome_id description\nATGCATGCATGCATGCATGCATGCATGCATGC\nGCATGCATGCATGCATGCATGCATGCATGCAT\n...'}
                  sample={SAMPLE_FASTA} showMissing={missing}
                  missingText="Upload a FASTA file or paste a sequence before predicting." />

      <div className="mb-4">
        <label className="form-label-custom" htmlFor="threshSlider2">Decision Threshold: <span id="threshVal2">{thr}</span>{' '}
          <i className="bi bi-info-circle text-muted ms-1" data-bs-toggle="tooltip" data-bs-placement="right"
             data-bs-title={`Probability cutoff for Resistant classification. Starts at the threshold the model was evaluated at, ${m.kmer.threshold || 'not measured'}: ${m.kmer.threshold_rule || 'no rule recorded'}.`}></i>
        </label>
        <input type="range" name="threshold" className="form-range" min="0.1" max="0.9" step="0.01"
               value={thr} id="threshSlider2" onChange={e => setThreshold(e.target.value)}
               aria-label="Decision Threshold" aria-valuemin={0.1} aria-valuemax={0.9} aria-valuenow={Number(thr)} />
        <div className="d-flex justify-content-between"><small className="text-muted">0.1 (Sensitive)</small><small className="text-muted">0.9 (Specific)</small></div>
      </div>

      <button type="submit" className="btn btn-primary-custom btn-success-custom w-100 btn-lg" disabled={busy}>
        {busy
          ? <><span className="spinner-border spinner-border-sm me-2" role="status"></span>Analysing the genome…</>
          : <><i className="bi bi-dna me-2"></i>Predict Resistance</>}
      </button>
      <div className={'form-hint text-center mt-2' + (busy ? '' : ' d-none')} role="status" aria-live="polite">
        <i className="bi bi-hourglass-split me-1"></i>A complete genome can take up to a minute. Please keep this page open.
      </div>
    </form>
  );
}
