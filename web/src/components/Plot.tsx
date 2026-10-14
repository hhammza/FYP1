/* A Plotly chart. Plotly is large, so it loads with the first chart, not with
   the site; the chart redraws when its figure or the theme changes. */
import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react';
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
  /** the chart for the current theme's colours; keep it stable (useCallback) */
  figure: (t: PlotTheme) => Figure;
  config?: Partial<Config>;
}

const Plot = forwardRef<PlotElement | null, Props>(function Plot({ id, className, figure, config }, ref) {
  const el = useRef<PlotElement>(null);
  const dark = useDarkTheme();
  useImperativeHandle(ref, () => el.current as PlotElement, []);

  useEffect(() => {
    let alive = true;
    loadPlotly().then(P => {
      if (!alive || !el.current) return;
      const { data, layout } = figure(plotTheme());
      P.react(el.current, data, layout, { responsive: true, displayModeBar: false, ...config });
    }).catch(() => {});
    return () => { alive = false; };
  }, [figure, config, dark]);

  useEffect(() => () => {
    const node = el.current;
    if (node) loadPlotly().then(P => P.purge(node)).catch(() => {});
  }, []);

  return <div id={id} className={className} ref={el}></div>;
});

export default Plot;
