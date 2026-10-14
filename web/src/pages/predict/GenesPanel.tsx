/* The resistance genes behind a /predict result (_genes_panel.html; format §2).
     genes_found absent  -> the model does not search for genes: no panel
     genes_found == []   -> searched, nothing found
     genes_found == [..] -> genes linked to the drug's class first (`relevant`), then the rest */
import type { Gene, PredictResult } from './types';

function Chip({ g, linked }: { g: Gene; linked: boolean }) {
  // tooltip: the element's full name and subclass when the model sends them
  const sub = g.subclass || g.drug_class;
  return (
    <span className={'gene-chip' + (linked ? ' gene-chip-linked' : '')} title={(g.name || g.gene) + (sub ? ` (${sub})` : '')}>
      <span className="font-mono">{g.gene}</span>{' '}
      <span className="gene-chip-meta">{g.type === 'point_mutation' ? 'mutation' : 'gene'}{g.drug_class ? ` · ${g.drug_class}` : ''}</span>
    </span>
  );
}

// Jinja's sort, which the Flask page used, ignores case
const byGene = (a: Gene, b: Gene) => {
  const x = a.gene.toLowerCase(), y = b.gene.toLowerCase();
  return x < y ? -1 : x > y ? 1 : 0;
};
const count = (n: number) => `${n} ${n === 1 ? 'gene or mutation' : 'genes and mutations'}`;

/** The sentence above the chips: what the genes say about the call. */
export function genesSummary(result: PredictResult, linked: Gene[], scored: boolean): React.ReactNode {
  const genes = result.genes_found || [];
  const drugClass = linked[0]?.drug_class || '';
  if (!genes.length) return 'The genome was searched and no known resistance gene or mutation was found.';
  if (linked.length && result.prediction === 'Resistant') {
    return <>The genome carries {count(linked.length)} linked to {drugClass} resistance, which supports the <strong>Resistant</strong> call.</>;
  }
  if (linked.length) {
    return <>The model called this <strong>Susceptible</strong>, but the genome carries {count(linked.length)} linked to {drugClass} resistance. Treat this call with care.</>;
  }
  if (scored && result.prediction === 'Resistant') {
    return `No gene or mutation linked to ${result.antibiotic}'s drug class was found, so the Resistant call comes from other features of the genome.`;
  }
  if (scored) {
    return `No gene or mutation linked to ${result.antibiotic}'s drug class was found, which agrees with the Susceptible call.`;
  }
  return 'Resistance genes and mutations found in this genome.';
}

export default function GenesPanel({ result }: { result: PredictResult }) {
  const genes = result.genes_found;
  if (genes === undefined || genes === null) return null;
  const scored = genes.some(g => g.relevant !== undefined);
  const linked = genes.filter(g => g.relevant).sort(byGene);
  const others = genes.filter(g => !g.relevant).sort(byGene);

  return (
    <div className="info-card mb-4">
      <h6 className="card-section-title">
        <i className="bi bi-bacteria text-emerald2 me-2"></i>Resistance genes found{' '}
        <span className="feature-tag ms-2">{genes.length}</span>
      </h6>
      <p className="fs-13 mb-3">{genesSummary(result, linked, scored)}</p>
      {linked.length > 0 && (
        <>
          <div className="gene-group-label">Linked to this drug's class</div>
          <div className="d-flex flex-wrap gap-2 mb-3">{linked.map(g => <Chip key={g.gene} g={g} linked />)}</div>
        </>
      )}
      {others.length > 0 && (
        <>
          {scored && <div className="gene-group-label">Other resistance genes in this genome</div>}
          <div className="d-flex flex-wrap gap-2 mb-3">{others.map(g => <Chip key={g.gene} g={g} linked={false} />)}</div>
        </>
      )}
      <div className="text-muted fs-11">
        Found with NCBI AMRFinderPlus. A gene being present is evidence, not proof: it may not be expressed,
        and resistance can also come from mechanisms it does not detect.
      </div>
    </div>
  );
}
