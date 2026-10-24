import { fireEvent, render, screen } from '@testing-library/react';
import Predict from './Predict';
import GenesPanel from './predict/GenesPanel';
import PredictResult from './predict/PredictResult';
import { SAMPLE_FASTA } from './predict/PredictForm';
import type { PredictResult as Result } from './predict/types';
import { HEALTH, mockBackend, renderPage } from '../test-utils';
import { ToastProvider } from '../components/Toasts';

vi.mock('plotly.js-dist-min', () => ({ default: { react: vi.fn(), purge: vi.fn(), toImage: vi.fn(async () => '') } }));

afterEach(() => { vi.unstubAllGlobals(); sessionStorage.clear(); });

const KMER: Result = {
  antibiotic: 'ciprofloxacin', prediction: 'Susceptible', probability: 0.101, confidence: 89.9, threshold: 0.43,
  sequence_length: 2889905, gc_content: 39.61, model_used: 'LightGBM on 4-mers (G_kmer_deploy)',
  top_kmers: [{ kmer: 'AAAA', frequency: 0.0141 }, { kmer: 'TTTT', frequency: 0.0135 }],
};
const GENES: Result = {
  ...KMER, prediction: 'Resistant', model_used: 'LightGBM on AMRFinderPlus resistance genes (G_genes_deploy)',
  top_kmers: undefined, gc_content: null,
  species_detected: { species: 'Escherichia coli', genus: 'Escherichia' },
  genes_found: [
    { gene: 'parC_S80I', drug_class: 'quinolone', type: 'point_mutation', relevant: true },
    { gene: 'blaCTX-M-15', drug_class: 'beta-lactam', type: 'gene', relevant: false, name: 'CTX-M-15', subclass: 'cephalosporin' },
    { gene: 'gyrA_S83L', drug_class: 'quinolone', type: 'point_mutation', relevant: true },
  ],
};

const show = (r: Result) => render(<ToastProvider><PredictResult result={r} inputs={{ antibiotic: r.antibiotic, threshold: '' }} /></ToastProvider>);

function backend(extra: Record<string, { status?: number; body: unknown }> = {}) {
  return mockBackend({
    'health/': { body: HEALTH },
    'antibiotics/': { body: { antibiotics: ['ciprofloxacin'] } },
    'predict/': { body: KMER },
    ...extra,
  });
}

describe('genes panel', () => {
  it('is not shown for a model that does not search genes', () => {
    const { container } = render(<GenesPanel result={KMER} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('says so when the genome was searched and nothing found', () => {
    render(<GenesPanel result={{ ...GENES, genes_found: [] }} />);
    expect(screen.getByText(/no known resistance gene or mutation was found/)).toBeInTheDocument();
  });

  it('puts the genes linked to the drug first, sorted, and explains the call', () => {
    render(<GenesPanel result={GENES} />);
    const chips = Array.from(document.querySelectorAll('.gene-chip .font-mono')).map(e => e.textContent);
    expect(chips).toEqual(['gyrA_S83L', 'parC_S80I', 'blaCTX-M-15']);
    expect(document.querySelectorAll('.gene-chip-linked')).toHaveLength(2);
    expect(screen.getByText(/2 genes and mutations/).textContent).toMatch(/linked to quinolone resistance, which supports the Resistant call/);
    expect(document.querySelector('.gene-chip[title="CTX-M-15 (cephalosporin)"]')).not.toBeNull();
  });

  it('warns when the genes disagree with a Susceptible call', () => {
    render(<GenesPanel result={{ ...GENES, prediction: 'Susceptible' }} />);
    expect(screen.getByText(/Treat this call with care/)).toBeInTheDocument();
  });

  it('orders gene names as the Flask page did, ignoring case', () => {
    render(<GenesPanel result={{ ...GENES, genes_found: [{ gene: 'tet(A)' }, { gene: 'Aac' }, { gene: 'bla' }] }} />);
    expect(Array.from(document.querySelectorAll('.gene-chip .font-mono')).map(e => e.textContent)).toEqual(['Aac', 'bla', 'tet(A)']);
  });
});

describe('predict result', () => {
  it('shows the gene model’s species and no k-mer cards', () => {
    show(GENES);
    expect(document.querySelector('[data-species]')?.textContent).toMatch(/Identified as Escherichia coli/);
    expect(screen.queryByText(/Top 8 Discriminative 4-mers/)).toBeNull();
    expect(screen.queryByRole('button', { name: /Chart \(PNG\)/ })).toBeNull();
    expect(screen.getByText('not reported')).toBeInTheDocument();
  });

  it('shows the k-mer model’s 4-mers and says genes were not searched', () => {
    show(KMER);
    expect(screen.getByText('Top 8 Discriminative 4-mers')).toBeInTheDocument();
    expect(screen.getByText('2,889,905 bp')).toBeInTheDocument();
    expect(screen.getByText(/Not searched: this model reads the genome's k-mer composition/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Chart \(PNG\)/ })).toBeInTheDocument();
  });

  it('explains a failed gene search and an unknown antibiotic', () => {
    show({ ...KMER, warning: 'AMRFinderPlus timed out.', antibiotic_known: false });
    expect(screen.getByText('Resistance genes were not searched for this genome.')).toBeInTheDocument();
    expect(screen.getByText(/the gene search failed on this genome/)).toBeInTheDocument();
    expect(screen.getByText('The model never saw ciprofloxacin in training.')).toBeInTheDocument();
  });
});

describe('Predict page', () => {
  it('asks for a genome before sending anything', async () => {
    const calls = backend();
    renderPage(<Predict />, '/predict');
    await screen.findByRole('option', { name: 'Ciprofloxacin' });
    fireEvent.change(screen.getByLabelText(/^Antibiotic/), { target: { value: 'ciprofloxacin' } });
    fireEvent.click(screen.getByRole('button', { name: /Predict Resistance/ }));
    expect(screen.getByText('Upload a FASTA file or paste a sequence before predicting.')).toBeVisible();
    expect(calls.some(c => c.url.endsWith('/predict/'))).toBe(false);
  });

  it('sends a pasted sequence as JSON and shows the refusal', async () => {
    const calls = backend({ 'predict/': { status: 400, body: { error: 'genome too short (505 bp): upload a complete assembly' } } });
    renderPage(<Predict />, '/predict');
    await screen.findByRole('option', { name: 'Ciprofloxacin' });
    fireEvent.change(screen.getByLabelText(/^Antibiotic/), { target: { value: 'ciprofloxacin' } });
    fireEvent.click(screen.getByRole('button', { name: 'Load Sample' }));
    expect(screen.getByLabelText(/^FASTA Sequence/)).toHaveValue(SAMPLE_FASTA);
    fireEvent.click(screen.getByRole('button', { name: /Predict Resistance/ }));
    expect(await screen.findByText(/genome too short/)).toBeInTheDocument();
    const body = JSON.parse(String(calls.find(c => c.url.endsWith('/predict/'))?.init?.body));
    expect(body).toEqual({ fasta_text: SAMPLE_FASTA, antibiotic: 'ciprofloxacin', threshold: '0.43' });
    expect(screen.getByText('Upload a Bacterial Genome')).toBeInTheDocument();
  });

  it('uploads a file with the antibiotic and threshold', async () => {
    const calls = backend();
    renderPage(<Predict />, '/predict');
    await screen.findByRole('option', { name: 'Ciprofloxacin' });
    fireEvent.change(screen.getByLabelText(/^Antibiotic/), { target: { value: 'ciprofloxacin' } });
    const file = new File(['>g\nACGT\n'], 'genome.fna');
    fireEvent.change(screen.getByLabelText(/^FASTA File/), { target: { files: [file] } });
    expect(screen.getByText('genome.fna')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Predict Resistance/ }));
    expect(await screen.findByText('Susceptible', { selector: '.result-main-label' })).toBeInTheDocument();
    const form = calls.find(c => c.url.endsWith('/predict/'))?.init?.body as FormData;
    expect(form.get('fasta_file')).toBeInstanceOf(File);
    expect(form.get('antibiotic')).toBe('ciprofloxacin');
    expect(form.get('threshold')).toBe('0.43');
  });

  it('refuses a file over 20 MB without uploading it', async () => {
    const calls = backend();
    renderPage(<Predict />, '/predict');
    await screen.findByRole('option', { name: 'Ciprofloxacin' });
    fireEvent.change(screen.getByLabelText(/^Antibiotic/), { target: { value: 'ciprofloxacin' } });
    const big = new File(['x'], 'big.fna');
    Object.defineProperty(big, 'size', { value: 21 * 1024 * 1024 });
    fireEvent.change(screen.getByLabelText(/^FASTA File/), { target: { files: [big] } });
    fireEvent.click(screen.getByRole('button', { name: /Predict Resistance/ }));
    expect(await screen.findByText('The file is too large: the limit is 20 MB.')).toBeInTheDocument();
    expect(calls.some(c => c.url.endsWith('/predict/'))).toBe(false);
  });
});
