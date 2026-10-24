/* "Download this result" (templates/_export_bar.html): CSV, PDF report and,
   when the page has a chart, the chart as a PNG. */
import { useState, type RefObject } from 'react';
import { chartImage, downloadExport, saveAs, type ExportPage } from '../lib/exportFile';
import { errorText } from '../lib/api';
import { useToast } from './Toasts';
import type { PlotElement } from './Plot';

interface Props {
  page: ExportPage;
  result: unknown;
  inputs?: unknown;
  /** the page's chart; leave out when it has none */
  chart?: RefObject<PlotElement | null>;
}

type Kind = 'csv' | 'pdf' | 'png';

export default function ExportBar({ page, result, inputs, chart }: Props) {
  const [busy, setBusy] = useState<Kind | null>(null);
  const toast = useToast();

  async function run(kind: Kind) {
    setBusy(kind);
    try {
      if (kind === 'csv') {
        await downloadExport(page, 'csv', result, inputs);
        return;
      }
      const png = await chartImage(chart?.current);
      if (kind === 'png') {
        if (!png) toast('There is no chart to download.', 'error');
        else saveAs(png, `amr-${page}-chart.png`);
        return;
      }
      await downloadExport(page, 'pdf', result, inputs, png);   // no chart: the PDF simply has none
    } catch (e) {
      toast(errorText(e), 'error', 'Download failed');
    } finally {
      setBusy(null);
    }
  }

  const button = (kind: Kind, icon: string, label: string) => (
    <button type="button" className="btn btn-outline-custom btn-sm" disabled={busy !== null} onClick={() => run(kind)}>
      {busy === kind
        ? <span className="spinner-border spinner-border-sm me-1" role="status"></span>
        : <i className={`bi bi-${icon} me-1`}></i>}
      {label}
    </button>
  );

  return (
    <div className="info-card export-bar mb-4">
      <div className="d-flex flex-wrap align-items-center gap-2">
        <h6 className="card-section-title mb-0 me-auto"><i className="bi bi-download me-2 text-accent"></i>Download this result</h6>
        {button('csv', 'filetype-csv', 'CSV')}
        {page !== 'batch' && button('pdf', 'filetype-pdf', 'PDF report')}
        {chart && button('png', 'image', 'Chart (PNG)')}
      </div>
      <div className="text-muted fs-11 mt-2">
        {page === 'timeline' && 'Every download is labelled "Simulation, not a trained model". '}
        Research tool, not a clinical diagnostic.
      </div>
    </div>
  );
}
