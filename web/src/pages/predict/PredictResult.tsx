/* One genome's result on /predict: the call, the species the gene model
   identified, the resistance genes, downloads, genome statistics and, for the
   k-mer model, its 4-mers. */
import { useCallback, useRef } from 'react';
import ExportBar from '../../components/ExportBar';
import Plot, { type Figure, type PlotElement, type PlotTheme } from '../../components/Plot';
import { pyFixed, pyFloat, thousands } from '../../lib/metrics';
import GenesPanel from './GenesPanel';
import type { PredictInputs, PredictResult as Result } from './types';

function KmerChart({ kmers, chartRef }: { kmers: NonNullable<Result['top_kmers']>; chartRef: React.Ref<PlotElement | null> }) {
  const figure = useCallback((t: PlotTheme): Figure => ({
    data: [{
      type: 'bar',
      x: kmers.slice(0, 20).map(k => k.kmer),
      y: kmers.slice(0, 20).map(k => k.frequency),
      marker: { color: 'rgba(99,102,241,0.82)', line: { color: 'rgba(79,70,229,1)', width: 1 } },
      hovertemplate: '<b>%{x}</b><br>Frequency: %{y:.5f}<extra></extra>',
    }],
    layout: {
      paper_bgcolor: t.paper_bgcolor,
      plot_bgcolor: t.plot_bgcolor,
      margin: { t: 10, b: 50, l: 60, r: 10 },
      xaxis: { tickfont: { family: "'JetBrains Mono',monospace", size: 10, color: t.tickColor }, gridcolor: t.gridColor, linecolor: t.gridColor },
      yaxis: { tickfont: { color: t.tickColor, size: 10 }, gridcolor: t.gridColor, title: { text: 'Frequency', font: { color: t.tickColor, size: 11 } } },
      font: { family: t.fontFamily },
    },
  }), [kmers]);
  return <Plot id="kmerChart" className="chart-250" figure={figure} ref={chartRef} />;
}

/** "Identified as E. coli", "... (species unclear)", or none found. */
function Species({ found, long }: { found: NonNullable<Result['species_detected']>; long?: boolean }) {
  if (found.species) return <>{long && ' Identified as '}<em>{found.species}</em></>;
  if (found.genus) return <>{long && ' Identified as '}<em>{found.genus}</em> (species unclear)</>;
  return <>{long ? ' Species not identified from the genome' : 'Not identified'}</>;
}

interface Props {
  result: Result;
  inputs: PredictInputs;
  /** the agreed sample response, not a prediction (/predict/sample) */
  sample?: boolean;
}

export default function PredictResult({ result, inputs, sample }: Props) {
  const chart = useRef<PlotElement | null>(null);
  const resistant = result.prediction === 'Resistant';
  const kmers = result.top_kmers?.length ? result.top_kmers : null;
  const found = result.species_detected && typeof result.species_detected === 'object' ? result.species_detected : null;
  const gc = result.gc_content;

  return (
    <>
      {result.model_used?.startsWith('Heuristic') && (
        <div className="alert alert-warning-custom mb-3" role="status">
          <i className="bi bi-exclamation-triangle me-2"></i><strong>This is not a model prediction.</strong>{' '}
          {result.model_used === 'Heuristic fallback' ? 'The trained model failed on this input' : 'No trained model is loaded'},
          so the result comes from a GC-content rule of thumb. Do not rely on it.
        </div>
      )}
      {result.warning && (
        <div className="alert alert-warning-custom mb-3" role="status">
          <i className="bi bi-exclamation-triangle me-2"></i><strong>Resistance genes were not searched for this genome.</strong>{' '}
          {result.warning}
        </div>
      )}
      {result.antibiotic_known === false && (
        <div className="alert alert-warning-custom mb-3" role="status">
          <i className="bi bi-exclamation-triangle me-2"></i><strong>The model never saw {result.antibiotic} in training.</strong>{' '}
          The call reflects the genome alone, not this drug.
        </div>
      )}
      {sample && (
        <div className="alert alert-warning-custom mb-3" role="status">
          <i className="bi bi-eye me-2"></i><strong>Sample response, not a real prediction.</strong>{' '}
          This is <code>progress/formats/genome_response.sample.json</code>, shown to preview the layout.
        </div>
      )}

      <div className={`result-hero ${resistant ? 'result-resistant' : 'result-susceptible'} mb-4`}>
        <div className="result-hero-content">
          <div className="result-icon-large"><i className={resistant ? 'bi bi-shield-x' : 'bi bi-shield-check'}></i></div>
          <div>
            <div className="result-label">{(result.model_used || '').includes('K-mer') ? 'K-mer Genome Analysis' : 'Genome Analysis'}</div>
            <div className="result-main-label">{result.prediction}</div>
            <div className="result-sub">{result.antibiotic} | Confidence: {pyFloat(result.confidence)}%</div>
            {found && (
              <div className="result-sub mt-1" data-species>
                <i className="bi bi-bacteria me-1"></i><Species found={found} long />
              </div>
            )}
          </div>
          <div className="ms-auto text-end">
            <div className="result-prob-label">Resistance Probability</div>
            <div className="result-prob-val">{pyFixed(result.probability * 100, 1)}%</div>
            <div className="small text-muted">{result.model_used}</div>
          </div>
        </div>
        <div className="prob-bar-wrap mt-3">
          <div className="prob-bar-bg">
            <div className={`prob-bar-fill ${resistant ? 'resistant-fill' : 'susceptible-fill'}`}
                 style={{ width: `${(result.probability * 100).toFixed(1)}%` }}></div>
          </div>
          <div className="d-flex justify-content-between mt-1">
            <small className="text-success fw-500">Susceptible</small>
            <small className="text-danger fw-500">Resistant</small>
          </div>
        </div>
      </div>

      <GenesPanel result={result} />

      <ExportBar page="predict" result={result} inputs={inputs} chart={kmers ? chart : undefined} />

      <div className="row g-4 mb-4">
        <div className="col-md-6">
          <div className="info-card h-100">
            <h6 className="card-section-title"><i className="bi bi-diagram-3 text-accent me-2"></i>Genome Statistics</h6>
            <table className="table table-custom table-sm">
              <tbody>
                <tr><td className="text-muted">Sequence Length</td><td className="fw-500 font-mono">{thousands(result.sequence_length)} bp</td></tr>
                <tr><td className="text-muted">GC Content</td><td className="fw-500">{gc ?? 'not reported'}{gc != null && '%'}</td></tr>
                <tr><td className="text-muted">Antibiotic</td><td className="fw-500 text-capitalize">{result.antibiotic}</td></tr>
                <tr><td className="text-muted">Model</td><td className="fw-500 small">{result.model_used}</td></tr>
                {found && (
                  <tr><td className="text-muted">Species (from the genome)</td><td className="fw-500 small"><Species found={found} /></td></tr>
                )}
                {(result.genes_found === undefined || result.genes_found === null) && (
                  <tr><td className="text-muted">Resistance genes</td><td className="small text-muted">
                    {result.warning ? 'Not searched: the gene search failed on this genome, so the k-mer model answered'
                                    : "Not searched: this model reads the genome's k-mer composition, not its genes"}
                  </td></tr>
                )}
              </tbody>
            </table>
            {gc != null && (
              <div className="mt-2">
                <div className="d-flex justify-content-between mb-1">
                  <small className="text-muted">GC Content Distribution</small>
                  <small className="fw-500">{gc}%</small>
                </div>
                <div className="prob-bar-bg">
                  <div className="prob-bar-fill gc-fill" style={{ width: `${Number(gc).toFixed(1)}%` }}></div>
                </div>
                <div className="d-flex justify-content-between mt-1">
                  <small className="text-muted">0% AT-rich</small>
                  <small className="text-muted">100% GC-rich</small>
                </div>
              </div>
            )}
          </div>
        </div>

        {kmers && (
          <div className="col-md-6">
            <div className="info-card h-100">
              <h6 className="card-section-title"><i className="bi bi-grid-3x3 text-accent me-2"></i>Top 8 Discriminative 4-mers</h6>
              <div className="kmer-list">
                {kmers.slice(0, 8).map(km => (
                  <div className="kmer-item" key={km.kmer}>
                    <span className="kmer-seq font-mono">{km.kmer}</span>
                    <div className="kmer-bar-wrap">
                      <div className="kmer-bar" style={{ width: `${Math.trunc(km.frequency / kmers[0].frequency * 100)}%` }}></div>
                    </div>
                    <span className="kmer-freq">{pyFixed(km.frequency, 4)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {kmers && (
        <div className="info-card">
          <h6 className="card-section-title"><i className="bi bi-bar-chart text-accent me-2"></i>4-mer Frequency Spectrum (Top 20)</h6>
          <KmerChart kmers={kmers} chartRef={chart} />
        </div>
      )}
    </>
  );
}
