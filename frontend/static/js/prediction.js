/* ============================================================
   AMRPredict — Prediction Page (resistance_prediction.html)
   Tab switching, drag-drop, sample FASTA, and k-mer chart.
   Chart data is read from <script type="application/json" id="kmer-chart-data">.
   Expects: window.AMR (from main.js), Plotly (CDN)
   ============================================================ */

(function () {
  'use strict';

  /* ── Threshold slider ─────────────────────────────────────── */
  const slider    = document.getElementById('threshSlider2');
  const sliderVal = document.getElementById('threshVal2');
  if (slider && sliderVal) {
    slider.addEventListener('input', function () {
      sliderVal.textContent = this.value;
      this.setAttribute('aria-valuenow', this.value);
    });
  }

  /* ── File name display ────────────────────────────────────── */
  const fastaFile = document.getElementById('fastaFile');
  const fileName  = document.getElementById('fileName');
  if (fastaFile && fileName) {
    fastaFile.addEventListener('change', function () {
      fileName.textContent = this.files[0] ? this.files[0].name : '';
    });
  }

  /* ── Drag-and-drop ────────────────────────────────────────── */
  const dropZone = document.getElementById('dropZone');
  if (dropZone) {
    dropZone.addEventListener('dragover', e => {
      e.preventDefault();
      dropZone.classList.add('dragover');
    });
    dropZone.addEventListener('dragleave', () => {
      dropZone.classList.remove('dragover');
    });
    dropZone.addEventListener('drop', e => {
      e.preventDefault();
      dropZone.classList.remove('dragover');
      const file = e.dataTransfer.files[0];
      if (file && fastaFile) {
        fastaFile.files = e.dataTransfer.files;
        if (fileName) fileName.textContent = file.name;
      }
    });
  }

  /* ── Dynamic bar widths (set from data-prob / data-kw attrs) ─ */
  document.querySelectorAll('.prob-bar-fill[data-prob]').forEach(function (el) {
    el.style.width = parseFloat(el.dataset.prob).toFixed(1) + '%';
  });
  document.querySelectorAll('.kmer-bar[data-kw]').forEach(function (el) {
    el.style.width = parseInt(el.dataset.kw, 10) + '%';
  });

  /* ── K-mer chart ──────────────────────────────────────────── */
  function renderKmerChart(kmers) {
    if (!kmers || !kmers.length) return;
    const t = AMR.plotLayout();

    Plotly.newPlot('kmerChart', [{
      type: 'bar',
      x: kmers.slice(0, 20).map(k => k.kmer),
      y: kmers.slice(0, 20).map(k => k.frequency),
      marker: {
        color: 'rgba(99,102,241,0.82)',
        line: { color: 'rgba(79,70,229,1)', width: 1 },
      },
      hovertemplate: '<b>%{x}</b><br>Frequency: %{y:.5f}<extra></extra>',
    }], {
      paper_bgcolor: t.paper_bgcolor,
      plot_bgcolor:  t.plot_bgcolor,
      margin: { t: 10, b: 50, l: 60, r: 10 },
      xaxis: {
        tickfont: { family: "'JetBrains Mono',monospace", size: 10, color: t.tickColor },
        gridcolor: t.gridColor,
        linecolor: t.gridColor,
      },
      yaxis: {
        tickfont: { color: t.tickColor, size: 10 },
        gridcolor: t.gridColor,
        title: { text: 'Frequency', font: { color: t.tickColor, size: 11 } },
      },
      font: { family: t.fontFamily },
    }, { responsive: true, displayModeBar: false });
  }

  const dataEl = document.getElementById('kmer-chart-data');
  if (dataEl) {
    try { renderKmerChart(JSON.parse(dataEl.textContent)); } catch (_) {}
  }

})();

/* ── Tab switching (called via onclick in template) ───────────── */
window.switchTab = function (tab, btn) {
  document.querySelectorAll('#fastaTab .nav-link').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('fileTab').classList.toggle('d-none', tab !== 'file');
  document.getElementById('textTab').classList.toggle('d-none', tab !== 'text');
};

/* ── Load sample FASTA ────────────────────────────────────────── */
window.loadSampleFasta = function () {
  const sample = `>sample_genome_E_coli_K12
ATGAAACGCATTAGCACCACCATTACCACCACCATCACCATTACCACAGGTAACGGTGCGGGCTGACGCGTACAGGAAACACAGAAAAAAGCCCGCACCTGACAGTGCGGGCTTTTTTTTTCGACCAAAGGTAACGAGGTAACAACCATGCGAGTGTTGAAGTTCGGCGGTACATCAGTGGCAAATGCAGAACGTTTTCTGCGCGTTGTTACGCGCATTTTCTGATATTCG
GCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGCATGC
ATGAAACGCATTAGCACCACCATTACCACCACCATCACCATTACCACAGGTAACGGTGCGGGCTGACGCGTACAGGAAACACAGAAAAAAGCCCGCACCTGACAGTGCGGGCTTTTTTTTTCGACCAAAGGTAACGAGGT`;
  const textarea = document.querySelector('textarea[name=fasta_text]');
  if (textarea) textarea.value = sample;
  const textBtn = document.querySelectorAll('#fastaTab .nav-link')[1];
  if (textBtn) switchTab('text', textBtn);
};
