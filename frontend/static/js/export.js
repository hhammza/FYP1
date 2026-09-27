/* ============================================================
   AMRPredict — Download bar (templates/_export_bar.html)
   "Chart (PNG)" saves the page's chart; "PDF report" adds the same
   PNG to the form and posts it to /export/<page>.pdf. CSV needs no
   script: its button posts straight to /export/<page>.csv.
   Downloads always use a light chart, whatever the page theme.
   Expects: window.Plotly, window.AMR (from main.js)
   ============================================================ */
(function () {
  'use strict';

  const INK = '#1f2937', MUTED = '#475569', GRID = '#e5e7eb';

  /* A copy of the chart's figure restyled for white paper */
  function lightFigure(gd) {
    const layout = JSON.parse(JSON.stringify(gd.layout || {}));
    layout.paper_bgcolor = '#ffffff';
    layout.plot_bgcolor = '#ffffff';
    layout.font = Object.assign({}, layout.font, { color: INK });
    Object.keys(layout).filter(k => /^[xy]axis\d*$/.test(k)).forEach(k => {
      const ax = layout[k];
      ax.gridcolor = GRID;
      ax.linecolor = GRID;
      ax.tickfont = Object.assign({}, ax.tickfont, { color: MUTED });
      if (ax.title && typeof ax.title === 'object') {
        ax.title.font = Object.assign({}, ax.title.font, { color: MUTED });
      }
    });
    if (layout.legend) layout.legend.font = Object.assign({}, layout.legend.font, { color: INK });
    return { data: gd.data, layout: layout };
  }

  function chartImage(id) {
    const gd = id && document.getElementById(id);
    if (!gd || !gd.data || !window.Plotly) return Promise.resolve('');
    return Plotly.toImage(lightFigure(gd), { format: 'png', width: 1000, height: 520 })
      .catch(() => '');
  }

  document.querySelectorAll('form[data-export-page]').forEach(form => {
    const page = form.dataset.exportPage;
    const chartId = form.dataset.chartId;
    const chartField = form.querySelector('input[name="chart"]');

    form.querySelectorAll('[data-export]').forEach(btn => {
      btn.addEventListener('click', () => {
        btn.disabled = true;
        chartImage(chartId).then(url => {
          if (btn.dataset.export === 'png') {
            if (!url) { AMR.toast('There is no chart to download.', 'error'); return; }
            const a = document.createElement('a');
            a.href = url;
            a.download = `amr-${page}-chart.png`;
            document.body.appendChild(a);
            a.click();
            a.remove();
          } else {
            chartField.value = url;          // empty: the PDF simply has no chart
            form.action = `/export/${page}.pdf`;
            form.submit();
            chartField.value = '';
          }
        }).finally(() => { btn.disabled = false; });
      });
    });
  });
})();
