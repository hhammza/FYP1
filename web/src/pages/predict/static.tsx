/* The parts of /predict that only show text (converted from
   frontend/templates/resistance_prediction.html). */
import { Link } from 'react-router';
import { useMetrics } from '../../lib/health';

/** The page header. */
export function PredictHeader() {
  const m = useMetrics();
  return (
    <>
    <div className="page-header">
      <div className="container-xl">
        <nav aria-label="breadcrumb"><ol className="breadcrumb breadcrumb-custom">
          <li className="breadcrumb-item"><Link to="/">Dashboard</Link></li>
          <li className="breadcrumb-item active">Resistance Prediction</li>
        </ol></nav>
        <div className="d-flex align-items-center gap-3">
          <div className="page-header-icon kmer-icon"><i className="bi bi-dna"></i></div>
          <div>
            <h1 className="page-title">Genomic Resistance Prediction</h1>
            <p className="page-subtitle">K-mer frequency analysis of a complete genome assembly with LightGBM (AUC {m.kmer.auc} on lab-tested genomes it never saw)</p>
          </div>
        </div>
      </div>
    </div>
    </>
  );
}

/** The served model’s numbers above the form. */
export function ContextStrip() {
  const m = useMetrics();
  return (
    <>
      {/* ── Model Stats Strip (from the served model's metrics file) ── */}
      <div className="d-flex gap-3 flex-wrap mb-4">
        <div className="flex-fill min-w-150">
          <div className="stat-mini">
            <div className="stat-mini-value text-emerald2">{m.kmer.auc}</div>
            <div className="stat-mini-label">AUC-ROC (unseen genomes)</div>
          </div>
        </div>
        <div className="flex-fill min-w-150">
          <div className="stat-mini">
            <div className="stat-mini-value">256</div>
            <div className="stat-mini-label">K-mer features (4-mer)</div>
          </div>
        </div>
        <div className="flex-fill min-w-150">
          <div className="stat-mini">
            <div className="stat-mini-value text-indigo2">{m.kmer.threshold || 'n/a'}</div>
            <div className="stat-mini-label">Decision threshold (validated)</div>
          </div>
        </div>
        <div className="flex-fill min-w-150">
          <div className="stat-mini">
            <div className="stat-mini-value text-amber2">{m.kmer.train_rows_short}</div>
            <div className="stat-mini-label">Training genome-antibiotic pairs</div>
          </div>
        </div>
        <div className="flex-fill min-w-150">
          <div className="stat-mini">
            <div className="stat-mini-value text-rose2">{m.kmer.antibiotics}</div>
            <div className="stat-mini-label">Antibiotics covered</div>
          </div>
        </div>
      </div>
    </>
  );
}

/** The k-mer pipeline and GC content cards under the form. */
export function PipelineGuides() {
  return (
    <>
          {/* How it Works */}
          <div className="info-card mt-4">
            <h6 className="card-section-title"><i className="bi bi-gear text-accent me-2"></i>K-mer Analysis Pipeline</h6>
            <div className="method-steps">
              <div className="method-step"><span className="step-num">1</span>The whole FASTA genome is read, contig by contig; only A, T, C, G windows are counted</div>
              <div className="method-step"><span className="step-num">2</span>Sliding 4-mer window generates 256-dimensional frequency vector</div>
              <div className="method-step"><span className="step-num">3</span>The antibiotic, GC content and genome length are added</div>
              <div className="method-step"><span className="step-num">4</span>LightGBM (gradient-boosted trees) classifies Resistant vs Susceptible at a threshold chosen to miss at most 10% of resistant isolates</div>
              <div className="method-step"><span className="step-num">5</span>Output: probability, confidence, top discriminative k-mers</div>
            </div>
          </div>

          {/* GC Content Guide */}
          <div className="info-card mt-4">
            <h6 className="card-section-title"><i className="bi bi-pie-chart text-accent me-2"></i>GC Content & Resistance</h6>
            <div className="method-steps">
              <div className="method-step">{' '}
                <span className="step-num step-num-wide step-sky">~35%</span>{' '}
                <div><strong className="text-1">Low GC</strong>: typical of <em>Staphylococcus</em>, <em>Streptococcus</em></div>
              </div>
              <div className="method-step">{' '}
                <span className="step-num step-num-wide step-indigo">~50%</span>{' '}
                <div><strong className="text-1">Mid GC</strong>: typical of <em>E. coli</em>, <em>Salmonella</em></div>
              </div>
              <div className="method-step">{' '}
                <span className="step-num step-num-wide step-success">~65%</span>{' '}
                <div><strong className="text-1">High GC</strong>: typical of <em>Pseudomonas</em>, <em>Mycobacterium</em></div>
              </div>
            </div>
          </div>
    </>
  );
}

/** Shown before the first prediction. */
export function PredictEmpty() {
  return (
    <>
          {/* Empty State */}
          <div className="empty-state">
            <div className="empty-state-icon kmer-icon"><i className="bi bi-dna"></i></div>
            <h4>Upload a Bacterial Genome</h4>
            <p>Upload a FASTA file or paste a genome sequence to predict antibiotic resistance using 4-mer frequency analysis.</p>
            <div className="alert alert-info-custom mt-3 text-start">{' '}
              <i className="bi bi-lightbulb me-2"></i>{' '}
              <strong>Tip:</strong> Upload a complete genome assembly, for example one from <code>Data/genomes_full/</code>.{' '}
              <strong>Load Sample</strong> in the Paste Sequence tab pastes a short <em>E. coli</em> snippet (about 500 bp):
              the model refuses it, since it reads complete genomes of at least 100,000 bp.
            </div>
            <div className="row g-3 mt-2 text-start">
              <div className="col-md-6">
                <div className="example-box">
                  <div className="example-title">What you'll see</div>
                  <div className="example-content">
                    <div><i className="bi bi-check text-success me-1"></i>Resistant / Susceptible prediction</div>
                    <div><i className="bi bi-check text-success me-1"></i>Resistance probability score</div>
                    <div><i className="bi bi-check text-success me-1"></i>Genome GC content &amp; length</div>
                    <div><i className="bi bi-check text-success me-1"></i>Top discriminative 4-mers</div>
                    <div><i className="bi bi-check text-success me-1"></i>K-mer frequency spectrum chart</div>
                  </div>
                </div>
              </div>
              <div className="col-md-6">
                <div className="example-box">
                  <div className="example-title">Common test organisms</div>
                  <div className="example-content">
                    <div><i className="bi bi-bacteria text-accent me-1"></i><em>E. coli</em> K-12 (GC ~51%)</div>
                    <div><i className="bi bi-bacteria text-accent me-1"></i><em>K. pneumoniae</em> (GC ~57%)</div>
                    <div><i className="bi bi-bacteria text-accent me-1"></i><em>S. aureus</em> (GC ~33%)</div>
                    <div><i className="bi bi-bacteria text-accent me-1"></i><em>P. aeruginosa</em> (GC ~67%)</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
    </>
  );
}

/** The scientific background below the tool. */
export function PredictBackground() {
  const m = useMetrics();
  return (
    <>
      {/* ── Scientific Background ───────────────────────────────────── */}
      <div className="mt-5">
        <div className="mb-4">
          <div className="sec-eyebrow">Genomic Science</div>
          <div className="sec-title">K-mer Analysis for Resistance Prediction</div>
          <div className="sec-sub">K-mer frequencies encode the compositional "fingerprint" of a genome; resistance determinants leave distinctive patterns detectable by machine learning.</div>
        </div>

        <div className="row g-4 mb-4">
          <div className="col-md-4">
            <div className="crisis-card indigo h-100">
              <div className="crisis-icon"><i className="bi bi-grid text-indigo2"></i></div>
              <div className="crisis-val">4-mers</div>
              <div className="fw-600 mb-2 text-indigo2">256 Unique Tetranucleotides</div>
              <div className="crisis-desc">A 4-mer (tetranucleotide) is any consecutive 4-nucleotide sequence (AAAA, AAAT, …, TTTT). With 4 bases, 4⁴ = 256 possible 4-mers exist. Their relative frequencies form a "spectrum" that is unique per organism and encodes genomic composition, codon usage, and repeat content.</div>
            </div>
          </div>
          <div className="col-md-4">
            <div className="crisis-card amber h-100">
              <div className="crisis-icon"><i className="bi bi-tree text-amber2"></i></div>
              <div className="crisis-val">LightGBM</div>
              <div className="fw-600 mb-2 text-amber2">Gradient-Boosted Decision Trees</div>
              <div className="crisis-desc">LightGBM adds decision trees one at a time, each correcting the errors of the ones before. Trained on complete genomes of about 20,000 bacteria, it scores AUC-ROC {m.kmer.auc_ci} on lab-tested genomes it never saw. The earlier RandomForest, trained on partial genomes, scored about 0.70, no better than the antibiotic alone. 4-mer frequencies partly identify the lineage rather than the resistance mechanism, so the next model uses the resistance genes themselves.</div>
            </div>
          </div>
          <div className="col-md-4">
            <div className="crisis-card rose h-100">
              <div className="crisis-icon"><i className="bi bi-shield-exclamation text-rose2"></i></div>
              <div className="crisis-val">Resistance Genes</div>
              <div className="fw-600 mb-2 text-rose2">Genomic Determinants</div>
              <div className="crisis-desc">Resistance genes alter k-mer frequencies around their insertion sites. Beta-lactamase genes (blaTEM, blaSHV, blaKPC), efflux pumps (acrAB-tolC, mexAB-oprM), and aminoglycoside-modifying enzymes each leave detectable composition signatures in the 4-mer spectrum.</div>
            </div>
          </div>
        </div>

        <div className="row g-4">
          <div className="col-lg-6">
            <div className="glass-card h-100">
              <h6 className="card-section-title"><i className="bi bi-bezier2 text-accent me-2"></i>Key Resistance Mechanisms by Drug Class</h6>
              <div className="table-responsive">
                <table className="table table-custom table-sm mb-0">
                  <thead><tr><th>Drug Class</th><th>Primary Mechanism</th><th>Key Gene(s)</th></tr></thead>
                  <tbody>
                    <tr><td>Beta-Lactams</td><td>Enzyme hydrolysis</td><td className="font-mono text-accent2">blaTEM, blaSHV, blaKPC</td></tr>
                    <tr><td>Fluoroquinolones</td><td>Target mutation</td><td className="font-mono text-accent2">gyrA, parC, qnr</td></tr>
                    <tr><td>Aminoglycosides</td><td>Enzymatic modification</td><td className="font-mono text-accent2">aac, aph, ant</td></tr>
                    <tr><td>Tetracyclines</td><td>Efflux + ribosomal protection</td><td className="font-mono text-accent2">tetA–M, rpsJ</td></tr>
                    <tr><td>Carbapenems</td><td>Carbapenemase production</td><td className="font-mono text-accent2">blaKPC, blaNDM, blaOXA</td></tr>
                    <tr><td>Trimethoprim</td><td>Target mutation</td><td className="font-mono text-accent2">dhfr, dfrA</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          <div className="col-lg-6">
            <div className="glass-card h-100">
              <h6 className="card-section-title"><i className="bi bi-cpu text-accent me-2"></i>Why K-mers Beat Sequence Alignment</h6>
              <div className="how-step how-step-compact">
                <div className="how-num how-num-sm">01</div>
                <div><div className="how-title fs-13">Reference-free</div><div className="how-desc fs-12">No reference genome needed; it works on any novel pathogen assembly</div></div>
              </div>
              <div className="how-step how-step-compact">
                <div className="how-num how-num-sm">02</div>
                <div><div className="how-title fs-13">Speed</div><div className="how-desc fs-12">O(n) scan of genome sequence, taking milliseconds even for 5Mb genomes</div></div>
              </div>
              <div className="how-step how-step-compact">
                <div className="how-num how-num-sm">03</div>
                <div><div className="how-title fs-13">Captures mobile elements</div><div className="how-desc fs-12">Plasmid-borne resistance genes change k-mer composition globally, not just locally</div></div>
              </div>
              <div className="how-step how-step-compact">
                <div className="how-num how-num-sm">04</div>
                <div><div className="how-title fs-13">Interpretable</div><div className="how-desc fs-12">Feature importance reveals which 4-mers are most discriminative for each antibiotic class</div></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
