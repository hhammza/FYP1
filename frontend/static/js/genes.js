/* ============================================================
   AMRPredict — Resistance Genes page (/genes)
   Expects: window.AMR (main.js), AMRReport (report-charts.js), Plotly,
            #report-data JSON embedded by genes.html
   ============================================================ */
(function () {
  'use strict';

  const report = AMRReport.readData('report-data');
  if (!report) return;
  const { config, palette, layout, legendName } = AMRReport;
  const pct1 = x => (100 * x).toFixed(1) + '%';
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const title = s => String(s || '').toLowerCase().replace(/(^|[\/\s-])\w/g, m => m.toUpperCase());

  function wrapLabel(label) {
    if (label.length <= 22) return label;
    const cut = label.lastIndexOf('/', 22);
    return cut > 0 ? label.slice(0, cut + 1) + '<br>' + label.slice(cut + 1) : label;
  }

  /* Colour follows the kind of element, never its rank */
  const KINDS = {
    gene:           { label: 'Acquired gene',  color: 'c1' },
    point_mutation: { label: 'Point mutation', color: 'c2' },
  };

  /* ── Top genes ─────────────────────────────────────────────── */
  function renderTop() {
    const p = palette();
    const rows = report.top_genes;
    const order = rows.map(r => r.gene).reverse();   // most common at the top
    const traces = Object.entries(KINDS).map(([kind, k]) => {
      const sub = rows.filter(r => r.type === kind);
      return {
        type: 'bar', orientation: 'h', name: legendName(k.label),
        x: sub.map(r => 100 * r.share), y: sub.map(r => r.gene),
        marker: { color: p[k.color], line: { width: 0 } },
        customdata: sub.map(r => [r.name || '', title(r.class), title(r.subclass), r.genomes]),
        hovertemplate: '<b>%{y}</b><br>%{customdata[0]}<br>%{customdata[1]} · %{customdata[2]}'
          + '<br>%{customdata[3]:,} genomes (%{x:.1f}%)<extra></extra>',
      };
    }).filter(t => t.x.length);
    Plotly.react('topChart', traces, layout({
      barmode: 'relative', bargap: 0.35,
      margin: { t: 10, r: 16, b: 70, l: 110 },
      xaxis: { title: { text: 'Genomes carrying it' }, ticksuffix: '%', rangemode: 'tozero' },
      yaxis: { categoryorder: 'array', categoryarray: order, automargin: true, gridcolor: 'rgba(0,0,0,0)' },
      showlegend: traces.length > 1,
    }), config);
  }

  /* ── Genes per genome ──────────────────────────────────────── */
  function renderPerGenome() {
    const p = palette();
    const rows = report.genes_per_genome;
    const labels = rows.map(r => r.capped ? r.genes + '+' : String(r.genes));
    Plotly.react('perGenomeChart', [{
      type: 'bar', x: labels, y: rows.map(r => r.genomes),
      marker: { color: p.c1, line: { width: 0 } },
      hovertemplate: '%{x} genes: %{y:,} genomes<extra></extra>',
    }], layout({
      bargap: 0.25, showlegend: false,
      xaxis: { title: { text: 'Resistance genes and mutations in the genome' }, type: 'category' },
      yaxis: { title: { text: 'Genomes' }, rangemode: 'tozero' },
    }), config);
  }

  /* ── Drug classes ──────────────────────────────────────────── */
  function renderClasses() {
    const p = palette();
    const rows = report.classes.slice(0, 14);
    Plotly.react('classChart', [{
      type: 'bar', orientation: 'h',
      /* Long combined classes wrap onto two lines instead of being clipped */
      x: rows.map(r => 100 * r.share), y: rows.map(r => wrapLabel(title(r.class))),
      marker: { color: p.c1, line: { width: 0 } },
      customdata: rows.map(r => [r.genomes, r.symbols]),
      hovertemplate: '<b>%{y}</b><br>%{customdata[0]:,} genomes (%{x:.1f}%)'
        + '<br>%{customdata[1]} different genes or mutations<extra></extra>',
    }], layout({
      bargap: 0.35, showlegend: false,
      margin: { t: 10, r: 16, b: 48, l: 10 },
      xaxis: { title: { text: 'Genomes with a gene for this class' }, ticksuffix: '%', rangemode: 'tozero' },
      yaxis: { autorange: 'reversed', automargin: true, gridcolor: 'rgba(0,0,0,0)' },
    }), config);
  }

  /* ── Genus x gene heatmap (one hue, light to dark) ─────────── */
  function renderHeat() {
    const p = palette();
    const h = report.heatmap;
    if (!h.genera.length) return;
    Plotly.react('heatChart', [{
      type: 'heatmap', x: h.genes, y: h.genera, z: h.share.map(r => r.map(v => 100 * v)),
      colorscale: [[0, p.card], [1, p.c1]], zmin: 0, zmax: 100, xgap: 2, ygap: 2,
      colorbar: { ticksuffix: '%', thickness: 10, outlinewidth: 0, tickfont: { color: p.text2, size: 11 } },
      hovertemplate: '<b>%{y}</b> · %{x}<br>%{z:.1f}% of genomes<extra></extra>',
    }], layout({
      margin: { t: 10, r: 16, b: 110, l: 110 },
      xaxis: { tickangle: -40, gridcolor: 'rgba(0,0,0,0)' },
      yaxis: { autorange: 'reversed', gridcolor: 'rgba(0,0,0,0)', tickfont: { color: p.text2, size: 12 } },
    }), config);
  }

  /* ── Gene vs lab result ────────────────────────────────────── */
  let labels = 'lab';
  let showAll = false;
  const FIRST_ROWS = 12;

  function meter(share, cls) {
    if (share === null || share === undefined) return '<span class="text-muted">n/a</span>';
    const w = Math.max(2, Math.round(100 * share));
    return `<div class="lab-meter"><span class="lab-meter-track"><span class="lab-meter-fill ${cls}" style="width:${w}%"></span></span>`
      + `<span class="lab-meter-val">${pct1(share)}</span></div>`;
  }

  function renderLab() {
    const v = report.gene_vs_lab[labels];
    const body = document.querySelector('#labTable tbody');
    if (!v.pairs.length) {
      body.innerHTML = '<tr><td colspan="6" class="text-muted">Not enough labelled genomes yet.</td></tr>';
    } else {
      const rows = showAll ? v.pairs : v.pairs.slice(0, FIRST_ROWS);
      body.innerHTML = rows.map(r => `<tr>
        <td><code>${esc(r.gene)}</code><div class="caption-text">${esc(title(r.gene_subclass))}</div></td>
        <td>${esc(r.antibiotic)}</td>
        <td class="text-end">${r.carriers.toLocaleString()}</td>
        <td>${meter(r.carriers_resistant, 'with')}</td>
        <td class="text-end">${r.others.toLocaleString()}</td>
        <td>${meter(r.others_resistant, 'without')}</td></tr>`).join('');
    }
    const shown = showAll ? v.pairs.length : Math.min(FIRST_ROWS, v.pairs.length);
    const more = document.getElementById('labMore');
    more.classList.toggle('d-none', v.pairs.length <= FIRST_ROWS);
    more.textContent = showAll ? 'Show fewer' : `Show all ${v.pairs.length}`;
    document.getElementById('labCaption').textContent =
      `${shown} of ${v.pairs_total} gene and antibiotic pairs with at least ${v.min_carriers} genomes carrying the gene, `
      + `most genomes first. Over ${v.genomes_labelled.toLocaleString()} genomes with `
      + (labels === 'lab' ? 'a laboratory result.' : 'any label.');
    document.getElementById('compNote').classList.toggle('d-none', labels === 'lab');
    document.querySelectorAll('[data-labels]').forEach(b => {
      const on = b.dataset.labels === labels;
      b.classList.toggle('active', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
  }

  document.querySelectorAll('[data-labels]').forEach(b => b.addEventListener('click', () => {
    labels = b.dataset.labels;
    renderLab();
  }));
  document.getElementById('labMore').addEventListener('click', () => {
    showAll = !showAll;
    renderLab();
  });

  /* ── Genome lookup ─────────────────────────────────────────── */
  const KIND_LABEL = { gene: 'Gene', point_mutation: 'Mutation' };

  async function lookup(id) {
    const out = document.getElementById('lookupResult');
    id = id.trim();
    if (!id) return;
    out.innerHTML = '<p class="text-muted small mb-0">Looking up…</p>';
    let data;
    try {
      const r = await fetch('/api/genes/' + encodeURIComponent(id));
      data = await r.json();
      if (!r.ok) throw new Error(data.error || 'HTTP ' + r.status);
    } catch (e) {
      out.innerHTML = `<p class="text-danger small mb-0">${esc(e.message)}</p>`;
      return;
    }
    if (!data.searched) {
      out.innerHTML = `<p class="small mb-0"><strong>${esc(id)}</strong> was not searched: it is not one of our genomes,`
        + ' its complete assembly could not be downloaded, or the run has not reached it yet.</p>';
      return;
    }
    const head = `<p class="small mb-2"><strong>${esc(data.genome_id)}</strong> · <em>${esc(data.species)}</em> · `
      + (data.genes.length ? `${data.genes.length} resistance gene${data.genes.length > 1 ? 's' : ''} and mutations`
                           : 'searched, no core resistance gene or mutation found') + '</p>';
    if (!data.genes.length) { out.innerHTML = head; return; }
    const rows = data.genes.map(g => `<tr>
      <td><code>${esc(g.gene)}</code><div class="caption-text">${esc(g.name)}</div></td>
      <td>${esc(KIND_LABEL[g.type] || g.type)}</td>
      <td>${esc(title(g.class))}<div class="caption-text">${esc(title(g.subclass))}</div></td>
      <td class="text-end">${g.identity.toFixed(1)}%</td>
      <td class="text-end">${g.coverage.toFixed(1)}%</td>
      <td class="small">${esc(g.method)}</td></tr>`).join('');
    out.innerHTML = head + `<div class="table-responsive"><table class="table table-custom table-sm mb-0">
      <thead><tr><th>Gene or mutation</th><th>Type</th><th>Drug class</th>
      <th class="text-end">Identity</th><th class="text-end">Coverage</th><th>Method</th></tr></thead>
      <tbody>${rows}</tbody></table></div>`;
  }

  document.getElementById('lookupForm').addEventListener('submit', e => {
    e.preventDefault();
    const id = document.getElementById('genomeId').value.trim();
    history.replaceState(null, '', '#genome=' + encodeURIComponent(id));
    lookup(id);
  });
  document.querySelectorAll('.lookup-example').forEach(a => a.addEventListener('click', e => {
    e.preventDefault();
    document.getElementById('genomeId').value = a.dataset.id;
    history.replaceState(null, '', '#genome=' + encodeURIComponent(a.dataset.id));
    lookup(a.dataset.id);
    document.getElementById('lookup').scrollIntoView({ behavior: 'smooth' });
  }));

  /* /genes#genome=1000561.3 opens with that genome looked up, for sharing */
  const linked = decodeURIComponent((location.hash.match(/^#genome=(.+)$/) || [])[1] || '');
  if (linked) {
    document.getElementById('genomeId').value = linked;
    lookup(linked);
    document.getElementById('lookup').scrollIntoView();
  }

  AMRReport.draw(() => { renderTop(); renderPerGenome(); renderClasses(); renderHeat(); });
  renderLab();
})();
