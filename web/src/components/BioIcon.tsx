/* Animated microbiology icons, drawn as inline SVG so each part can move
   (a helix twisting, flagella waving, colonies growing). Takes the same
   Bootstrap icon name the page used before; a name without a drawing here
   falls back to the plain Bootstrap icon. Motion lives in styles/bio-icons.css:
   `live` icons loop gently, the others move while their link is hovered. */
import type { ReactElement } from 'react';

const S = { fill: 'none', stroke: 'currentColor', strokeWidth: 1.7, strokeLinecap: 'round', strokeLinejoin: 'round' } as const;

const DRAWINGS: Record<string, { name: string; svg: ReactElement }> = {
  'bi-dna': { name: 'dna', svg: <>
    <path {...S} d="M7 2c0 5 10 5 10 10s-10 5-10 10" />
    <path {...S} d="M17 2c0 5-10 5-10 10s10 5 10 10" />
    {[4.6, 7.4, 16.6, 19.4].map((y, i) => <line key={y} {...S} className={`rung r${i}`} x1="8.6" x2="15.4" y1={y} y2={y} strokeOpacity={0.75} />)}
  </> },
  'bi-bacteria': { name: 'bacterium', svg: <>
    <g className="flagella">
      <path {...S} strokeWidth={1.3} d="M16.5 12c1.6-1.8 2.6 1.8 4.2 0s1.4 1.2 2.3.6" />
      <path {...S} strokeWidth={1.1} strokeOpacity={0.7} d="M16 9.6c1.4-2.2 2.4.6 3.8-1.3" />
      <path {...S} strokeWidth={1.1} strokeOpacity={0.7} d="M16 14.4c1.4 2.2 2.4-.6 3.8 1.3" />
    </g>
    <g className="body"><rect {...S} x="2" y="7.5" width="15" height="9" rx="4.5" />
      <ellipse cx="8" cy="12" rx="2.6" ry="1.5" fill="currentColor" fillOpacity={0.45} /></g>
  </> },
  'bi-virus2': { name: 'virus', svg: <>
    <g className="spikes">{[0, 45, 90, 135, 180, 225, 270, 315].map(a => (
      <g key={a} transform={`rotate(${a} 12 12)`}><line {...S} x1="12" y1="5.6" x2="12" y2="2.8" /><circle cx="12" cy="2.3" r="1.2" fill="currentColor" /></g>))}</g>
    <circle {...S} className="core" cx="12" cy="12" r="5.6" />
    <circle className="core" cx="10.4" cy="11" r="1.1" fill="currentColor" /><circle className="core" cx="13.6" cy="13.4" r="0.9" fill="currentColor" />
  </> },
  'bi-globe2': { name: 'globe', svg: <>
    <circle {...S} cx="12" cy="12" r="9.5" />
    <path {...S} strokeOpacity={0.6} d="M2.8 9h18.4M2.8 15h18.4" />
    <ellipse {...S} className="meridian m0" cx="12" cy="12" rx="4.2" ry="9.5" />
    <ellipse {...S} className="meridian m1" cx="12" cy="12" rx="4.2" ry="9.5" strokeOpacity={0.55} />
  </> },
  'bi-palette': { name: 'petri', svg: <>
    <circle {...S} cx="12" cy="12" r="9.8" /><circle {...S} cx="12" cy="12" r="8" strokeOpacity={0.4} />
    {[[8.5, 9, 2.2], [14.8, 8.4, 1.6], [13.6, 14.6, 2.6], [8.2, 15, 1.3]].map(([x, y, r], i) => (
      <circle key={i} className={`colony c${i}`} cx={x} cy={y} r={r} fill="currentColor" fillOpacity={0.35 + i * 0.15} />))}
  </> },
  'bi-map': { name: 'map', svg: <>
    <path {...S} d="M2.5 6.5 8.5 4l7 2.5 6-2.5v13.5l-6 2.5-7-2.5-6 2.5z" />
    <path {...S} strokeOpacity={0.5} d="M8.5 4v13.5M15.5 6.5V20" />
    <g className="pin"><path fillRule="evenodd" fill="currentColor"
      d="M12 6.2a3 3 0 0 1 3 3c0 2.2-3 5.2-3 5.2s-3-3-3-5.2a3 3 0 0 1 3-3zM13.1 9.2a1.1 1.1 0 1 0-2.2 0a1.1 1.1 0 1 0 2.2 0z" /></g>
  </> },
  'bi-bar-chart': { name: 'bars', svg: <>
    <path {...S} d="M3 21h18" />
    {[[4.5, 9], [10, 4], [15.5, 12]].map(([x, y], i) => <rect key={i} className={`bar b${i}`} x={x} y={y} width="4" height={20 - y} rx="1" fill="currentColor" fillOpacity={0.55 + i * 0.15} />)}
  </> },
  'bi-capsule': { name: 'capsule', svg: <g transform="rotate(-40 12 12)">
    <path {...S} className="half h0" d="M12 7.5H7.5a4.5 4.5 0 0 0 0 9H12z" fill="currentColor" fillOpacity={0.4} />
    <path {...S} className="half h1" d="M12 7.5h4.5a4.5 4.5 0 0 1 0 9H12z" />
    {[0, 1, 2].map(i => <circle key={i} className={`grain g${i}`} cx={12} cy={12} r="0.9" fill="currentColor" />)}
  </g> },
  'bi-hexagon': { name: 'molecule', svg: <g className="ring">
    <path {...S} d="M12 3.5 19.4 7.75v8.5L12 20.5l-7.4-4.25v-8.5z" />
    <circle {...S} className="pi" cx="12" cy="12" r="4" strokeOpacity={0.6} />
    {[[12, 3.5], [19.4, 7.75], [19.4, 16.25], [12, 20.5], [4.6, 16.25], [4.6, 7.75]].map(([x, y], i) => (
      <circle key={i} className={`atom a${i}`} cx={x} cy={y} r="1.6" fill="currentColor" />))}
  </g> },
  'bi-graph-up-arrow': { name: 'growth', svg: <>
    <path {...S} strokeOpacity={0.55} d="M3 3v18h18" />
    <path {...S} className="curve" pathLength={1} d="M5 18c4 0 5-.5 7-5s3-7 8-7.5" />
    <circle className="tip" cx="20" cy="5.5" r="1.6" fill="currentColor" />
  </> },
  'bi-activity': { name: 'pulse', svg: <>
    <path {...S} className="curve" pathLength={1} d="M2 12h4l2.5-6 4 12 3-9 1.8 3H22" />
  </> },
  'bi-database': { name: 'database', svg: <>
    {[0, 1, 2].map(i => <g key={i} className={`disc d${i}`}><ellipse {...S} cx="12" cy={5 + i * 6.5} rx="8" ry="2.6" />
      {i < 2 && <path {...S} strokeOpacity={0.6} d={`M4 ${5 + i * 6.5}v6.5M20 ${5 + i * 6.5}v6.5`} />}</g>)}
  </> },
  'bi-clipboard-data': { name: 'report', svg: <>
    <rect {...S} x="4.5" y="4" width="15" height="17.5" rx="2" /><rect {...S} x="8.5" y="2.5" width="7" height="3" rx="1" />
    {[[8, 13], [11.2, 10], [14.4, 15]].map(([x, y], i) => <rect key={i} className={`bar b${i}`} x={x} y={y} width="2.2" height={18.5 - y} rx=".6" fill="currentColor" />)}
  </> },
  'bi-cpu': { name: 'network', svg: <>
    {[[4, 7, 12, 5], [4, 7, 12, 12], [4, 17, 12, 12], [4, 17, 12, 19], [12, 5, 20, 12], [12, 12, 20, 12], [12, 19, 20, 12]].map(([a, b, c, d], i) => (
      <line key={i} {...S} strokeWidth={1.1} strokeOpacity={0.5} x1={a} y1={b} x2={c} y2={d} />))}
    {[[4, 7, 0], [4, 17, 0], [12, 5, 1], [12, 12, 1], [12, 19, 1], [20, 12, 2]].map(([x, y, l], i) => (
      <circle key={i} className={`node l${l}`} cx={x} cy={y} r="2.1" fill="currentColor" />))}
  </> },
  'bi-box-seam': { name: 'package', svg: <>
    <path {...S} d="M4 9.5v9l8 4 8-4v-9" /><path {...S} strokeOpacity={0.55} d="M12 13.5v9" />
    <g className="lid"><path {...S} d="M3 7.5 12 3l9 4.5-9 4.5z" fill="currentColor" fillOpacity={0.25} /></g>
  </> },
  'bi-info-circle': { name: 'microscope', svg: <>
    <path {...S} d="M5 21h14M9 18h6M12 18v3" /><path {...S} d="M8.5 14a6 6 0 0 0 9.5-5" />
    <rect {...S} x="9.5" y="2.5" width="4" height="8" rx="1" transform="rotate(-25 11.5 6.5)" />
    <circle className="beam" cx="9" cy="14.5" r="1.6" fill="currentColor" />
  </> },
};

/* other Bootstrap names that mean the same thing share a drawing */
const ALIASES: Record<string, string> = {
  'bi-capsule-pill': 'bi-capsule', 'bi-graph-up': 'bi-graph-up-arrow',
  'bi-bar-chart-line': 'bi-bar-chart', 'bi-bar-chart-steps': 'bi-bar-chart', 'bi-globe': 'bi-globe2',
  'bi-virus': 'bi-virus2',
};

export const hasDrawing = (icon: string) => Boolean(DRAWINGS[ALIASES[icon] || icon]);

export default function BioIcon({ icon, live = false, className = '' }: { icon: string; live?: boolean; className?: string }) {
  const d = DRAWINGS[ALIASES[icon] || icon];
  if (!d) return <i className={`bi ${icon} ${className}`.trim()}></i>;
  return (
    <svg className={`bio-icon bio-${d.name}${live ? ' live' : ''} ${className}`.trim()} viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      {d.svg}
    </svg>
  );
}
