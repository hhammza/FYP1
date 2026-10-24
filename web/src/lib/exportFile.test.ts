import { downloadExport, lightFigure } from './exportFile';
import type { PlotElement } from '../components/Plot';

vi.mock('plotly.js-dist-min', () => ({ default: {} }));

afterEach(() => vi.unstubAllGlobals());

describe('downloads', () => {
  it('posts the result to /api/export/ and saves the file under its name', async () => {
    const fetch = vi.fn(async () => new Response('a,b\n', {
      status: 200, headers: { 'Content-Disposition': 'attachment; filename="amr-forecast-20261014-1200.csv"' } }));
    vi.stubGlobal('fetch', fetch);
    URL.createObjectURL = vi.fn(() => 'blob:x');
    URL.revokeObjectURL = vi.fn();
    let saved = '';
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (this: HTMLAnchorElement) {
      saved = this.download;
    });
    await downloadExport('forecast', 'csv', { prediction: 'Resistant' }, { genus: 'Escherichia' });
    const [url, init] = fetch.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe('/api/export/forecast.csv');
    const body = init.body as FormData;
    expect(JSON.parse(String(body.get('result')))).toEqual({ prediction: 'Resistant' });
    expect(JSON.parse(String(body.get('inputs')))).toEqual({ genus: 'Escherichia' });
    expect(saved).toBe('amr-forecast-20261014-1200.csv');
  });

  it("shows the backend's reason when it refuses", async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({ error: 'Nothing to export: run a prediction first.' }), { status: 400 })));
    await expect(downloadExport('forecast', 'pdf', {}, {})).rejects.toThrow('Nothing to export');
  });

  it('draws the chart light for paper, whatever the page theme', () => {
    const gd = { data: [], layout: { paper_bgcolor: 'rgba(0,0,0,0)', xaxis: { gridcolor: '#333', tickfont: { size: 11 } },
                                     yaxis: { title: { text: 'Rows' } }, legend: {} } } as unknown as PlotElement;
    const { layout } = lightFigure(gd) as { layout: Record<string, Record<string, unknown>> };
    expect(layout.paper_bgcolor).toBe('#ffffff');
    expect(layout.xaxis.gridcolor).toBe('#e5e7eb');
    expect(layout.xaxis.tickfont).toEqual({ size: 11, color: '#475569' });
    expect((layout.yaxis.title as Record<string, unknown>).font).toEqual({ color: '#475569' });
    expect(gd.layout?.paper_bgcolor).toBe('rgba(0,0,0,0)');    // the page's chart is untouched
  });
});
