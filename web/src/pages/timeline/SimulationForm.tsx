/* /timeline's what-if tab: the simulation form (POST /api/timeline/simulate/).
   A genome, an antibiotic and a number of weeks; not a trained model. */
import { useEffect, useState, type FormEvent } from 'react';
import FastaInput, { chosenGenome, EMPTY_FASTA, type FastaValue } from '../../components/FastaInput';
import { useToast } from '../../components/Toasts';
import { useAntibiotics } from '../../lib/vocab';
import AntibioticSelect from '../../components/AntibioticSelect';
import BioIcon from '../../components/BioIcon';

export const SAMPLE_GENOME = `>sample_Ecoli_genome
ATGAAACGCATTAGCACCACCATTACCACCACCATCACCATTACCACAGGTAACGGTGCGGGCTGACGCGTACAGGAAACACAGAAAAAAGCCCGCACCTGACAGTGCGGGCTTTTTTTTTCGACCAAAGGTAACGAGGTAACAACCATGCGAGTGTTGAAGTTCGGCGGTACATCAGTGGCAAATGCAGAACGTTTTCTGCGCGTTGTTACGCGCATTTTCTGATATTCGATTCGCATCATTTTCGGTCGGGTATCGCGGCGTTTGCTAAAAAACGTCAGCGTTTGCAGTTTTCGCTGAAACAGATGCGTATTTCGGTTTATCTCAAAAGTTCGTTTAGTAACAACGATGCGTAAAGCAGCATTAACGAAACAGTTTCAACGTTTGGCTGAAACGCAGTTTAAAGCTCAACGCAACAGTTTGCAAACGCAGCGCAATTTAAACAAGCGTTTGCAGAAACG`;

export interface SimulationSubmit {
  antibiotic: string;
  n_weeks: string;
  genome: { file: File } | { text: string };
}

interface Props {
  busy: boolean;
  initial?: { antibiotic: string; n_weeks: string };
  onSubmit: (s: SimulationSubmit) => void;
}

export default function SimulationForm({ busy, initial, onSubmit }: Props) {
  const toast = useToast();
  const antibiotics = useAntibiotics('kmer');
  const [antibiotic, setAntibiotic] = useState(initial?.antibiotic ?? '');
  const [weeks, setWeeks] = useState(initial?.n_weeks ?? '8');
  const [fasta, setFasta] = useState<FastaValue>(EMPTY_FASTA);
  const [missing, setMissing] = useState(false);

  useEffect(() => { if (initial) { setAntibiotic(initial.antibiotic); setWeeks(initial.n_weeks); } }, [initial]);

  useEffect(() => {
    if (antibiotics.state === 'failed') {
      toast('Could not load antibiotic list. Make sure the backend is running.', 'error', 'Connection Error');
    }
  }, [antibiotics.state, toast]);

  function submit(e: FormEvent) {
    e.preventDefault();
    const genome = chosenGenome(fasta);
    if (!genome) {
      setMissing(true);
      document.getElementById(fasta.tab === 'text' ? 'fastaText3' : 'fastaFile3')?.focus();
      return;
    }
    onSubmit({ antibiotic, n_weeks: weeks, genome });
  }

  return (
    <form id="simulationForm" onSubmit={submit}>
      <div className="mb-3">
        <label className="form-label-custom" htmlFor="simAntibiotic">Antibiotic <span className="required">*</span>{' '}
          <i className="bi bi-info-circle text-muted ms-1" data-bs-toggle="tooltip" data-bs-placement="right"
             data-bs-title="Select the antibiotic to simulate. Each has a hand-set growth rate and peak resistance; the curve shape has been checked against published lab and hospital data."></i>
        </label>
        <AntibioticSelect id="simAntibiotic" name="antibiotic" required value={antibiotic} onChange={setAntibiotic}
                          names={antibiotics.state === 'ready' ? antibiotics.data : []}
                          placeholder={antibiotics.state === 'failed' ? 'Failed to load — check backend' : '-- Select Antibiotic --'} />
      </div>

      <div className="mb-3">
        <label className="form-label-custom" htmlFor="weeksSlider">Simulation Weeks: <span id="weeksVal">{weeks}</span>{' '}
          <i className="bi bi-info-circle text-muted ms-1" data-bs-toggle="tooltip" data-bs-placement="right"
             data-bs-title="How many weeks to simulate. 8 weeks covers a typical treatment course; 24 weeks shows long-term population dynamics. The 50% line marks the treatment failure threshold."></i>
        </label>
        <input type="range" name="n_weeks" className="form-range" min="2" max="24" step="1"
               value={weeks} id="weeksSlider" onChange={e => setWeeks(e.target.value)}
               aria-label="Simulation Weeks" aria-valuemin={2} aria-valuemax={24} aria-valuenow={Number(weeks)} />
        <div className="d-flex justify-content-between">
          <small className="text-muted">2 weeks</small>
          <small className="text-muted">24 weeks</small>
        </div>
      </div>

      <FastaInput suffix="3" compact value={fasta} onChange={v => { setFasta(v); setMissing(false); }} accept=".fasta,.fa,.fna" rows={7}
                  fileTooltip="Upload a genome assembly (.fasta, .fa, .fna). Its GC content sets the starting resistant fraction for the simulation. Required unless you paste a sequence instead."
                  textTooltip="Paste a FASTA sequence to set the simulation baseline. GC content is extracted and used to set initial mutation pressure. Required unless you upload a file instead."
                  placeholder={'>genome_header\nATGCATGCATGCATGCATGC...'} sample={SAMPLE_GENOME} showMissing={missing}
                  missingText="Upload a FASTA file or paste a sequence before generating a timeline." />

      <button type="submit" className="btn btn-primary-custom btn-danger-custom w-100 btn-lg" disabled={busy}>
        {busy
          ? <><span className="spinner-border spinner-border-sm me-2" role="status"></span>Processing…</>
          : <><BioIcon icon="bi-activity" className="me-2" />Generate Timeline</>}
      </button>
    </form>
  );
}
