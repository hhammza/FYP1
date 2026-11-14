/* A living strip along the top of the footer: a DNA double strand flowing past,
   with bacteria swimming through and an antibiotic capsule drifting by.
   Decorative; motion in styles/header-scenes.css (.footer-scene). */
const PERIOD = 120;      // one helical turn, px
const HALF = 2400;       // the strand is drawn twice this wide and slides by HALF
const MID = 26, AMP = 10;

function strand(phase: number) {
  let d = '';
  for (let x = 0; x <= HALF * 2; x += 6) {
    const y = MID + AMP * Math.sin((2 * Math.PI * x) / PERIOD + phase);
    d += `${x ? 'L' : 'M'}${x} ${y.toFixed(1)}`;
  }
  return d;
}
const A = strand(0), B = strand(Math.PI);
const RUNGS = Array.from({ length: (HALF * 2) / 15 }, (_, i) => {
  const x = i * 15, s = Math.sin((2 * Math.PI * x) / PERIOD);
  return { x, y1: MID + AMP * s, y2: MID - AMP * s, k: i % 4 };
});

function Bug({ cls }: { cls: string }) {
  return (
    <svg className={`fs-bug ${cls}`} viewBox="-14 -7 34 14" aria-hidden="true">
      <path className="fs-flag" d="M10 0c3-3 5 3 8 0" />
      <rect x="-12" y="-5" width="22" height="10" rx="5" />
    </svg>
  );
}

export default function FooterScene() {
  return (
    <div className="footer-scene" aria-hidden="true">
      <svg className="fs-dna" width={HALF * 2} height="52" viewBox={`0 0 ${HALF * 2} 52`}>
        {RUNGS.map(r => <line key={r.x} className={`fs-rung k${r.k}`} x1={r.x} x2={r.x} y1={r.y1} y2={r.y2} />)}
        <path className="fs-strand a" d={A} />
        <path className="fs-strand b" d={B} />
      </svg>
      <Bug cls="b1" /><Bug cls="b2 r" /><Bug cls="b3" />
      <svg className="fs-capsule" viewBox="-12 -7 24 14" aria-hidden="true">
        <path className="fs-cap-a" d="M0-6H-6a6 6 0 0 0 0 12H0z" /><path className="fs-cap-b" d="M0-6H6a6 6 0 0 1 0 12H0z" />
      </svg>
    </div>
  );
}
