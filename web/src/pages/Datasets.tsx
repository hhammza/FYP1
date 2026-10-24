import { Link } from 'react-router';
import { useMetrics } from '../lib/health';
import { useTitle } from '../lib/pageEffects';

export default function Datasets() {
  useTitle('Datasets & Data Sources');
  const m = useMetrics();
  return (
    <>
    <div className="page-header">
      <div className="container-xl">
        <nav aria-label="breadcrumb"><ol className="breadcrumb breadcrumb-custom">
          <li className="breadcrumb-item"><Link to="/">Dashboard</Link></li>
          <li className="breadcrumb-item active">Datasets</li>
        </ol></nav>
        <div className="d-flex align-items-center gap-3">
          <div className="page-header-icon">{' '}
            <i className="bi bi-database"></i>
          </div>
          <div>
            <h1 className="page-title">Datasets &amp; Data Sources</h1>
            <p className="page-subtitle">Five source datasets from BV-BRC, NCBI GenBank and published studies, the data we built from them, and which model uses which</p>
          </div>
        </div>
      </div>
    </div>


    <div className="container-xl py-4">

      {/* ── Overview Stats Strip ──────────────────────────────────── */}
      <div className="d-flex gap-3 flex-wrap mb-4">
        <div className="flex-fill min-w-130"><div className="stat-mini">
          <div className="stat-mini-value stat-mini-static text-indigo2">5</div>
          <div className="stat-mini-label">Source datasets</div>
        </div></div>
        <div className="flex-fill min-w-130"><div className="stat-mini">
          <div className="stat-mini-value stat-mini-static text-emerald2">7.85M</div>
          <div className="stat-mini-label">Labelled AMR records (after cleaning)</div>
        </div></div>
        <div className="flex-fill min-w-130"><div className="stat-mini">
          <div className="stat-mini-value stat-mini-static">439,542</div>
          <div className="stat-mini-label">Genomes with AMR results</div>
        </div></div>
        <div className="flex-fill min-w-130"><div className="stat-mini">
          <div className="stat-mini-value stat-mini-static text-amber2">24,926</div>
          <div className="stat-mini-label">Complete genomes</div>
        </div></div>
        <div className="flex-fill min-w-130"><div className="stat-mini">
          <div className="stat-mini-value stat-mini-static text-rose2">126</div>
          <div className="stat-mini-label">Antibiotics</div>
        </div></div>
        <div className="flex-fill min-w-130"><div className="stat-mini">
          <div className="stat-mini-value stat-mini-static fs-13">BV-BRC, NCBI<br />ECDC, PLOS</div>
          <div className="stat-mini-label">Data sources</div>
        </div></div>
      </div>

      {/* ── Source datasets ───────────────────────────────────────── */}
      <div className="glass-card mb-4">
        <h5 className="fw-700 mb-1"><i className="bi bi-table me-2 text-indigo2"></i>The Five Source Datasets</h5>
        <p className="fs-13 text-muted mb-3">Downloaded from outside the project. Everything else on this page is built from these.</p>
        <div className="table-responsive">
          <table className="table table-custom mb-0">
            <thead>
              <tr>
                <th>#</th><th>Dataset</th><th>Location</th><th>Size</th><th>Source</th><th>Used for</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><span className="step-num step-indigo">1</span></td>
                <td className="fw-600 text-white"><a href="#ds-amr">AMR Phenotype Records</a></td>
                <td className="font-mono text-accent small">amr_full/</td>
                <td>17.6M records · 7.85M rows after cleaning</td>
                <td className="small">BV-BRC</td>
                <td><span className="status-badge trained">LightGBM</span></td>
              </tr>
              <tr>
                <td><span className="step-num step-emerald">2</span></td>
                <td className="fw-600 text-white"><a href="#ds-fasta">Genome Sequences (partial FASTA)</a>{' '}
                  <span className="status-badge simulated ms-1">Superseded</span></td>
                <td className="font-mono text-accent small">fasta_output/</td>
                <td>2,587 files · 4.0 GB</td>
                <td className="small">NCBI GenBank</td>
                <td><span className="status-badge simulated">Original K-mer RF (retired)</span></td>
              </tr>
              <tr>
                <td><span className="step-num step-amber">3</span></td>
                <td className="fw-600 text-white"><a href="#ds-assemblies">Complete Genome Assemblies</a></td>
                <td className="font-mono text-accent small">genomes_full/</td>
                <td>24,926 genomes · 102.5 billion bp</td>
                <td className="small">BV-BRC</td>
                <td><span className="status-badge trained status-badge-emerald">K-mer LightGBM</span>{' '}
                  <span className="status-badge trained status-badge-emerald ms-1">AMRFinderPlus</span></td>
              </tr>
              <tr>
                <td><span className="step-num step-rose">4</span></td>
                <td className="fw-600 text-white"><a href="#ds-export">Single AMR Export</a></td>
                <td className="font-mono text-accent small">BVBRC_genome_amr.csv</td>
                <td>171,000 rows · 69,708 genomes</td>
                <td className="small">BV-BRC</td>
                <td><span className="status-badge simulated">Notebooks</span></td>
              </tr>
              <tr>
                <td><span className="step-num step-sky">5</span></td>
                <td className="fw-600 text-white"><a href="#ds-calibration">Published Resistance Curves</a></td>
                <td className="font-mono text-accent small">evolution_curves/</td>
                <td>5 lab curves · 31 countries × 20 years</td>
                <td className="small">PLOS Biology, ECDC</td>
                <td><span className="status-badge simulated">Timeline check</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Built from the datasets ───────────────────────────────── */}
      <div className="glass-card mb-5">
        <h5 className="fw-700 mb-1"><i className="bi bi-diagram-3 me-2 text-indigo2"></i>Built From Them (not separate datasets)</h5>
        <p className="fs-13 text-muted mb-3">Made by this project's code from Datasets 1 to 3, so they are not counted as datasets of their own.</p>
        <div className="table-responsive">
          <table className="table table-custom mb-0">
            <thead>
              <tr><th>What</th><th>Location</th><th>Made from</th><th>Used for</th></tr>
            </thead>
            <tbody>
              <tr>
                <td className="fw-600 text-white"><a href="#ds-mapped">Mapped AMR Records</a></td>
                <td className="font-mono text-accent small">mapped_output/</td>
                <td className="small">Dataset 1 rows joined to Dataset 2 files</td>
                <td><span className="status-badge simulated">Original K-mer RF (retired)</span></td>
              </tr>
              <tr>
                <td className="fw-600 text-white"><Link to="/genes">Gene Matrix</Link></td>
                <td className="font-mono text-accent small">experiments/genome/features/</td>
                <td className="small">AMRFinderPlus run on Dataset 3</td>
                <td><span className="status-badge simulated">Next models, <Link to="/genes">/genes</Link></span></td>
              </tr>
              <tr>
                <td className="fw-600 text-white"><a href="#ds-samples">Test Samples</a></td>
                <td className="font-mono text-accent small">sample_*/</td>
                <td className="small">Small copies of Datasets 1 and 2 and the mapped records</td>
                <td><span className="status-badge simulated">Quick tests</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* ════════════════════════════════════════════════════════════
           DATASET 1: AMR Phenotype Records
           ════════════════════════════════════════════════════════════ */}
      <div className="mb-5" id="ds-amr">
        <div className="d-flex align-items-center gap-3 mb-3">
          <div className="step-num fs-5 fw-700 step-num-lg step-indigo">1</div>
          <div>
            <div className="sec-eyebrow">Dataset 1 · Primary Training Data</div>
            <h2 className="sec-title mb-0">AMR Phenotype Records (CSV)</h2>
          </div>
        </div>

        <div className="row g-4">
          {/* Description */}
          <div className="col-lg-8">
            <div className="info-card h-100">
              <h6 className="card-section-title"><i className="bi bi-info-circle text-accent me-2"></i>What This Dataset Contains</h6>
              <p className="body-text lh-17">{' '}
                This is the core tabular dataset sourced from the <strong>BVBRC (BV-BRC / PATRIC) database</strong>, a United States Department of Energy national database of bacterial genomic and antimicrobial resistance data. It provides the labeled ground-truth used to train the LightGBM gradient boosting model.
              </p>
              <p className="body-text lh-17">{' '}
                Each row represents a single <em>genome–antibiotic test result</em>: a specific bacterial isolate tested against a specific antibiotic. The key label is the <strong className="text-rose2">Resistant Phenotype</strong> column, which shows whether the isolate was found <strong className="text-rose2">Resistant</strong>, <strong className="text-emerald2">Susceptible</strong>, or <strong className="text-amber2">Intermediate</strong>.
              </p>
              <p className="body-text lh-17">{' '}
                After cleaning it covers 40 bacterial genera and 126 antibiotics. Only 8% of the labels were measured in a laboratory; the rest were predicted by BV-BRC's own models, and every row records which it is.
              </p>

              <h6 className="card-section-title mt-4"><i className="bi bi-table text-accent me-2"></i>Column Schema</h6>
              <div className="table-responsive">
                <table className="table table-custom table-sm mb-0">
                  <thead><tr><th>Column</th><th>Type</th><th>Description</th><th>Used in Model</th></tr></thead>
                  <tbody>
                    <tr><td className="font-mono text-accent2">Genome ID</td><td className="small">String</td><td className="small text-muted">Unique genome identifier in BVBRC</td><td><span className="feature-tag">Dedup key</span></td></tr>
                    <tr><td className="font-mono text-accent2">Genome Name</td><td className="small">String</td><td className="small text-muted">Full species name (e.g., "Escherichia coli K-12")</td><td><span className="feature-tag">genus/species</span></td></tr>
                    <tr><td className="font-mono text-accent2">Taxon ID</td><td className="small">Integer</td><td className="small text-muted">NCBI Taxonomy ID of the organism</td><td><span className="feature-tag">Feature</span></td></tr>
                    <tr><td className="font-mono text-accent2">Antibiotic</td><td className="small">String</td><td className="small text-muted">Antibiotic tested (lowercase, standardized)</td><td><span className="feature-tag">Feature + Encode</span></td></tr>
                    <tr><td className="font-mono text-rose2">Resistant Phenotype</td><td className="small">Categorical</td><td className="small text-muted"><strong>TARGET LABEL</strong>: Resistant, Susceptible, or Intermediate</td><td><span className="feature-tag feature-tag-rose">Target</span></td></tr>
                    <tr><td className="font-mono text-accent2">Measurement</td><td className="small">String</td><td className="small text-muted">Raw MIC string (e.g., "&lt;=4", "2", "&gt;=32")</td><td><span className="feature-tag">mic_sign + mic_value</span></td></tr>
                    <tr><td className="font-mono text-accent2">Measurement Value</td><td className="small">Float</td><td className="small text-muted">Numeric MIC value in mg/L</td><td><span className="feature-tag">mic_value</span></td></tr>
                    <tr><td className="font-mono text-accent2">Measurement Units</td><td className="small">String</td><td className="small text-muted">Unit of measurement (typically mg/L)</td><td><span className="feature-tag">Validation</span></td></tr>
                    <tr><td className="font-mono text-accent2">Evidence</td><td className="small">String</td><td className="small text-muted">"Laboratory Method" or "Computational Method"</td><td><span className="feature-tag">is_lab_confirmed</span></td></tr>
                    <tr><td className="font-mono text-accent2">Computational Method Performance</td><td className="small">String</td><td className="small text-muted">Model F1 score string (parsed for confidence weight)</td><td><span className="feature-tag">computational_f1</span></td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Stats + Usage */}
          <div className="col-lg-4">
            <div className="info-card mb-4">
              <h6 className="card-section-title"><i className="bi bi-bar-chart text-accent me-2"></i>Dataset Statistics</h6>
              <table className="table table-custom table-sm">
                <thead><tr><th></th><th>Count</th></tr></thead><tbody>
                <tr><td className="text-muted">Raw records</td><td className="fw-600 text-white">17,585,506</td></tr>
                <tr><td className="text-muted">Rows after cleaning</td><td className="fw-600 text-white">7,847,110</td></tr>
                <tr><td className="text-muted">Genomes</td><td className="fw-600 text-white">439,542</td></tr>
                <tr><td className="text-muted">Lab-tested genomes</td><td className="fw-600 text-white">87,325</td></tr>
                <tr><td className="text-muted">Laboratory-measured rows</td><td className="fw-600 text-white">649,944 (8%)</td></tr>
                <tr><td className="text-muted">Antibiotics</td><td className="fw-600 text-white">126</td></tr>
                <tr><td className="text-muted">Species</td><td className="fw-600 text-white">247</td></tr>
                <tr><td className="text-muted">Resistant share</td><td className="fw-600 text-white">28.0%</td></tr>
                <tr><td className="text-muted">Resistant share, lab rows</td><td className="fw-600 text-white">33.7%</td></tr>
              </tbody></table>
            </div>

            <div className="info-card mb-4">
              <h6 className="card-section-title"><i className="bi bi-bacteria text-accent me-2"></i>Largest Genera (rows after cleaning)</h6>
              <div className="method-steps">
                <div className="method-step"><span className="step-num step-num-xs">1</span><div><em>Escherichia</em>: 3,562,956</div></div>
                <div className="method-step"><span className="step-num step-num-xs">2</span><div><em>Salmonella</em>: 1,083,062</div></div>
                <div className="method-step"><span className="step-num step-num-xs">3</span><div><em>Mycobacterium</em>: 979,138</div></div>
                <div className="method-step"><span className="step-num step-num-xs">4</span><div><em>Klebsiella</em>: 703,539</div></div>
                <div className="method-step"><span className="step-num step-num-xs">5</span><div><em>Staphylococcus</em>: 366,887</div></div>
              </div>
            </div>

            <div className="info-card">
              <h6 className="card-section-title"><i className="bi bi-gear text-accent me-2"></i>Preprocessing Steps</h6>
              <div className="method-steps">
                <div className="method-step"><span className="step-num" style={{width: '24px', height: '24px', fontSize: '10px'}}>1</span>Parse MIC sign (&lt;=, =, &gt;=) from Measurement string</div>
                <div className="method-step"><span className="step-num" style={{width: '24px', height: '24px', fontSize: '10px'}}>2</span>Extract numeric MIC value with regex fallback</div>
                <div className="method-step"><span className="step-num" style={{width: '24px', height: '24px', fontSize: '10px'}}>3</span>Parse genus + species from Genome Name</div>
                <div className="method-step"><span className="step-num" style={{width: '24px', height: '24px', fontSize: '10px'}}>4</span>Merge Intermediate → Resistant (binary labels)</div>
                <div className="method-step"><span className="step-num" style={{width: '24px', height: '24px', fontSize: '10px'}}>5</span>Deduplicate on (Genome ID, Antibiotic), keep lab-confirmed</div>
                <div className="method-step"><span className="step-num" style={{width: '24px', height: '24px', fontSize: '10px'}}>6</span>Target-encode resistance rates per antibiotic, taxon, genus</div>
              </div>
            </div>
          </div>
        </div>

        {/* Feature Engineering */}
        <div className="glass-card mt-4">
          <h6 className="card-section-title"><i className="bi bi-cpu text-accent me-2"></i>14 Features Extracted → LightGBM Model</h6>
          <div className="row g-3">
            <div className="col-md-4">
              <div className="example-box">
                <div className="example-title" style={{color: 'var(--accent2)'}}>Direct Columns (raw)</div>
                <div className="example-content">
                  <div className="font-mono small" style={{color: 'var(--text-2)'}}>Taxon ID</div>
                  <div className="font-mono small" style={{color: 'var(--text-2)'}}>Antibiotic</div>
                  <div className="font-mono small" style={{color: 'var(--text-2)'}}>drug_class (mapped)</div>
                  <div className="font-mono small" style={{color: 'var(--text-2)'}}>genus, species</div>
                  <div className="font-mono small" style={{color: 'var(--text-2)'}}>mic_sign, mic_value</div>
                </div>
              </div>
            </div>
            <div className="col-md-4">
              <div className="example-box">
                <div className="example-title" style={{color: 'var(--emerald2)'}}>Derived Features (engineered)</div>
                <div className="example-content">
                  <div className="font-mono small" style={{color: 'var(--text-2)'}}>mic_log = log1p(mic_value)</div>
                  <div className="font-mono small" style={{color: 'var(--text-2)'}}>has_mic = 0 or 1</div>
                  <div className="font-mono small" style={{color: 'var(--text-2)'}}>is_lab_confirmed = 0/1</div>
                  <div className="font-mono small" style={{color: 'var(--text-2)'}}>computational_f1 ∈ [0,1]</div>
                </div>
              </div>
            </div>
            <div className="col-md-4">
              <div className="example-box">
                <div className="example-title" style={{color: 'var(--amber2)'}}>Target-Encoded Rates</div>
                <div className="example-content">
                  <div className="font-mono small" style={{color: 'var(--text-2)'}}>ab_resistance_rate</div>
                  <div className="font-mono small" style={{color: 'var(--text-2)'}}>(per antibiotic, global)</div>
                  <div className="font-mono small" style={{color: 'var(--text-2)'}}>taxon_ab_resistance_rate</div>
                  <div className="font-mono small" style={{color: 'var(--text-2)'}}>genus_ab_resistance_rate</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>


      {/* ════════════════════════════════════════════════════════════
           DATASET 2: FASTA Genome Sequences
           ════════════════════════════════════════════════════════════ */}
      <div className="mb-5" id="ds-fasta">
        <div className="d-flex align-items-center gap-3 mb-3">
          <div className="step-num fs-5 fw-700" style={{width: '44px', height: '44px', background: 'rgba(16,185,129,0.15)', borderColor: 'rgba(16,185,129,0.4)', color: 'var(--emerald2)'}}>2</div>
          <div>
            <div className="sec-eyebrow">Dataset 2 · Genomic Sequences</div>
            <h2 className="sec-title mb-0">Genome Sequences (partial FASTA)</h2>
          </div>
        </div>

        <div className="alert alert-warning-custom mb-4" role="note">{' '}
          <i className="bi bi-archive me-2"></i><strong>Superseded by <a href="#ds-assemblies">Dataset 3</a>, kept to reproduce the original K-mer model.</strong>{' '}
          <Link to="/predict">/predict</Link> now serves a model trained on the complete genomes of Dataset 3. The numbers in this
          section describe the original K-mer RandomForest trained on these partial files.
        </div>

        <div className="row g-4">
          <div className="col-lg-8">
            <div className="info-card h-100">
              <h6 className="card-section-title"><i className="bi bi-info-circle text-accent me-2"></i>What This Dataset Contains</h6>
              <p style={{fontSize: '13px', color: 'var(--text-2)', lineHeight: '1.7'}}>{' '}
                Bacterial DNA sequences in <strong>FASTA format</strong>, the standard bioinformatics format for nucleotide sequences, one file per isolate. <strong>These files are partial:</strong> a typical file holds about a third of its genome (median 31%; an <em>E. coli</em> file is about 0.8 of 5 MB), because they were saved truncated. A resistance gene in the missing part cannot be seen, which is why the gene search uses <a href="#ds-assemblies">Dataset 3</a> instead.
              </p>
              <p style={{fontSize: '13px', color: 'var(--text-2)', lineHeight: '1.7'}}>{' '}
                Files are organized by BVBRC genome ID. A FASTA file begins with a header line (starting with <code className="font-mono">&gt;</code>) followed by the raw nucleotide sequence. These sequences are the input to the K-mer resistance predictor. The model reads the sequence, computes 4-mer frequencies, and classifies resistance without needing a reference genome alignment.
              </p>

              <h6 className="card-section-title mt-4"><i className="bi bi-file-code text-accent me-2"></i>FASTA Format Example</h6>
              <div className="code-block" style={{background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: 'var(--r)', padding: '16px', fontSize: '12px'}}>
                <div style={{color: 'var(--text-3)', marginBottom: '8px'}}>Sample FASTA file (E. coli K-12):</div>
                <pre className="font-mono mb-0" style={{color: 'var(--accent2)', fontSize: '11px', lineHeight: '1.8'}}>{">fig|562.2166.peg.1  Escherichia coli K-12 substr. MG1655\nATGAAACGCATTAGCACCACCATTACCACCACCATCACCATTACCACAGG\nTAACGGTGCGGGCTGACGCGTACAGGAAACACAGAAAAAAGCCCGCACCT\nGACAGTGCGGGCTTTTTTTTTCGACCAAAGGTAACGAGGTAACAACCAT\nGCGAGTGTTGAAGTTCGGCGGTACATCAGTGGCAAATGCAGAACGTTTT\n"}<span style={{color: 'var(--text-3)'}}>{"... (continues for millions of base pairs) ..."}</span></pre>
              </div>

              <h6 className="card-section-title mt-4"><i className="bi bi-grid-3x3 text-accent me-2"></i>K-mer Feature Extraction Pipeline</h6>
              <div className="row g-3">
                <div className="col-md-6">
                  <div className="how-step" style={{padding: '14px', marginBottom: '0'}}>
                    <div className="how-num" style={{width: '30px', height: '30px', fontSize: '12px'}}>1</div>
                    <div><div className="how-title" style={{fontSize: '13px'}}>Read &amp; Clean</div><div className="how-desc" style={{fontSize: '12px'}}>Parse FASTA, strip header lines, keep only A/T/C/G nucleotides. First 500,000 bp analyzed.</div></div>
                  </div>
                </div>
                <div className="col-md-6">
                  <div className="how-step" style={{padding: '14px', marginBottom: '0'}}>
                    <div className="how-num" style={{width: '30px', height: '30px', fontSize: '12px'}}>2</div>
                    <div><div className="how-title" style={{fontSize: '13px'}}>4-mer Sliding Window</div><div className="how-desc" style={{fontSize: '12px'}}>Slide a 4-nucleotide window across the full sequence, counting each of 4⁴=256 possible tetranucleotides.</div></div>
                  </div>
                </div>
                <div className="col-md-6">
                  <div className="how-step" style={{padding: '14px', marginBottom: '0'}}>
                    <div className="how-num" style={{width: '30px', height: '30px', fontSize: '12px'}}>3</div>
                    <div><div className="how-title" style={{fontSize: '13px'}}>Frequency Normalization</div><div className="how-desc" style={{fontSize: '12px'}}>Divide each count by total k-mers → frequency vector in [0, 1]. This removes genome length bias.</div></div>
                  </div>
                </div>
                <div className="col-md-6">
                  <div className="how-step" style={{padding: '14px', marginBottom: '0'}}>
                    <div className="how-num" style={{width: '30px', height: '30px', fontSize: '12px'}}>4</div>
                    <div><div className="how-title" style={{fontSize: '13px'}}>GC Content + Antibiotic</div><div className="how-desc" style={{fontSize: '12px'}}>Append GC%, AT%, genome_length/500K, plus one-hot encoding of the antibiotic class (N dimensions).</div></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="col-lg-4">
            <div className="info-card mb-4">
              <h6 className="card-section-title"><i className="bi bi-bar-chart text-accent me-2"></i>Dataset Statistics</h6>
              <table className="table table-custom table-sm"><tbody>
                <tr><td className="text-muted">FASTA files (genomes)</td><td className="fw-600 text-white">2,587</td></tr>
                <tr><td className="text-muted">Taxon folders</td><td className="fw-600 text-white">1,683</td></tr>
                <tr><td className="text-muted">Size on disk</td><td className="fw-600 text-white">4.0 GB</td></tr>
                <tr><td className="text-muted">Share of each genome kept</td><td className="fw-600 text-white">median 31%</td></tr>
                {/* The retired model's final numbers (backend/trained_models/kmer_metrics.json):
                    metrics.kmer is now the model /predict serves, trained on Dataset 3 */}
                <tr><td className="text-muted">BP analyzed per genome (original model)</td><td className="fw-600 text-white">up to 500,000</td></tr>
                <tr><td className="text-muted">4-mer dimensions</td><td className="fw-600 text-white">256</td></tr>
                <tr><td className="text-muted">Original K-mer RF trained on</td><td className="fw-600 text-white">6,002 genome–antibiotic pairs</td></tr>
              </tbody></table>
            </div>

            <div className="info-card mb-4">
              <h6 className="card-section-title"><i className="bi bi-pie-chart text-accent me-2"></i>GC Content by Species</h6>
              <div className="method-steps">
                <div className="method-step">{' '}
                  <span className="step-num" style={{width: '28px', height: '28px', fontSize: '10px', background: 'rgba(244,63,94,0.12)', borderColor: 'rgba(244,63,94,0.3)', color: 'var(--rose2)'}}>33%</span>{' '}
                  <div><em>S. aureus</em>: AT-rich genome</div>
                </div>
                <div className="method-step">{' '}
                  <span className="step-num" style={{width: '28px', height: '28px', fontSize: '10px', background: 'rgba(99,102,241,0.12)', borderColor: 'rgba(99,102,241,0.3)', color: 'var(--indigo2)'}}>51%</span>{' '}
                  <div><em>E. coli</em>: balanced GC</div>
                </div>
                <div className="method-step">{' '}
                  <span className="step-num" style={{width: '28px', height: '28px', fontSize: '10px', background: 'rgba(245,158,11,0.12)', borderColor: 'rgba(245,158,11,0.3)', color: 'var(--amber2)'}}>57%</span>{' '}
                  <div><em>K. pneumoniae</em>: GC-rich</div>
                </div>
                <div className="method-step">{' '}
                  <span className="step-num" style={{width: '28px', height: '28px', fontSize: '10px', background: 'rgba(16,185,129,0.12)', borderColor: 'rgba(16,185,129,0.3)', color: 'var(--emerald2)'}}>67%</span>{' '}
                  <div><em>P. aeruginosa</em>: high GC</div>
                </div>
              </div>
            </div>

            <div className="info-card">
              <h6 className="card-section-title"><i className="bi bi-shield-check text-accent me-2"></i>Why K-mers?</h6>
              <p style={{fontSize: '12px', color: 'var(--text-2)', lineHeight: '1.6'}}>{' '}
                K-mer frequencies capture the compositional "fingerprint" of a genome without requiring alignment to a reference. Resistance genes alter the k-mer composition around insertion sites, making these patterns detectable by machine learning. The approach is <strong>alignment-free</strong>, works on any assembly quality, and runs in milliseconds.
              </p>
              <div className="d-flex flex-wrap gap-2 mt-2">{' '}
                <span className="feature-tag">Reference-free</span>{' '}
                <span className="feature-tag">O(n) scan</span>{' '}
                <span className="feature-tag">Original model AUC 0.695</span>{' '}
                <span className="feature-tag">On complete genomes (Dataset 3): {m.kmer.auc}</span>
              </div>
            </div>
          </div>
        </div>
      </div>


      {/* ════════════════════════════════════════════════════════════
           DATASET 3: Complete Genome Assemblies
           ════════════════════════════════════════════════════════════ */}
      <div className="mb-5" id="ds-assemblies">
        <div className="d-flex align-items-center gap-3 mb-3">
          <div className="step-num fs-5 fw-700" style={{width: '44px', height: '44px', background: 'rgba(245,158,11,0.15)', borderColor: 'rgba(245,158,11,0.4)', color: 'var(--amber2)'}}>3</div>
          <div>
            <div className="sec-eyebrow">Dataset 3 · Complete Genomes</div>
            <h2 className="sec-title mb-0">Complete Genome Assemblies</h2>
          </div>
        </div>

        <div className="row g-4">
          <div className="col-lg-8">
            <div className="info-card h-100">
              <h6 className="card-section-title"><i className="bi bi-info-circle text-accent me-2"></i>What This Dataset Contains</h6>
              <p className="body-text lh-17">{' '}
                Complete genomes downloaded from the <strong>BV-BRC API</strong>: the same 2,587 isolates as Dataset 2 (downloaded again because the local FASTA files are partial), plus every genome with a <strong>laboratory</strong> resistance result in the earlier version of Dataset 1, 22,475 in all (Sept 2026). The complete export has 87,325 lab-tested genomes; the DNA of the other 64,850 is not downloaded yet. Before that, only 136 genomes with DNA had a lab result, too few to test the genome models on. A download is kept only if its length is within 1% of the length BV-BRC reports for that genome, so every file here is complete.
              </p>
              <p className="body-text lh-17">{' '}
                NCBI <strong>AMRFinderPlus</strong> searched every assembly for known resistance genes and resistance mutations. The results form the <Link to="/genes">gene matrix</Link>: one row per genome, one 0/1 column per gene or mutation (2,733 columns). At about 100 GB the assemblies are not stored in git; <code className="font-mono">experiments/genome/features/download_genomes.py</code> downloads them again.
              </p>
            </div>
          </div>
          <div className="col-lg-4">
            <div className="info-card h-100">
              <h6 className="card-section-title"><i className="bi bi-bar-chart text-accent me-2"></i>Dataset Statistics</h6>
              <table className="table table-custom table-sm mb-0"><tbody>
                <tr><td className="text-muted">Genomes</td><td className="fw-600 text-white">24,926</td></tr>
                <tr><td className="text-muted">With a lab result</td><td className="fw-600 text-white">22,475</td></tr>
                <tr><td className="text-muted">Total length</td><td className="fw-600 text-white">102.5 billion bp</td></tr>
                <tr><td className="text-muted">Median genome</td><td className="fw-600 text-white">4.5 million bp</td></tr>
                <tr><td className="text-muted">Size on disk</td><td className="fw-600 text-white">98 GB</td></tr>
                <tr><td className="text-muted">Searched by AMRFinderPlus</td><td className="fw-600 text-white">all 24,926</td></tr>
                <tr><td className="text-muted">With a resistance gene</td><td className="fw-600 text-white">22,949</td></tr>
              </tbody></table>
            </div>
          </div>
        </div>
      </div>


      {/* ════════════════════════════════════════════════════════════
           DATASET 4: Single AMR Export
           ════════════════════════════════════════════════════════════ */}
      <div className="mb-5" id="ds-export">
        <div className="d-flex align-items-center gap-3 mb-3">
          <div className="step-num fs-5 fw-700" style={{width: '44px', height: '44px', background: 'rgba(244,63,94,0.15)', borderColor: 'rgba(244,63,94,0.4)', color: 'var(--rose2)'}}>4</div>
          <div>
            <div className="sec-eyebrow">Dataset 4 · Notebook Data</div>
            <h2 className="sec-title mb-0">Single AMR Export</h2>
          </div>
        </div>

        <div className="row g-4">
          <div className="col-lg-8">
            <div className="info-card h-100">
              <h6 className="card-section-title"><i className="bi bi-info-circle text-accent me-2"></i>What This Dataset Contains</h6>
              <p className="body-text lh-17">{' '}
                One CSV file, <code className="font-mono">BVBRC_genome_amr.csv</code>, exported from BV-BRC with the same kind of genome–antibiotic results as Dataset 1 but in a single file and a smaller, separate selection of genomes.
              </p>
              <p className="body-text lh-17">{' '}
                The development notebooks were built on it, so their numbers come from this file, not from Dataset 1. <strong>The deployed models do not use it.</strong> The project uses it to check the antibiotic names offered in the dropdowns.
              </p>
            </div>
          </div>
          <div className="col-lg-4">
            <div className="info-card h-100">
              <h6 className="card-section-title"><i className="bi bi-bar-chart text-accent me-2"></i>Dataset Statistics</h6>
              <table className="table table-custom table-sm mb-0"><tbody>
                <tr><td className="text-muted">Rows</td><td className="fw-600 text-white">171,000</td></tr>
                <tr><td className="text-muted">Genomes</td><td className="fw-600 text-white">69,708</td></tr>
                <tr><td className="text-muted">Antibiotics</td><td className="fw-600 text-white">93</td></tr>
                <tr><td className="text-muted">Columns</td><td className="fw-600 text-white">21</td></tr>
                <tr><td className="text-muted">Size</td><td className="fw-600 text-white">30 MB</td></tr>
              </tbody></table>
            </div>
          </div>
        </div>
      </div>


      {/* ════════════════════════════════════════════════════════════
           DATASET 5: Published Resistance Curves (timeline calibration)
           ════════════════════════════════════════════════════════════ */}
      <div className="mb-5" id="ds-calibration">
        <div className="d-flex align-items-center gap-3 mb-3">
          <div className="step-num step-sky fs-5 fw-700" style={{width: '44px', height: '44px'}}>5</div>
          <div>
            <div className="sec-eyebrow">Dataset 5 · Timeline Calibration</div>
            <h2 className="sec-title mb-0">Published Resistance Curves</h2>
          </div>
        </div>

        <div className="row g-4">
          <div className="col-lg-8">
            <div className="info-card h-100">
              <h6 className="card-section-title"><i className="bi bi-info-circle text-accent me-2"></i>What This Dataset Contains</h6>
              <p className="body-text lh-17">{' '}
                Resistance measured over time, taken from published work, to check the shape of the <Link to="/timeline">Mutation Timeline</Link>'s curve. Two kinds, kept apart because they measure different things:
              </p>
              <ul className="body-text lh-17 mb-3">
                <li><strong>Lab evolution</strong> (Maltas, Huynh &amp; Wood 2025, <em>PLOS Biology</em>, doi:10.1371/journal.pbio.3002970): <em>Enterococcus faecalis</em> evolved for 8 days under ciprofloxacin, ceftriaxone, doxycycline, daptomycin or linezolid, 4 populations each, with resistance (IC50) measured every 2 days.</li>
                <li><strong>Hospital surveillance</strong> (ECDC Surveillance Atlas, EARS-Net): the share of invasive <em>Klebsiella pneumoniae</em> resistant to carbapenems, per country and year.</li>
              </ul>
              <p className="body-text lh-17">{' '}
                The timeline's logistic curve fits 15 of these curves with a median R&sup2; of 0.91. <strong>It does not change the timeline's numbers:</strong> the lab curves run in days and the hospital ones in years, so the weeks the timeline shows stay illustrative. <code className="font-mono">experiments/evolution/calibrate.py</code> makes the fit and the summary <code className="font-mono">/api/timeline/</code> returns.
              </p>
              <p className="fs-11 text-3 mb-0">{' '}
                ECDC data: &ldquo;Dataset provided by ECDC based on data provided by public health authorities, scientific institutes or health care providers in the relevant reporting countries and/or by WHO&rdquo; (CC BY 4.0); the fitted curves are this project's adaptation. PLOS data: CC BY 4.0.
              </p>
            </div>
          </div>
          <div className="col-lg-4">
            <div className="info-card h-100">
              <h6 className="card-section-title"><i className="bi bi-bar-chart text-accent me-2"></i>Dataset Statistics</h6>
              <table className="table table-custom table-sm mb-0"><tbody>
                <tr><td className="text-muted">Lab curves</td><td className="fw-600 text-white">5 drugs &times; 4 populations</td></tr>
                <tr><td className="text-muted">Lab time points</td><td className="fw-600 text-white">days 0, 2, 4, 6, 8</td></tr>
                <tr><td className="text-muted">Hospital series</td><td className="fw-600 text-white">31 countries, 2005&ndash;2024</td></tr>
                <tr><td className="text-muted">Used in the fit</td><td className="fw-600 text-white">5 lab + 10 countries</td></tr>
                <tr><td className="text-muted">Median R&sup2;</td><td className="fw-600 text-white">0.91</td></tr>
                <tr><td className="text-muted">Location</td><td className="fw-600 text-white font-mono small">evolution_curves/</td></tr>
              </tbody></table>
            </div>
          </div>
        </div>
      </div>

      {/* ════════════════════════════════════════════════════════════
           BUILT FROM THE DATASETS
           ════════════════════════════════════════════════════════════ */}
      <div className="mb-4">
        <div className="sec-eyebrow"><i className="bi bi-diagram-3 me-2"></i>Built From the Datasets</div>
        <h2 className="sec-title mb-1">Data This Project Made</h2>
        <p className="sec-sub mb-0">Produced by the project's own code from Datasets 1 to 3, so they are not separate datasets. The gene matrix has its own page: <Link to="/genes">Resistance Genes</Link>.</p>
      </div>

      {/* ════════════════════════════════════════════════════════════
           BUILT: Mapped AMR Records
           ════════════════════════════════════════════════════════════ */}
      <div className="mb-5" id="ds-mapped">
        <div className="d-flex align-items-center gap-3 mb-3">
          <div className="step-num fs-5 fw-700" style={{width: '44px', height: '44px'}}><i className="bi bi-link-45deg"></i></div>
          <div>
            <div className="sec-eyebrow">Built from Datasets 1 + 2 · Linking Layer</div>
            <h2 className="sec-title mb-0">Mapped AMR Records</h2>
          </div>
        </div>

        <div className="row g-4">
          <div className="col-lg-8">
            <div className="info-card h-100">
              <h6 className="card-section-title"><i className="bi bi-info-circle text-accent me-2"></i>What This Dataset Contains</h6>
              <p style={{fontSize: '13px', color: 'var(--text-2)', lineHeight: '1.7'}}>{' '}
                This is a <strong>linking table</strong> made by <code className="font-mono">scripts/fasta_amr_map.py</code> that bridges Dataset 1 (AMR phenotype labels) and Dataset 2 (FASTA sequences). Each row from the AMR CSV files is enriched with a <code className="font-mono" style={{color: 'var(--accent2)'}}>fasta_path</code> column pointing to the actual genome FASTA file for that isolate.
              </p>
              <p style={{fontSize: '13px', color: 'var(--text-2)', lineHeight: '1.7'}}>{' '}
                This linkage was essential for training the original K-mer RandomForest model (now retired, see <a href="#ds-fasta">Dataset 2</a>): the model needs both the <strong style={{color: 'var(--rose2)'}}>resistance label</strong> (from Dataset 1) AND the <strong style={{color: 'var(--emerald2)'}}>genome sequence</strong> (from Dataset 2). The mapped records provide both in one place.
              </p>
              <p style={{fontSize: '13px', color: 'var(--text-2)', lineHeight: '1.7'}}>{' '}
                Not every AMR record has a matching FASTA file: 1,683 of the 3,655 taxon files it was built from have genomes. This linkage step keeps only the rows that do.
              </p>

              <h6 className="card-section-title mt-4"><i className="bi bi-diagram-3 text-accent me-2"></i>How the Linkage Works</h6>
              <div className="pipeline-diagram" style={{flexWrap: 'wrap', gap: '12px'}}>
                <div className="pipeline-step">
                  <div className="pipeline-icon"><i className="bi bi-file-earmark-spreadsheet"></i></div>
                  <div className="pipeline-label">AMR CSV<br /><small>Genome ID + Label</small></div>
                </div>
                <div className="pipeline-arrow"><i className="bi bi-arrow-right"></i></div>
                <div className="pipeline-step">
                  <div className="pipeline-icon"><i className="bi bi-search"></i></div>
                  <div className="pipeline-label">Genome ID<br /><small>Lookup key</small></div>
                </div>
                <div className="pipeline-arrow"><i className="bi bi-arrow-right"></i></div>
                <div className="pipeline-step">
                  <div className="pipeline-icon"><i className="bi bi-folder2"></i></div>
                  <div className="pipeline-label">fasta_output/<br /><small>Find FASTA file</small></div>
                </div>
                <div className="pipeline-arrow"><i className="bi bi-arrow-right"></i></div>
                <div className="pipeline-step active-step">
                  <div className="pipeline-icon"><i className="bi bi-file-plus"></i></div>
                  <div className="pipeline-label">Mapped CSV<br /><small>Label + fasta_path</small></div>
                </div>
              </div>

              <h6 className="card-section-title mt-4"><i className="bi bi-table text-accent me-2"></i>Column Schema</h6>
              <div className="table-responsive">
                <table className="table table-custom table-sm mb-0">
                  <thead><tr><th>Column</th><th>Source</th><th>Description</th></tr></thead>
                  <tbody>
                    <tr><td className="font-mono text-accent2">Genome ID</td><td><span className="feature-tag">Dataset 1</span></td><td className="small text-muted">BVBRC genome identifier</td></tr>
                    <tr><td className="font-mono text-accent2">Antibiotic</td><td><span className="feature-tag">Dataset 1</span></td><td className="small text-muted">Antibiotic tested</td></tr>
                    <tr><td className="font-mono" style={{color: 'var(--rose2)'}}>Resistant Phenotype</td><td><span className="feature-tag">Dataset 1</span></td><td className="small text-muted">Ground truth label (R/S/I)</td></tr>
                    <tr><td className="font-mono" style={{color: 'var(--accent2)'}}>Measurement</td><td><span className="feature-tag">Dataset 1</span></td><td className="small text-muted">MIC value string</td></tr>
                    <tr><td className="font-mono" style={{color: 'var(--emerald2)'}}>fasta_path</td><td><span className="feature-tag" style={{background: 'rgba(16,185,129,0.15)', color: 'var(--emerald2)', borderColor: 'rgba(16,185,129,0.3)'}}>Added</span></td><td className="small text-muted">Full file path to the matching FASTA genome file</td></tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="col-lg-4">
            <div className="info-card mb-4">
              <h6 className="card-section-title"><i className="bi bi-bar-chart text-accent me-2"></i>Dataset Statistics</h6>
              <table className="table table-custom table-sm"><tbody>
                <tr><td className="text-muted">Mapped CSV files</td><td className="fw-600 text-white">1,683</td></tr>
                <tr><td className="text-muted">Linked rows</td><td className="fw-600 text-white">110,493</td></tr>
                <tr><td className="text-muted">Genomes linked</td><td className="fw-600 text-white">2,567</td></tr>
                <tr><td className="text-muted">Antibiotics</td><td className="fw-600 text-white">101</td></tr>
                <tr><td className="text-muted">Taxon files with genomes</td><td className="fw-600" style={{color: 'var(--emerald2)'}}>1,683 of 3,655 (46%)</td></tr>
                <tr><td className="text-muted">Original K-mer RF trained on</td><td className="fw-600 text-white">6,002 rows</td></tr>
              </tbody></table>
            </div>

            <div className="info-card">
              <h6 className="card-section-title"><i className="bi bi-gear text-accent me-2"></i>How Used in Training</h6>
              <div className="method-steps">
                <div className="method-step"><span className="step-num" style={{width: '24px', height: '24px', fontSize: '10px'}}>1</span>Load mapped CSVs from <code className="font-mono">mapped_output/</code></div>
                <div className="method-step"><span className="step-num" style={{width: '24px', height: '24px', fontSize: '10px'}}>2</span>For each row, read the FASTA at <code className="font-mono">fasta_path</code></div>
                <div className="method-step"><span className="step-num" style={{width: '24px', height: '24px', fontSize: '10px'}}>3</span>Compute 256-dim k-mer vector from sequence</div>
                <div className="method-step"><span className="step-num" style={{width: '24px', height: '24px', fontSize: '10px'}}>4</span>Combine with antibiotic one-hot + GC features</div>
                <div className="method-step"><span className="step-num" style={{width: '24px', height: '24px', fontSize: '10px'}}>5</span>Train RandomForest on (features, label) pairs</div>
                <div className="method-step"><span className="step-num" style={{width: '24px', height: '24px', fontSize: '10px'}}>6</span>Cache k-mer vectors as <code className="font-mono">*.k4.npy</code> files for speed</div>
              </div>
            </div>
          </div>
        </div>
      </div>


      {/* ════════════════════════════════════════════════════════════
           BUILT: Test Samples
           ════════════════════════════════════════════════════════════ */}
      <div className="mb-5" id="ds-samples">
        <div className="d-flex align-items-center gap-3 mb-3">
          <div className="step-num fs-5 fw-700" style={{width: '44px', height: '44px'}}><i className="bi bi-files"></i></div>
          <div>
            <div className="sec-eyebrow">Copies for testing · not a dataset</div>
            <h2 className="sec-title mb-0">Test Samples</h2>
          </div>
        </div>

        <div className="row g-4">
          <div className="col-lg-6">
            <div className="info-card h-100">
              <h6 className="card-section-title"><i className="bi bi-info-circle text-accent me-2"></i>What These Are</h6>
              <p style={{fontSize: '13px', color: 'var(--text-2)', lineHeight: '1.7'}}>{' '}
                Small copies taken from the data above, not new data: a few AMR files from Dataset 1, the genomes of one species (<em>Acinetobacter nosocomialis</em>) from Dataset 2, and their mapped records.
              </p>
              <p style={{fontSize: '13px', color: 'var(--text-2)', lineHeight: '1.7'}}>{' '}
                They let the system run on a machine without the multi-gigabyte data: when <code className="font-mono">mapped_output/</code> is missing, the K-mer trainer falls back to <code className="font-mono">sample_mapped_output/</code> for a quick demonstration. No reported result comes from them.
              </p>

              <div className="row g-3 mt-2">
                <div className="col-6">
                  <div className="example-box">
                    <div className="example-title">sample_fasta_output/</div>
                    <div className="example-content small">
                      <div className="text-muted">4 FASTA files, 5 MB</div>
                      <div className="text-muted">One species</div>
                      <div className="text-muted">Copied from Dataset 2</div>
                    </div>
                  </div>
                </div>
                <div className="col-6">
                  <div className="example-box">
                    <div className="example-title">sample_mapped_output/ · sample_amr_data/</div>
                    <div className="example-content small">
                      <div className="text-muted">1 mapped CSV, 4 AMR CSVs</div>
                      <div className="text-muted">Trainer demonstration</div>
                      <div className="text-muted">Copied from Dataset 1 and the mapped records</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="col-lg-6">
            <div className="info-card h-100">
              <h6 className="card-section-title"><i className="bi bi-lightbulb text-accent me-2"></i>Using Your Own FASTA File</h6>
              <p style={{fontSize: '13px', color: 'var(--text-2)', lineHeight: '1.7'}}>{' '}
                The system accepts any bacterial FASTA file as input to the <Link to="/predict" style={{color: 'var(--emerald2)'}}>Resistance Prediction</Link> and <Link to="/timeline" style={{color: 'var(--rose2)'}}>Mutation Timeline</Link> pages. You can:
              </p>
              <div className="method-steps">
                <div className="method-step"><span className="step-num" style={{width: '24px', height: '24px', fontSize: '10px'}}>A</span>Use any file from <code className="font-mono">fasta_output/</code> in the project directory</div>
                <div className="method-step"><span className="step-num" style={{width: '24px', height: '24px', fontSize: '10px'}}>B</span>Download a FASTA from NCBI, BVBRC, or UniProt</div>
                <div className="method-step"><span className="step-num" style={{width: '24px', height: '24px', fontSize: '10px'}}>C</span>Paste a raw FASTA sequence in the text box (Paste Sequence tab)</div>
                <div className="method-step"><span className="step-num" style={{width: '24px', height: '24px', fontSize: '10px'}}>D</span>Use the Load Sample button for a built-in <em>E. coli</em> K-12 sequence</div>
              </div>
              <div className="alert-info-custom mt-3" style={{fontSize: '12px', padding: '10px', borderRadius: '8px', background: 'rgba(56,189,248,0.07)', border: '1px solid rgba(56,189,248,0.2)', color: 'var(--accent2)'}}>{' '}
                <i className="bi bi-info-circle me-2"></i>{' '}
                Minimum 100 bp for K-mer prediction, 50 bp for Timeline. Supports .fasta, .fa, .fna formats.
              </div>
            </div>
          </div>
        </div>
      </div>


      {/* ════════════════════════════════════════════════════════════
           MODEL–DATASET MAPPING
           ════════════════════════════════════════════════════════════ */}
      <div className="mb-5">
        <div className="sec-eyebrow"><i className="bi bi-diagram-3 me-2"></i>Model–Dataset Relationships</div>
        <h2 className="sec-title mb-1">Which Model Uses Which Dataset</h2>
        <p className="sec-sub mb-4">The two trained models each learn from different data; the timeline is a simulation that reads only the genome you give it.</p>

        <div className="row g-4">
          <div className="col-lg-4">
            <div className="model-card h-100">
              <div className="d-flex align-items-start gap-3 mb-3">
                <div className="model-icon lgbm-icon"><i className="bi bi-graph-up-arrow"></i></div>
                <div><div className="fw-700 text-white">LightGBM Forecasting</div><div style={{fontSize: '12px', color: 'var(--text-3)'}}>AMR Resistance Classifier</div></div>
              </div>
              <div className="mb-3">
                <div className="text-muted small mb-2">Primary dataset:</div>{' '}
                <span className="feature-tag" style={{background: 'rgba(99,102,241,0.15)', color: 'var(--indigo2)', borderColor: 'rgba(99,102,241,0.3)'}}>Dataset 1  AMR Phenotype CSVs</span>
              </div>
              <div className="method-steps">
                <div className="method-step"><span className="step-num" style={{width: '20px', height: '20px', fontSize: '9px'}}>→</span>14 features from AMR metadata</div>
                <div className="method-step"><span className="step-num" style={{width: '20px', height: '20px', fontSize: '9px'}}>→</span>{m.lgbm.train_rows} training rows</div>
                <div className="method-step"><span className="step-num" style={{width: '20px', height: '20px', fontSize: '9px'}}>→</span>No FASTA sequence needed</div>
              </div>{' '}
              <Link to="/forecast" className="btn btn-model w-100 mt-3"><i className="bi bi-arrow-right-circle me-2"></i>Use AMR Forecasting</Link>
            </div>
          </div>
          <div className="col-lg-4">
            <div className="model-card h-100">
              <div className="d-flex align-items-start gap-3 mb-3">
                <div className="model-icon kmer-icon"><i className="bi bi-dna"></i></div>
                <div><div className="fw-700 text-white">K-mer LightGBM</div><div style={{fontSize: '12px', color: 'var(--text-3)'}}>Genomic Resistance Predictor</div></div>
              </div>
              <div className="mb-3">
                <div className="text-muted small mb-2">Datasets used:</div>{' '}
                <span className="feature-tag" style={{background: 'rgba(245,158,11,0.15)', color: 'var(--amber2)', borderColor: 'rgba(245,158,11,0.3)'}}>Dataset 3  Complete genomes</span>{' '}
                <span className="feature-tag ms-1">Dataset 1 (labels)</span>
              </div>
              <div className="method-steps">
                <div className="method-step"><span className="step-num" style={{width: '20px', height: '20px', fontSize: '9px'}}>→</span>256 k-mer features per complete genome</div>
                <div className="method-step"><span className="step-num" style={{width: '20px', height: '20px', fontSize: '9px'}}>→</span>{m.kmer.train_rows} genome–antibiotic pairs</div>
                <div className="method-step"><span className="step-num" style={{width: '20px', height: '20px', fontSize: '9px'}}>→</span>Requires a complete assembly at inference (at least 100,000 bp)</div>
              </div>{' '}
              <Link to="/predict" className="btn btn-model btn-model-green w-100 mt-3"><i className="bi bi-arrow-right-circle me-2"></i>Use Resistance Prediction</Link>
            </div>
          </div>
          <div className="col-lg-4">
            <div className="model-card h-100">
              <div className="d-flex align-items-start gap-3 mb-3">
                <div className="model-icon timeline-icon"><i className="bi bi-activity"></i></div>
                <div><div className="fw-700 text-white">Mutation Timeline</div><div style={{fontSize: '12px', color: 'var(--text-3)'}}>Biological Simulation</div></div>
              </div>
              <div className="mb-3">
                <div className="text-muted small mb-2">Datasets used at inference:</div>{' '}
                <span className="feature-tag" style={{background: 'rgba(16,185,129,0.15)', color: 'var(--emerald2)', borderColor: 'rgba(16,185,129,0.3)'}}>Your FASTA</span>{' '}
                <span className="feature-tag ms-1">Hand-set drug profiles</span>
              </div>
              <div className="method-steps">
                <div className="method-step"><span className="step-num" style={{width: '20px', height: '20px', fontSize: '9px'}}>→</span>GC content from FASTA</div>
                <div className="method-step"><span className="step-num" style={{width: '20px', height: '20px', fontSize: '9px'}}>→</span>Hotspot detection on sequence</div>
                <div className="method-step"><span className="step-num" style={{width: '20px', height: '20px', fontSize: '9px'}}>→</span>Logistic growth simulation</div>
              </div>{' '}
              <Link to="/timeline" className="btn btn-model btn-model-red w-100 mt-3"><i className="bi bi-arrow-right-circle me-2"></i>View Mutation Timeline</Link>
            </div>
          </div>
        </div>
      </div>


      {/* ════════════════════════════════════════════════════════════
           HOW TO USE THE SYSTEM
           ════════════════════════════════════════════════════════════ */}
      <div className="mb-5">
        <div className="sec-eyebrow"><i className="bi bi-lightning-charge me-2"></i>System Guide</div>
        <h2 className="sec-title mb-1">How to Use This System</h2>
        <p className="sec-sub mb-4">Step-by-step guide for the two prediction modes, the simulation, and training.</p>

        <div className="row g-4">

          {/* Mode 1 */}
          <div className="col-md-6 col-lg-3">
            <div className="glass-card h-100">
              <div className="model-icon lgbm-icon mb-3" style={{width: '44px', height: '44px'}}><i className="bi bi-graph-up-arrow"></i></div>
              <h6 className="fw-700 text-white mb-2">Mode 1: AMR Forecasting</h6>
              <p style={{fontSize: '12px', color: 'var(--text-2)'}}>Predict resistance from metadata  <strong>no genome file needed.</strong></p>
              <div className="method-steps mt-3">
                <div className="method-step"><span className="step-num" style={{width: '22px', height: '22px', fontSize: '10px'}}>1</span>Go to <Link to="/forecast">AMR Forecasting</Link></div>
                <div className="method-step"><span className="step-num" style={{width: '22px', height: '22px', fontSize: '10px'}}>2</span>Select antibiotic from dropdown</div>
                <div className="method-step"><span className="step-num" style={{width: '22px', height: '22px', fontSize: '10px'}}>3</span>Enter MIC value &amp; sign (optional)</div>
                <div className="method-step"><span className="step-num" style={{width: '22px', height: '22px', fontSize: '10px'}}>4</span>Select organism or enter genus/species</div>
                <div className="method-step"><span className="step-num" style={{width: '22px', height: '22px', fontSize: '10px'}}>5</span>Click <strong>Predict Resistance</strong></div>
              </div>
              <div className="mt-3">{' '}
                <div className="feature-tag">Input: metadata</div>{' '}
                <div className="feature-tag mt-1">Output: R/S + probability</div>
              </div>
            </div>
          </div>

          {/* Mode 2 */}
          <div className="col-md-6 col-lg-3">
            <div className="glass-card h-100">
              <div className="model-icon kmer-icon mb-3" style={{width: '44px', height: '44px'}}><i className="bi bi-dna"></i></div>
              <h6 className="fw-700 text-white mb-2">Mode 2: K-mer Prediction</h6>
              <p style={{fontSize: '12px', color: 'var(--text-2)'}}>Predict resistance from a genome FASTA file.</p>
              <div className="method-steps mt-3">
                <div className="method-step"><span className="step-num" style={{width: '22px', height: '22px', fontSize: '10px'}}>1</span>Go to <Link to="/predict">Resistance Prediction</Link></div>
                <div className="method-step"><span className="step-num" style={{width: '22px', height: '22px', fontSize: '10px'}}>2</span>Select antibiotic</div>
                <div className="method-step"><span className="step-num" style={{width: '22px', height: '22px', fontSize: '10px'}}>3</span>Upload .fasta file or paste sequence</div>
                <div className="method-step"><span className="step-num" style={{width: '22px', height: '22px', fontSize: '10px'}}>4</span>Adjust threshold (default 0.5)</div>
                <div className="method-step"><span className="step-num" style={{width: '22px', height: '22px', fontSize: '10px'}}>5</span>Click <strong>Predict Resistance</strong></div>
              </div>
              <div className="mt-3">{' '}
                <div className="feature-tag">Input: FASTA sequence</div>{' '}
                <div className="feature-tag mt-1">Output: R/S + k-mer chart</div>
              </div>
            </div>
          </div>

          {/* Mode 3 */}
          <div className="col-md-6 col-lg-3">
            <div className="glass-card h-100">
              <div className="model-icon timeline-icon mb-3" style={{width: '44px', height: '44px'}}><i className="bi bi-activity"></i></div>
              <h6 className="fw-700 text-white mb-2">Mode 3: Mutation Timeline</h6>
              <p style={{fontSize: '12px', color: 'var(--text-2)'}}>Simulate week-by-week resistance evolution.</p>
              <div className="method-steps mt-3">
                <div className="method-step"><span className="step-num" style={{width: '22px', height: '22px', fontSize: '10px'}}>1</span>Go to <Link to="/timeline">Mutation Timeline</Link></div>
                <div className="method-step"><span className="step-num" style={{width: '22px', height: '22px', fontSize: '10px'}}>2</span>Select antibiotic</div>
                <div className="method-step"><span className="step-num" style={{width: '22px', height: '22px', fontSize: '10px'}}>3</span>Set number of simulation weeks</div>
                <div className="method-step"><span className="step-num" style={{width: '22px', height: '22px', fontSize: '10px'}}>4</span>Upload FASTA or paste sequence</div>
                <div className="method-step"><span className="step-num" style={{width: '22px', height: '22px', fontSize: '10px'}}>5</span>Click <strong>Generate Timeline</strong></div>
              </div>
              <div className="mt-3">{' '}
                <div className="feature-tag">Input: FASTA + weeks</div>{' '}
                <div className="feature-tag mt-1">Output: evolution chart</div>
              </div>
            </div>
          </div>

          {/* Mode 4: Training */}
          <div className="col-md-6 col-lg-3">
            <div className="glass-card h-100">
              <div className="model-icon lgbm-icon mb-3" style={{width: '44px', height: '44px'}}><i className="bi bi-cpu"></i></div>
              <h6 className="fw-700 text-white mb-2">Mode 4: Training</h6>
              <p style={{fontSize: '12px', color: 'var(--text-2)'}}>Retrain models on your local data (optional, as models are already pre-trained).</p>
              <div className="method-steps mt-3">
                <div className="method-step"><span className="step-num" style={{width: '22px', height: '22px', fontSize: '10px'}}>A</span>Via UI: <Link to="/train">Train Models</Link> page</div>
                <div className="method-step"><span className="step-num" style={{width: '22px', height: '22px', fontSize: '10px'}}>B</span>Via CLI in <code className="font-mono">backend/</code> folder</div>
                <div className="method-step"><span className="step-num" style={{width: '22px', height: '22px', fontSize: '10px'}}>C</span><code className="font-mono small">python train_models.py --model all</code></div>
                <div className="method-step"><span className="step-num" style={{width: '22px', height: '22px', fontSize: '10px'}}>D</span>Saved to <code className="font-mono small">trained_models/candidates/</code>; the site keeps its model until one is promoted</div>
              </div>
              <div className="mt-3">{' '}
                <div className="feature-tag">LightGBM: ~4 min</div>{' '}
                <div className="feature-tag mt-1">K-mer RF: ~1 hour</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Input Format Reference ─────────────────────────────────── */}
      <div className="glass-card mb-5">
        <h5 className="fw-700 mb-1"><i className="bi bi-code text-accent me-2"></i>Input Format Reference</h5>
        <p style={{fontSize: '13px', color: 'var(--text-3)', marginBottom: '20px'}}>Quick reference for the accepted inputs on the Forecasting, Prediction and Timeline pages.</p>
        <div className="row g-4">
          <div className="col-md-4">
            <div className="example-box">
              <div className="example-title" style={{color: 'var(--indigo2)'}}>AMR Forecasting Inputs</div>
              <div className="example-content small">
                <div className="font-mono" style={{color: 'var(--accent2)'}}>antibiotic:</div>
                <div className="text-muted ms-2">Any drug in the dropdown, which lists only the drugs the loaded model knows (e.g., "ciprofloxacin")</div>
                <div className="font-mono mt-2" style={{color: 'var(--accent2)'}}>mic_sign:</div>
                <div className="text-muted ms-2">&lt;=, &lt;, =, &gt;, &gt;= (leave blank if unknown)</div>
                <div className="font-mono mt-2" style={{color: 'var(--accent2)'}}>mic_value:</div>
                <div className="text-muted ms-2">Numeric mg/L (e.g., 4.0, 0.25, 32)</div>
                <div className="font-mono mt-2" style={{color: 'var(--accent2)'}}>taxon_id:</div>
                <div className="text-muted ms-2">NCBI Taxonomy ID (e.g., 562 for E. coli)</div>
                <div className="font-mono mt-2" style={{color: 'var(--accent2)'}}>genus / species:</div>
                <div className="text-muted ms-2">E.g., "Escherichia" / "coli"</div>
              </div>
            </div>
          </div>
          <div className="col-md-4">
            <div className="example-box">
              <div className="example-title" style={{color: 'var(--emerald2)'}}>FASTA File Inputs</div>
              <div className="example-content small">
                <div className="font-mono" style={{color: 'var(--accent2)'}}>Accepted formats:</div>
                <div className="text-muted ms-2">.fasta, .fa, .fna, .ffn</div>
                <div className="font-mono mt-2" style={{color: 'var(--accent2)'}}>Minimum size:</div>
                <div className="text-muted ms-2">100,000 bp, a complete assembly (Resistance Prediction); 50 bp (Timeline)</div>
                <div className="font-mono mt-2" style={{color: 'var(--accent2)'}}>Max analyzed:</div>
                <div className="text-muted ms-2">The whole genome (Resistance Prediction), 200,000 bp (Timeline)</div>
                <div className="font-mono mt-2" style={{color: 'var(--accent2)'}}>Nucleotides:</div>
                <div className="text-muted ms-2">A, T, C, G only; ambiguous bases are removed</div>
                <div className="font-mono mt-2" style={{color: 'var(--accent2)'}}>Multi-contig:</div>
                <div className="text-muted ms-2">Supported: k-mers are counted within each contig (Resistance Prediction); contigs joined (Timeline)</div>
              </div>
            </div>
          </div>
          <div className="col-md-4">
            <div className="example-box">
              <div className="example-title" style={{color: 'var(--amber2)'}}>Interpreting Results</div>
              <div className="example-content small">
                <div className="font-mono" style={{color: 'var(--rose2)'}}>RESISTANT:</div>
                <div className="text-muted ms-2">Probability ≥ threshold. Consider alternative antibiotics.</div>
                <div className="font-mono mt-2" style={{color: 'var(--emerald2)'}}>SUSCEPTIBLE:</div>
                <div className="text-muted ms-2">Probability &lt; threshold. Standard dosing likely effective.</div>
                <div className="font-mono mt-2" style={{color: 'var(--accent2)'}}>Probability:</div>
                <div className="text-muted ms-2">Model's confidence that this isolate is resistant (0–100%).</div>
                <div className="font-mono mt-2" style={{color: 'var(--accent2)'}}>Threshold:</div>
                <div className="text-muted ms-2">Default {m.lgbm.threshold || 'not measured'} (LightGBM), {m.kmer.threshold || 'not measured'} (K-mer), the thresholds each model was evaluated at. Adjustable.</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Source & Citation ──────────────────────────────────────── */}
      <div className="glass-card">
        <h5 className="fw-700 mb-1"><i className="bi bi-journal-text text-accent me-2"></i>Data Source &amp; Citation</h5>
        <p style={{fontSize: '13px', color: 'var(--text-2)', marginBottom: '16px'}}>The AMR phenotype data and the complete assemblies come from <strong>BV-BRC (Bacterial and Viral Bioinformatics Resource Center)</strong>, formerly PATRIC; the partial FASTA files from NCBI GenBank.</p>
        <div className="row g-3">
          <div className="col-md-6">
            <div className="example-box">
              <div className="example-title">BVBRC / PATRIC Database</div>
              <div className="example-content small">
                <div className="text-muted">Olson, R.D. et al. (2023). PATRIC, the NCBI taxonomic database... <em>Nucleic Acids Research</em>, 51(D1), D678–D689.</div>
                <div className="mt-2"><span className="feature-tag">Open Access</span> <span className="feature-tag">Public Domain</span></div>
              </div>
            </div>
          </div>
          <div className="col-md-6">
            <div className="example-box">
              <div className="example-title">WHO AMR Data</div>
              <div className="example-content small">
                <div className="text-muted">WHO Global Antimicrobial Resistance and Use Surveillance System (GLASS) Report 2022. World Health Organization, Geneva.</div>
                <div className="mt-2"><span className="feature-tag">EUCAST Breakpoints</span> <span className="feature-tag">CLSI Standards</span></div>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
    </>
  );
}
