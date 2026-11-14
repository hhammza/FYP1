/* A Plotly chart. Plotly is large, so it loads with the first chart, not with
   the site; the chart redraws when its figure or the theme changes. */
import { forwardRef, useEffect, useImperativeHandle, useRef, useState, type CSSProperties } from 'react';
import type { Config, Data, Layout } from 'plotly.js-dist-min';
import { plotTheme, useDarkTheme } from '../lib/theme';

export type PlotTheme = ReturnType<typeof plotTheme>;
export interface Figure { data: Data[]; layout: Partial<Layout> }

/** The chart's element once drawn; Plotly keeps the figure on it (for downloads). */
export type PlotElement = HTMLDivElement & { data?: Data[]; layout?: Partial<Layout> };

let plotly: Promise<typeof import('plotly.js-dist-min')> | undefined;
export const loadPlotly = () => (plotly ??= import('plotly.js-dist-min').then(m => m.default ?? m));

interface Props {
  id?: string;
  className?: string;
  style?: CSSProperties;
  /** the chart for the current theme's colours; keep it stable (useCallback) */
  figure: (t: PlotTheme) => Figure;
  config?: Partial<Config>;
  /** called with the clicked point's customdata (the dashboard's map sets a filter) */
  onPointClick?: (customdata: unknown) => void;
}

const Plot = forwardRef<PlotElement | null, Props>(function Plot({ id, className, style, figure, config, onPointClick }, ref) {
  const el = useRef<PlotElement>(null);
  const dark = useDarkTheme();
  // drawn again once the web fonts load: Plotly sizes legends with the font it has
  const [fonts, setFonts] = useState(false);
  useEffect(() => { document.fonts?.ready.then(() => setFonts(true)).catch(() => {}); }, []);
  useImperativeHandle(ref, () => el.current as PlotElement, []);

  useEffect(() => {
    let alive = true;
    loadPlotly().then(P => {
      if (!alive || !el.current) return;
      const { data, layout } = figure(plotTheme());
      P.react(el.current, data, layout, { responsive: true, displayModeBar: false, ...config });
      const node = el.current as PlotElement & { removeAllListeners?: (e: string) => void; on?: (e: string, f: (ev: { points: { customdata?: unknown }[] }) => void) => void };
      if (onPointClick && node.on) {
        node.removeAllListeners?.('plotly_click');
        node.on('plotly_click', ev => onPointClick(ev.points[0]?.customdata));
      }
    }).catch(() => {});
    return () => { alive = false; };
  }, [figure, config, dark, fonts, onPointClick]);

  useEffect(() => () => {
    const node = el.current;
    if (node) loadPlotly().then(P => P.purge(node)).catch(() => {});
  }, []);

  return <div id={id} className={className} style={style} ref={el}></div>;
});

export default Plot;
