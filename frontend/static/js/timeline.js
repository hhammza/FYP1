/* ============================================================
   AMRPredict — Timeline Page (mutation_timeline.html)
   Weeks slider, tab switching, drag-drop, sample genome,
   toggle table, and timeline Plotly chart.
   Chart data from <script type="application/json" id="timeline-chart-data">.
   Expects: window.AMR (from main.js), Plotly (CDN)
   ============================================================ */

(function () {
  'use strict';

  /* ── Weeks slider ─────────────────────────────────────────── */
  const slider   = document.getElementById('weeksSlider');
  const weeksVal = document.getElementById('weeksVal');
  if (slider && weeksVal) {
    slider.addEventListener('input', function () {
      weeksVal.textContent = this.value;
      this.setAttribute('aria-valuenow', this.value);
    });
  }

  /* ── File name display ────────────────────────────────────── */
  const fastaFile2 = document.getElementById('fastaFile2');
  const fileName2  = document.getElementById('fileName2');
  if (fastaFile2 && fileName2) {
    fastaFile2.addEventListener('change', function () {
      fileName2.textContent = this.files[0] ? this.files[0].name : '';
    });
  }

  /* ── Drag-and-drop ────────────────────────────────────────── */
  const dropZone2 = document.getElementById('dropZone2');
  if (dropZone2) {
    dropZone2.addEventListener('dragover', e => {
      e.preventDefault();
      dropZone2.classList.add('dragover');
    });
    dropZone2.addEventListener('dragleave', () => {
      dropZone2.classList.remove('dragover');
    });
    dropZone2.addEventListener('drop', e => {
      e.preventDefault();
      dropZone2.classList.remove('dragover');
      const file = e.dataTransfer.files[0];
      if (file && fastaFile2) {
        fastaFile2.files = e.dataTransfer.files;
        if (fileName2) fileName2.textContent = file.name;
      }
    });
  }

  /* ── Timeline chart ───────────────────────────────────────── */
  function renderTimelineChart(tlData, failWeek) {
    if (!tlData || !tlData.length) return;

    const weeks        = tlData.map(d => 'Week ' + d.week);
    const resistant    = tlData.map(d => d.resistant_fraction);
    const susceptible  = tlData.map(d => d.susceptible_fraction);
    const intermediate = tlData.map(d => d.intermediate_fraction);

    const traces = [
      {
        name: 'Resistant', x: weeks, y: resistant,
        mode: 'lines+markers',
        line: { color: '#ef4444', width: 3 },
        marker: { size: 6 },
        fill: 'tozeroy', fillcolor: 'rgba(239,68,68,0.1)',
        hovertemplate: '%{x}<br>Resistant: %{y:.1f}%<extra></extra>',
      },
      {
        name: 'Intermediate', x: weeks, y: intermediate,
        mode: 'lines',
        line: { color: '#f59e0b', width: 2, dash: 'dot' },
        hovertemplate: '%{x}<br>Intermediate: %{y:.1f}%<extra></extra>',
      },
      {
        name: 'Susceptible', x: weeks, y: susceptible,
        mode: 'lines+markers',
        line: { color: '#22c55e', width: 3 },
        marker: { size: 6 },
        hovertemplate: '%{x}<br>Susceptible: %{y:.1f}%<extra></extra>',
      },
    ];

    const shapes = [{
      type: 'line',
      x0: 0, x1: tlData.length - 1, y0: 50, y1: 50,
      line: { color: 'rgba(239,68,68,0.5)', width: 1.5, dash: 'dash' },
      xref: 'x', yref: 'y',
    }];

    if (failWeek !== null && failWeek !== undefined) {
      shapes.push({
        type: 'line',
        x0: 'Week ' + failWeek, x1: 'Week ' + failWeek, y0: 0, y1: 100,
        line: { color: 'rgba(239,68,68,0.7)', width: 2, dash: 'dash' },
        xref: 'x', yref: 'y',
      });
    }

    const t = AMR.plotLayout();

    Plotly.newPlot('timelineChart', traces, {
      paper_bgcolor: t.paper_bgcolor,
      plot_bgcolor:  t.plot_bgcolor,
      margin: { t: 20, b: 60, l: 50, r: 20 },
      legend: {
        font: { color: t.tickColor },
        orientation: 'h', x: 0, y: 1.1,
      },
      xaxis: {
        tickfont: { color: t.tickColor, size: 11 },
        gridcolor: t.gridColor,
        linecolor: t.gridColor,
        tickangle: -30,
      },
      yaxis: {
        tickfont: { color: t.tickColor },
        gridcolor: t.gridColor,
        range: [0, 105],
        ticksuffix: '%',
        title: { text: 'Population %', font: { color: t.tickColor, size: 12 } },
      },
      shapes: shapes,
      annotations: [{
        x: weeks[Math.floor(weeks.length / 2)],
        y: 53,
        text: '50% — Treatment Failure Threshold',
        font: { color: 'rgba(239,68,68,0.8)', size: 10 },
        showarrow: false,
      }],
      font: { family: t.fontFamily },
      hovermode: 'x unified',
    }, { responsive: true, displayModeBar: false });
  }

  /* ── Dynamic bar widths (gene contribution bars) ─────────── */
  document.querySelectorAll('.prob-bar-fill[data-prob]').forEach(function (el) {
    el.style.width = parseFloat(el.dataset.prob).toFixed(1) + '%';
  });

  /* Auto-init from data islands */
  const tlEl   = document.getElementById('timeline-chart-data');
  const fwEl   = document.getElementById('timeline-fail-week');
  if (tlEl) {
    try {
      const tlData   = JSON.parse(tlEl.textContent);
      const failWeek = fwEl ? JSON.parse(fwEl.textContent) : null;
      renderTimelineChart(tlData, failWeek);
    } catch (_) {}
  }

})();

/* ── Tab switching (called via onclick in template) ───────────── */
window.switchTab2 = function (tab, btn) {
  document.querySelectorAll('#fastaTab2 .nav-link').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('fileTab2').classList.toggle('d-none', tab !== 'file');
  document.getElementById('textTab2').classList.toggle('d-none', tab !== 'text');
};

/* ── Load sample genome ───────────────────────────────────────── */
window.loadSample2 = function () {
  const textarea = document.querySelector('#textTab2 textarea');
  if (textarea) {
    textarea.value = `>sample_Ecoli_genome
ATGAAACGCATTAGCACCACCATTACCACCACCATCACCATTACCACAGGTAACGGTGCGGGCTGACGCGTACAGGAAACACAGAAAAAAGCCCGCACCTGACAGTGCGGGCTTTTTTTTTCGACCAAAGGTAACGAGGTAACAACCATGCGAGTGTTGAAGTTCGGCGGTACATCAGTGGCAAATGCAGAACGTTTTCTGCGCGTTGTTACGCGCATTTTCTGATATTCGATTCGCATCATTTTCGGTCGGGTATCGCGGCGTTTGCTAAAAAACGTCAGCGTTTGCAGTTTTCGCTGAAACAGATGCGTATTTCGGTTTATCTCAAAAGTTCGTTTAGTAACAACGATGCGTAAAGCAGCATTAACGAAACAGTTTCAACGTTTGGCTGAAACGCAGTTTAAAGCTCAACGCAACAGTTTGCAAACGCAGCGCAATTTAAACAAGCGTTTGCAGAAACG`;
  }
  const textBtn = document.querySelectorAll('#fastaTab2 .nav-link')[1];
  if (textBtn) switchTab2('text', textBtn);
};

/* ── Toggle data table ────────────────────────────────────────── */
window.toggleTable = function () {
  const tbl = document.getElementById('timelineTable');
  const ch  = document.getElementById('tableChevron');
  if (!tbl) return;
  const hidden = tbl.classList.contains('d-none');
  tbl.classList.toggle('d-none', !hidden);
  if (ch) ch.className = hidden ? 'bi bi-chevron-up' : 'bi bi-chevron-down';
};
