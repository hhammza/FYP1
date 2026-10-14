/* Downloads of a tool page's result (export.js in the Flask frontend). The
   result goes to POST /api/export/<page>.<fmt> (backend/api/exports.py); a PDF
   carries a PNG of the page's chart, drawn light whatever the page theme. */
import { ApiError, apiUrl, DEFAULT_TIMEOUT_S } from './api';
import { loadPlotly, type PlotElement } from '../components/Plot';

export type ExportPage = 'forecast' | 'predict' | 'timeline' | 'batch';

const INK = '#1f2937', MUTED = '#475569', GRID = '#e5e7eb';

type Obj = Record<string, unknown>;

/** A copy of the chart's figure restyled for white paper. */
export function lightFigure(gd: PlotElement) {
  const layout = JSON.parse(JSON.stringify(gd.layout || {})) as Obj;
  layout.paper_bgcolor = '#ffffff';
  layout.plot_bgcolor = '#ffffff';
  layout.font = { ...(layout.font as Obj), color: INK };
  Object.keys(layout).filter(k => /^[xy]axis\d*$/.test(k)).forEach(k => {
    const ax = layout[k] as Obj;
    ax.gridcolor = GRID;
    ax.linecolor = GRID;
    ax.tickfont = { ...(ax.tickfont as Obj), color: MUTED };
    if (ax.title && typeof ax.title === 'object') {
      const title = ax.title as Obj;
      title.font = { ...(title.font as Obj), color: MUTED };
    }
  });
  if (layout.legend) (layout.legend as Obj).font = { ...((layout.legend as Obj).font as Obj), color: INK };
  return { data: gd.data || [], layout };
}

/** The chart as a PNG data URL, or '' when there is none. */
export async function chartImage(gd: PlotElement | null | undefined): Promise<string> {
  if (!gd || !gd.data) return '';
  try {
    const P = await loadPlotly();
    const fig = lightFigure(gd);
    return await P.toImage(fig as Parameters<typeof P.toImage>[0], { format: 'png', width: 1000, height: 520 });
  } catch {
    return '';
  }
}

/** Saves `href` (a data or blob URL) as a file. */
export function saveAs(href: string, name: string) {
  const a = document.createElement('a');
  a.href = href;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
}

/** Asks the backend for the CSV or PDF of `result` and saves it. */
export async function downloadExport(page: ExportPage, fmt: 'csv' | 'pdf', result: unknown,
                                     inputs: unknown, chart = ''): Promise<void> {
  const form = new FormData();
  form.append('result', JSON.stringify(result));
  form.append('inputs', JSON.stringify(inputs || {}));
  form.append('chart', chart);
  let r: Response;
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), DEFAULT_TIMEOUT_S * 1000);
  try {
    r = await fetch(apiUrl(`export/${page}.${fmt}`), { method: 'POST', body: form, signal: ctrl.signal });
  } catch {
    throw new ApiError('The download could not be made: the backend is not reachable.', 503);
  } finally {
    clearTimeout(timer);
  }
  if (!r.ok) {
    let message = `The download failed (HTTP ${r.status}).`;
    try { message = ((await r.json()) as { error?: string }).error || message; } catch { /* not JSON */ }
    throw new ApiError(message, r.status);
  }
  const name = /filename="([^"]+)"/.exec(r.headers.get('Content-Disposition') || '')?.[1] || `amr-${page}.${fmt}`;
  const url = URL.createObjectURL(await r.blob());
  saveAs(url, name);
  setTimeout(() => URL.revokeObjectURL(url), 10_000);
}
