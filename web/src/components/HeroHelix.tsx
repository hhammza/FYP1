/* The home page's DNA double helix, drawn in 3D: two backbones twisting round
   each other, base pairs coloured by letter (A-T, G-C), the far side dimmer than
   the near side. Every few seconds one base pair mutates: it flashes red and a
   known resistance mutation floats out beside it, the kind of change the genome
   model reads. Positions are computed per frame and written straight to the SVG
   (no React re-render); for reduced motion it draws one still frame. */
import { useEffect, useRef } from 'react';

const N = 30;                 // base pairs
const W = 220, H = 640;       // viewBox
const CX = W / 2, R = 46;     // axis and radius
const TWIST = 0.42;           // radians between pairs
const TOP = 26, GAP = (H - 2 * TOP) / (N - 1);
const SEQ = 'ATGCGTACCGATTGCAAGTCCGATGGCTAA';
const PAIR: Record<string, string> = { A: 'T', T: 'A', G: 'C', C: 'G' };
const MUTATIONS = ['gyrA S83L', 'parC S80I', 'blaTEM-1', 'rpoB S531L', 'mecA', 'blaCTX-M-15', 'katG S315T', 'tet(M)'];

export default function HeroHelix() {
  const svg = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const el = svg.current;
    if (!el) return;
    const q = <T extends Element>(s: string) => Array.from(el.querySelectorAll<T>(s));
    const segA = q<SVGLineElement>('.hh-seg.a'), segB = q<SVGLineElement>('.hh-seg.b');
    const rungA = q<SVGLineElement>('.hh-rung.a'), rungB = q<SVGLineElement>('.hh-rung.b');
    const nucA = q<SVGCircleElement>('.hh-nuc.a'), nucB = q<SVGCircleElement>('.hh-nuc.b');
    const pairs = q<SVGGElement>('.hh-pair');
    const tag = el.querySelector<SVGGElement>('.hh-tag')!, tagText = el.querySelector<SVGTextElement>('.hh-tag text')!;
    const tagBox = el.querySelector<SVGRectElement>('.hh-tag rect')!;

    let mut = -1, mutAt = -10, mutName = 0;
    const draw = (t: number) => {
      const s = t / 1000;
      const pts = Array.from({ length: N }, (_, i) => {
        const th = i * TWIST + s * 0.9;
        return { y: TOP + i * GAP, xa: CX + R * Math.sin(th), za: Math.cos(th), xb: CX - R * Math.sin(th), zb: -Math.cos(th) };
      });
      const depth = (z: number) => 0.25 + 0.75 * ((z + 1) / 2);   // 0.25 far .. 1 near
      for (let i = 0; i < N; i++) {
        const p = pts[i];
        if (i < N - 1) {
          const n = pts[i + 1];
          for (const [seg, x1, x2, z] of [[segA[i], p.xa, n.xa, (p.za + n.za) / 2], [segB[i], p.xb, n.xb, (p.zb + n.zb) / 2]] as const) {
            seg.setAttribute('x1', x1.toFixed(1)); seg.setAttribute('x2', x2.toFixed(1));
            seg.style.opacity = depth(z).toFixed(2); seg.style.strokeWidth = (2 + 3 * depth(z)).toFixed(1);
          }
        }
        const mid = (p.xa + p.xb) / 2;
        rungA[i].setAttribute('x1', p.xa.toFixed(1)); rungA[i].setAttribute('x2', mid.toFixed(1));
        rungB[i].setAttribute('x1', mid.toFixed(1)); rungB[i].setAttribute('x2', p.xb.toFixed(1));
        const rz = depth(0) * 0.8 + 0.2 * Math.abs(Math.sin(i * TWIST + s * 0.9));
        rungA[i].style.opacity = rungB[i].style.opacity = rz.toFixed(2);
        nucA[i].setAttribute('cx', p.xa.toFixed(1)); nucA[i].setAttribute('r', (2.5 + 3.5 * depth(p.za)).toFixed(1));
        nucA[i].style.opacity = depth(p.za).toFixed(2);
        nucB[i].setAttribute('cx', p.xb.toFixed(1)); nucB[i].setAttribute('r', (2.5 + 3.5 * depth(p.zb)).toFixed(1));
        nucB[i].style.opacity = depth(p.zb).toFixed(2);
      }
      // a mutation every 4.5 s, shown for 2.6 s
      if (s - mutAt > 4.5) {
        if (mut >= 0) pairs[mut].classList.remove('mutating');
        mut = 4 + Math.floor(Math.random() * (N - 8)); mutAt = s; mutName = (mutName + 1) % MUTATIONS.length;
        pairs[mut].classList.add('mutating');
        tagText.textContent = MUTATIONS[mutName];
        tagBox.setAttribute('width', String(tagText.textContent.length * 6.6 + 16));
      }
      const age = s - mutAt, p = pts[mut];
      const on = age < 2.6;
      if (!on) pairs[mut].classList.remove('mutating');
      tag.style.opacity = on ? String(Math.min(1, age * 3, (2.6 - age) * 3)) : '0';
      // centred just above the mutated pair, inside the helix's own column
      const w = Number(tagBox.getAttribute('width'));
      tag.setAttribute('transform', `translate(${((p.xa + p.xb) / 2 - w / 2).toFixed(1)} ${(p.y - 20 - age * 6).toFixed(1)})`);
    };

    const calm = typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (calm || typeof requestAnimationFrame !== 'function') { draw(0); tag.style.opacity = '0'; return; }
    let raf = 0;
    const loop = (t: number) => { draw(t); raf = requestAnimationFrame(loop); };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <div className="hero-helix" aria-hidden="true">
      <svg ref={svg} viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid meet">
        <defs>
          <filter id="hhGlow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.4" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
        </defs>
        {Array.from({ length: N }, (_, i) => {
          const y = TOP + i * GAP, b = SEQ[i % SEQ.length];
          return (
            <g key={i} className="hh-pair">
              <line className={`hh-rung a n-${b}`} y1={y} y2={y} />
              <line className={`hh-rung b n-${PAIR[b]}`} y1={y} y2={y} />
            </g>);
        })}
        {Array.from({ length: N - 1 }, (_, i) => (
          <g key={i}>
            <line className="hh-seg a" y1={TOP + i * GAP} y2={TOP + (i + 1) * GAP} />
            <line className="hh-seg b" y1={TOP + i * GAP} y2={TOP + (i + 1) * GAP} />
          </g>))}
        {Array.from({ length: N }, (_, i) => (
          <g key={i}>
            <circle className="hh-nuc a" cy={TOP + i * GAP} r="4" filter="url(#hhGlow)" />
            <circle className="hh-nuc b" cy={TOP + i * GAP} r="4" filter="url(#hhGlow)" />
          </g>))}
        <g className="hh-tag" style={{ opacity: 0 }}>
          <rect x="0" y="-11" height="20" rx="10" width="80" />
          <text x="8" y="3">mutation</text>
        </g>
      </svg>
    </div>
  );
}
