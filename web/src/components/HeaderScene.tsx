/* One animated scene per page, behind the page header, each showing what that
   page is about: a k-mer scan for genome prediction, an MIC dilution plate for
   the forecaster, a treatment curve for the timeline, a globe for the Explorer,
   plasmid transfer for resistance genes, the cleaning pipeline for the data,
   ROC curves for the model reports, boosted trees for training, the CLI for the
   library and a microscope for About. Decorative; motion lives in
   styles/header-scenes.css and stops for reduced motion. */
import type { CSSProperties, ReactElement } from 'react';

export type SceneKind = 'kmer' | 'mic' | 'growth' | 'world' | 'plasmid' | 'pipeline' | 'roc' | 'compare' | 'trees' | 'terminal' | 'microscope';

const v = (o: Record<string, string | number>) => o as CSSProperties;

/* ── genome prediction: a sequence passes through a k-mer window ── */
const SEQ = 'ATGCGTACCGATTGCAAGTCCGATGGCTAACGTTAGCCATGCAGTTCGAACTGGATCCTAGCAATG';
const PAIR: Record<string, string> = { A: 'T', T: 'A', G: 'C', C: 'G' };
const GENES = [{ from: 10, to: 21, label: 'gyrA' }, { from: 38, to: 53, label: 'blaCTX-M' }];
const STEP = 18;
function Kmer() {
  const len = SEQ.length * STEP;
  const copy = (off: number) => (
    <g key={off} transform={`translate(${off} 0)`}>
      {GENES.map(g => (
        <g key={g.label}>
          <rect className="sc-gene" x={g.from * STEP - 4} y="52" width={(g.to - g.from) * STEP} height="68" rx="6" />
          <text className="sc-gene-label" x={g.from * STEP} y="44">{g.label}</text>
        </g>))}
      {[...SEQ].map((b, i) => (
        <g key={i}>
          <text className={`sc-base b-${b}`} x={i * STEP} y="72">{b}</text>
          <line className="sc-tick" x1={i * STEP + 5} x2={i * STEP + 5} y1="78" y2="94" />
          <text className={`sc-base dim b-${PAIR[b]}`} x={i * STEP} y="112">{PAIR[b]}</text>
        </g>))}
    </g>);
  return (<>
    <defs><clipPath id="scSeq"><rect x="0" y="0" width="440" height="160" /></clipPath></defs>
    <g clipPath="url(#scSeq)"><g className="sc-scroll" style={v({ '--len': `${-len}px` })}>{copy(0)}{copy(len)}</g></g>
    <rect className="sc-window" x="301" y="50" width="76" height="74" rx="7" />
    <text className="sc-caption" x="339" y="142" textAnchor="middle">4-mer window</text>
    {[34, 58, 22, 70, 46, 30, 62, 40].map((h, i) => (
      <rect key={i} className="sc-count" x={470 + i * 15} y={128 - h} width="10" height={h} rx="2" style={v({ animationDelay: `${-i * 0.37}s` })} />))}
    <line className="sc-axis" x1="464" x2="590" y1="128" y2="128" />
    <text className="sc-caption" x="527" y="146" textAnchor="middle">k-mer counts</text>
  </>);
}

/* ── forecast: broth microdilution, growth below the MIC ── */
const CONC = ['64', '32', '16', '8', '4', '2', '1', '0.5'];
const MIC_AT = 3;
function Mic() {
  return (<>
    <text className="sc-caption" x="40" y="22">antibiotic, µg/mL</text>
    <path className="sc-arrow" d="M150 18h330" markerEnd="url(#scArr)" />
    <defs><marker id="scArr" viewBox="0 0 8 8" refX="6" refY="4" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0 8 4 0 8z" className="sc-arrowhead" /></marker></defs>
    {CONC.map((c, i) => {
      const x = 62 + i * 64;
      return (
        <g key={c} transform={`translate(${x} 80)`}>
          <circle className="sc-well" r="24" />
          <circle className="sc-drug" r="21" style={{ opacity: 0.62 - i * 0.075 }} />
          {i > MIC_AT && (
            <g className="sc-growth" style={v({ animationDelay: `${(7 - i) * 0.45}s` })}>
              <circle className="sc-turbid" r="20" />
              {[[-8, -6, 20], [6, -2, -30], [-3, 8, 60], [9, 9, 10]].map(([bx, by, r], k) => (
                <rect key={k} className="sc-bug" x={bx - 5} y={by - 2.5} width="10" height="5" rx="2.5" transform={`rotate(${r} ${bx} ${by})`} />))}
            </g>)}
          <text className="sc-caption" y="44" textAnchor="middle">{c}</text>
        </g>);
    })}
    <g className="sc-mic-pointer" style={v({ '--from': `${(7 - MIC_AT) * 64}px` })} transform={`translate(${62 + MIC_AT * 64} 0)`}>
      <g><path className="sc-pointer" d="M-7 44h14l-7 9z" /><text className="sc-pointer-label" y="40" textAnchor="middle">MIC</text></g>
    </g>
  </>);
}

/* ── timeline: weekly doses, susceptible cells fall, resistant cells take over ── */
function Growth() {
  return (<>
    <path className="sc-axis" d="M40 18V138H584" />
    <text className="sc-caption" x="46" y="16">population</text>
    <text className="sc-caption" x="584" y="154" textAnchor="end">weeks of treatment</text>
    {[0, 1, 2, 3, 4, 5, 6].map(i => (
      <g key={i} transform={`translate(${84 + i * 72} 150)`}>
        <g className="sc-dose" style={v({ animationDelay: `${i * 0.55}s` })}>
          <path className="sc-cap-a" d="M0-3.5H-4a3.5 3.5 0 0 0 0 7H0z" /><path className="sc-cap-b" d="M0-3.5H4a3.5 3.5 0 0 1 0 7H0z" />
        </g>
      </g>))}
    <path className="sc-curve s" pathLength={1} d="M40 36C150 36 190 112 290 126S520 132 584 132" />
    <path className="sc-curve r" pathLength={1} d="M40 134C200 134 270 60 380 44S540 36 584 36" />
    <text className="sc-curve-label s" x="590" y="132">susceptible</text>
    <text className="sc-curve-label r" x="590" y="38">resistant</text>
    <line className="sc-playhead" x1="40" x2="40" y1="20" y2="138" />
  </>);
}

/* ── explorer: a turning globe, hotspots, resistance bins ── */
const BINS = ['#fde6d8', '#f8b08a', '#ec7a45', '#c84a1c', '#8a2c0d'];
function World() {
  const spots: [number, number, number][] = [[-30, -22, 4], [12, -34, 2], [26, 6, 3], [-14, 20, 4], [40, -12, 1]];
  return (<>
    {[[64, 3], [48, 1], [80, 4], [36, 0], [56, 2]].map(([w, b], i) => (
      <g key={i} transform={`translate(150 ${34 + i * 22})`}>
        <rect className="sc-bar-track" width="150" height="10" rx="5" />
        <rect className="sc-bar" width={w * 1.5} height="10" rx="5" fill={BINS[b]} style={v({ animationDelay: `${i * 0.25}s` })} />
      </g>))}
    <text className="sc-caption" x="150" y="22">resistant % by country</text>
    <g transform="translate(470 82)">
      <circle className="sc-globe" r="62" />
      <ellipse className="sc-lat" rx="62" ry="20" /><ellipse className="sc-lat" rx="54" ry="8" cy="-34" /><ellipse className="sc-lat" rx="54" ry="8" cy="34" />
      {[0, 1, 2].map(i => <ellipse key={i} className="sc-meridian" rx="26" ry="62" style={v({ animationDelay: `${-i * 2}s` })} />)}
      <path className="sc-arc" d="M-30 -22Q-10 -60 12 -34" /><path className="sc-arc" d="M12 -34Q50 -20 26 6" /><path className="sc-arc" d="M26 6Q10 40 -14 20" />
      {spots.map(([x, y, b], i) => (
        <g key={i} transform={`translate(${x} ${y})`}>
          <circle className="sc-ripple" r="5" style={v({ '--c': BINS[b], animationDelay: `${i * 0.5}s` })} />
          <circle r="4" fill={BINS[b]} className="sc-spot" />
        </g>))}
    </g>
  </>);
}

/* ── resistance genes: a plasmid crosses a pilus to a new host ── */
function Plasmid() {
  const ring = (cls: string) => (
    <g className={cls}>
      <circle className="sc-plasmid" r="17" />
      <path className="sc-gene-arc a" d="M0-17A17 17 0 0 1 14.7-8.5" />
      <path className="sc-gene-arc b" d="M8.5 14.7A17 17 0 0 1-8.5 14.7" />
    </g>);
  return (<>
    <g transform="translate(150 48)"><rect className="sc-cell r" width="150" height="66" rx="33" /></g>
    <path className="sc-chromo" d="M180 70c8-10 16 10 24 0s16 10 24 0" />
    <g transform="translate(250 82)">{ring('sc-ring-spin')}</g>
    <path className="sc-pilus" d="M300 81H392" />
    <g transform="translate(392 48)"><rect className="sc-cell recipient" width="150" height="66" rx="33" /></g>
    <path className="sc-chromo" d="M420 70c8-10 16 10 24 0s16 10 24 0" />
    <g transform="translate(250 82)"><g className="sc-travel"><circle className="sc-plasmid small" r="9" /><path className="sc-gene-arc a" d="M0-9A9 9 0 0 1 7.8-4.5" /></g></g>
    <g transform="translate(492 82)">{ring('sc-ring-new')}</g>
    <text className="sc-caption" x="225" y="136" textAnchor="middle">resistant donor</text>
    <text className="sc-caption" x="467" y="136" textAnchor="middle">recipient</text>
    <text className="sc-caption" x="346" y="70" textAnchor="middle">plasmid</text>
  </>);
}

/* ── datasets: records pass a cleaning gate into the store ── */
function Pipeline() {
  const recs = [0, 1, 2, 3, 4, 5, 6, 7];
  const rejected = new Set([2, 5]);
  return (<>
    <text className="sc-caption" x="110" y="30">BV-BRC records</text>
    <text className="sc-num" x="110" y="50">17.6M</text>
    <path className="sc-gate" d="M330 36v28M330 98v28" />
    <path className="sc-gate-sieve" d="M330 64v34" />
    <text className="sc-caption" x="330" y="146" textAnchor="middle">clean, deduplicate</text>
    <g transform="translate(500 50)" className="sc-db">
      <path className="sc-db-body" d="M-34 0v60a34 10 0 0 0 68 0V0" /><ellipse className="sc-db-top" rx="34" ry="10" />
      <path className="sc-db-line" d="M-34 20a34 10 0 0 0 68 0M-34 40a34 10 0 0 0 68 0" />
    </g>
    <text className="sc-caption" x="500" y="134" textAnchor="middle">cleaned</text>
    <text className="sc-num" x="500" y="152" textAnchor="middle">7.8M</text>
    {recs.map(i => (
      <g key={i} transform={`translate(110 ${66 + (i % 3) * 14})`}>
        <g className={'sc-rec ' + (rejected.has(i) ? 'bad' : 'good')} style={v({ animationDelay: `${i * 0.6}s` })}>
          <rect width="30" height="10" rx="3" /><line x1="6" x2="22" y1="5" y2="5" />
        </g>
      </g>))}
  </>);
}

/* ── model report / comparison: ROC curve over chance, confusion matrix ── */
function Roc({ two }: { two?: boolean }) {
  return (<>
    {[[0, 0, 'tp'], [1, 0, 'fn'], [0, 1, 'fp'], [1, 1, 'tn']].map(([c, r, k], i) => (
      <g key={k as string} transform={`translate(${170 + (c as number) * 58} ${30 + (r as number) * 52})`}>
        <rect className={`sc-cm ${k}`} width="54" height="48" rx="6" style={v({ animationDelay: `${i * 0.5}s` })} />
        <text className="sc-cm-label" x="27" y="29" textAnchor="middle">{(k as string).toUpperCase()}</text>
      </g>))}
    <text className="sc-caption" x="228" y="146" textAnchor="middle">confusion matrix</text>
    <g transform="translate(360 18)">
      <rect className="sc-roc-box" width="190" height="120" />
      <path className="sc-chance" d="M0 120L190 0" />
      <path className="sc-roc-area" d="M0 120C6 40 40 10 190 0V120z" />
      <path className="sc-curve r roc" pathLength={1} d="M0 120C6 40 40 10 190 0" />
      {two && <path className="sc-curve s roc late" pathLength={1} d="M0 120C20 70 70 30 190 0" />}
      <text className="sc-caption" x="95" y="136" textAnchor="middle">{two ? 'ROC: deployed vs experimental' : 'ROC on unseen genomes'}</text>
    </g>
  </>);
}

/* ── train: gradient boosting adds one small tree at a time ── */
function Trees() {
  const tree = (i: number) => (
    <g key={i} transform={`translate(${130 + i * 104} 0)`} className="sc-tree" style={v({ '--t': `${i * 0.8}s` })}>
      <path className="sc-edge" pathLength={1} d="M0 36L-22 74M0 36L22 74M-22 74L-34 112M-22 74L-10 112M22 74L10 112M22 74L34 112" />
      <circle className="sc-node" cy="36" r="8" />
      <circle className="sc-node" cx="-22" cy="74" r="7" /><circle className="sc-node" cx="22" cy="74" r="7" />
      {[-34, -10, 10, 34].map((x, k) => <circle key={x} className={'sc-leaf ' + ((i + k) % 3 ? 's' : 'r')} cx={x} cy="112" r="6" />)}
      <text className="sc-caption" y="140" textAnchor="middle">tree {i + 1}</text>
    </g>);
  return (<>
    {[0, 1, 2, 3].map(tree)}
    {[0, 1, 2].map(i => <text key={i} className="sc-plus" x={182 + i * 104} y="80" textAnchor="middle">+</text>)}
    <text className="sc-plus" x="490" y="80" textAnchor="middle">=</text>
    <g transform="translate(512 62)"><rect className="sc-bar-track" width="70" height="12" rx="6" /><rect className="sc-prob" width="70" height="12" rx="6" /></g>
    <text className="sc-caption" x="547" y="96" textAnchor="middle">P(resistant)</text>
  </>);
}

/* ── library: the amrpredict command line ── */
const CMDS = ['amrpredict forecast ciprofloxacin --taxon-id 562 --mic-value 4', 'amrpredict predict genome.fasta ampicillin', 'amrpredict antibiotics --compact | jq'];
function Terminal() {
  return (<>
    <rect className="sc-term" x="150" y="14" width="434" height="132" rx="9" />
    <path className="sc-term-bar" d="M150 23a9 9 0 0 1 9-9h416a9 9 0 0 1 9 9v11H150z" />
    {[0, 1, 2].map(i => <circle key={i} cx={166 + i * 13} cy="24" r="4" className={`sc-dot d${i}`} />)}
    {CMDS.map((c, i) => (
      <g key={c}>
        <defs><clipPath id={`scLine${i}`}><rect className="sc-type" x="162" y={52 + i * 30} width="410" height="20" style={v({ '--n': c.length + 2, animationDelay: `${i * 2.2}s` })} /></clipPath></defs>
        <text className="sc-cmd" x="164" y={66 + i * 30} clipPath={`url(#scLine${i})`}><tspan className="sc-prompt">$ </tspan>{c}</text>
      </g>))}
    <rect className="sc-cursor" x="164" y="128" width="7" height="12" />
  </>);
}

/* ── about: bacteria under a microscope, drifting in and out of focus ── */
function Microscope() {
  const bugs: [number, number, number][] = [[-30, -20, 20], [18, -28, -40], [30, 14, 70], [-20, 22, -10], [0, 0, 45], [-42, 4, 90]];
  return (<>
    <defs><clipPath id="scEye"><circle cx="430" cy="80" r="64" /></clipPath></defs>
    <circle className="sc-knob" cx="430" cy="80" r="74" />
    <circle className="sc-eye" cx="430" cy="80" r="64" />
    <g clipPath="url(#scEye)">
      <g className="sc-focus">
        {bugs.map(([x, y, r], i) => (
          <g key={i} transform={`translate(${430 + x} ${80 + y}) rotate(${r})`}>
            <g className="sc-swim" style={v({ animationDelay: `${-i * 0.7}s` })}>
              <rect className={'sc-micro ' + (i % 3 ? 's' : 'r')} x="-10" y="-4.5" width="20" height="9" rx="4.5" />
              <path className="sc-micro-flag" d="M10 0c3-3 5 3 8 0" />
            </g>
          </g>))}
      </g>
      <path className="sc-cross" d="M430 16V144M366 80H494" />
    </g>
    <path className="sc-scale" d="M454 124h28" /><text className="sc-caption" x="468" y="120" textAnchor="middle">10 µm</text>
    <text className="sc-caption" x="300" y="80" textAnchor="end">×1000</text>
  </>);
}

const SCENES: Record<SceneKind, () => ReactElement> = {
  kmer: Kmer, mic: Mic, growth: Growth, world: World, plasmid: Plasmid, pipeline: Pipeline,
  roc: () => <Roc />, compare: () => <Roc two />, trees: Trees, terminal: Terminal, microscope: Microscope,
};

export default function HeaderScene({ kind }: { kind: SceneKind }) {
  const Scene = SCENES[kind];
  return (
    <div className={`header-scene scene-${kind}`} aria-hidden="true">
      <svg viewBox="0 0 600 160" preserveAspectRatio="xMaxYMid meet"><Scene /></svg>
    </div>
  );
}
