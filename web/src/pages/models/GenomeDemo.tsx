/* The genome split illustration on /models (renderGenomeDemos in models.js):
   six genomes of twelve antibiotic tests each. A random row split puts rows of
   one genome on both sides; a genome-grouped split never does. */
const N_GENOMES = 6, N_ROWS = 12;

/** Which cells are test rows, per genome; the same seeded draw as models.js. */
export function demoRows(mode: 'random' | 'grouped'): boolean[][] {
  let seed = 7;
  const rand = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  return Array.from({ length: N_GENOMES }, (_, gi) =>
    Array.from({ length: N_ROWS }, () => (mode === 'random' ? rand() < 0.2 : gi === 1 || gi === 4)));
}

export default function GenomeDemo({ mode }: { mode: 'random' | 'grouped' }) {
  return (
    <div className="genome-demo" data-mode={mode} aria-hidden="true">
      {demoRows(mode).map((cells, gi) => {
        const test = cells.filter(Boolean).length, train = cells.length - test;
        return (
          <div className="genome-row" key={gi}>
            <span className="genome-label">genome {gi + 1}</span>
            {cells.map((isTest, ri) => <span key={ri} className={'genome-cell ' + (isTest ? 'test' : 'train')}></span>)}
            {train && test
              ? <span className="genome-tag leak">both sides</span>
              : <span className="genome-tag">{test ? 'test only' : 'train only'}</span>}
          </div>
        );
      })}
    </div>
  );
}
