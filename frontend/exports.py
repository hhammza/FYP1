"""CSV and PDF downloads of a result shown on /forecast, /predict or /timeline.

The page posts back the result it rendered (JSON), its inputs, and for a PDF a
PNG of its chart. The model details (name, run, AUC, threshold) are added
here from the metrics files, never taken from the page, so a download cannot
carry numbers the server did not produce.
"""
import base64
import csv
import io
from datetime import datetime, timezone
from xml.sax.saxutils import escape

DISCLAIMER = 'Research tool, not a clinical diagnostic. Do not use it for treatment decisions.'
SIMULATION = 'Simulation, not a trained model'

TITLES = {
    'forecast': 'Resistance forecast',
    'predict': 'Genomic resistance prediction',
    'timeline': 'Mutation timeline',
    'batch': 'Batch resistance forecast',
}

MAX_CHART_BYTES = 5 * 1024 * 1024


def now_utc():
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')


def _cell(value):
    """A CSV cell that a spreadsheet will not run as a formula.

    Values echoed from an uploaded file could start with =, +, - or @; a
    leading apostrophe keeps them as text. Plain negative numbers stay.
    """
    if value is None:
        return ''
    if isinstance(value, bool):
        return 'yes' if value else 'no'
    text = str(value)
    if text[:1] in ('=', '+', '@', '\t', '\r') or (text[:1] == '-' and not _is_number(text)):
        return "'" + text
    return text


def _is_number(text):
    try:
        float(text)
        return True
    except ValueError:
        return False


def _pct(p):
    return f'{p * 100:.1f}%' if isinstance(p, (int, float)) else ''


def genes_text(result):
    """The genes behind a /predict result as one line; the format's three cases."""
    genes = result.get('genes_found')
    if genes is None:
        return 'not searched'
    if not genes:
        return 'none found'
    ordered = sorted(genes, key=lambda g: (not g.get('relevant'), g.get('gene', '')))
    return '; '.join(f"{g.get('gene')} ({g.get('drug_class') or 'unknown'}"
                     f"{', linked' if g.get('relevant') else ''})" for g in ordered)


def species_text(result):
    """The species the gene model identified from the genome ('' for the
    k-mer model, which does not identify one)."""
    found = result.get('species_detected')
    if not isinstance(found, dict):
        return ''
    if found.get('species'):
        return found['species']
    if found.get('genus'):
        return f"{found['genus']} (genus only)"
    return 'not identified'


def _csv(header, rows):
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    for r in rows:
        w.writerow([_cell(v) for v in r])
    return buf.getvalue()


# ── CSV ──────────────────────────────────────────────────────────────────

def build_csv(page, result, inputs, model):
    """CSV text for one page's result. `model` is summarize_metrics() output."""
    stamp = now_utc()
    if page == 'forecast':
        header = ['exported_at', 'antibiotic', 'genus', 'species', 'taxon_id', 'mic_value', 'mic_sign',
                  'prediction', 'probability_resistant', 'confidence_pct', 'threshold', 'drug_class',
                  'model_used', 'model_run', 'calibrated', 'model_auc_unseen_genomes', 'note']
        row = [stamp, result.get('antibiotic'), inputs.get('genus'), inputs.get('species'),
               inputs.get('taxon_id'), inputs.get('mic_value'), inputs.get('mic_sign'),
               result.get('prediction'), result.get('probability'), result.get('confidence'),
               result.get('threshold'), result.get('drug_class'), result.get('model_used'),
               result.get('model_run'), result.get('calibrated'), model['auc_ci'], DISCLAIMER]
        return _csv(header, [row])

    if page == 'predict':
        kmers = ';'.join(f"{k.get('kmer')}:{k.get('frequency')}" for k in (result.get('top_kmers') or [])[:20])
        header = ['exported_at', 'antibiotic', 'antibiotic_known', 'prediction', 'probability_resistant',
                  'confidence_pct', 'threshold', 'sequence_length', 'gc_content_pct', 'model_used',
                  'model_auc_unseen_genomes', 'species_identified', 'resistance_genes', 'top_kmers',
                  'warning', 'note']
        row = [stamp, result.get('antibiotic'), result.get('antibiotic_known'), result.get('prediction'),
               result.get('probability'), result.get('confidence'), result.get('threshold'),
               result.get('sequence_length'), result.get('gc_content'), result.get('model_used'),
               model['auc_ci'], species_text(result), genes_text(result), kmers,
               result.get('warning') or '', DISCLAIMER]
        return _csv(header, [row])

    if page == 'timeline':
        header = ['week', 'susceptible_pct', 'intermediate_pct', 'resistant_pct', 'cumulative_mutations',
                  'mic_fold_change', 'treatment_effective', 'antibiotic', 'failure_week', 'seed', 'source']
        rows = [[w.get('week'), w.get('susceptible_fraction'), w.get('intermediate_fraction'),
                 w.get('resistant_fraction'), w.get('cumulative_mutations'), w.get('mic_fold_change'),
                 w.get('treatment_effective'), result.get('antibiotic'), result.get('failure_week'),
                 result.get('seed'), SIMULATION]
                for w in result.get('timeline') or []]
        return _csv(header, rows)

    if page == 'batch':
        header = ['row', 'antibiotic', 'genus', 'species', 'taxon_id', 'mic_value', 'mic_sign',
                  'prediction', 'probability_resistant', 'error']
        rows = [[r.get(k) for k in ('row', 'antibiotic', 'genus', 'species', 'taxon_id', 'mic_value',
                                    'mic_sign', 'prediction', 'probability', 'error')]
                for r in result.get('rows') or []]
        return _csv(header, rows)

    raise ValueError(f'unknown page {page!r}')


# ── PDF ──────────────────────────────────────────────────────────────────

def decode_chart(data_url):
    """PNG bytes from a `data:image/png;base64,...` URL, or None if it is not one."""
    prefix = 'data:image/png;base64,'
    if not data_url or not data_url.startswith(prefix):
        return None
    try:
        png = base64.b64decode(data_url[len(prefix):], validate=True)
    except (ValueError, TypeError):
        return None
    if len(png) > MAX_CHART_BYTES or not png.startswith(b'\x89PNG\r\n\x1a\n'):
        return None
    return png


def _model_rows(page, model, result):
    if page == 'timeline':
        return [
            ['Method', 'Logistic-growth simulation with hand-set, literature-based constants'],
            ['Trained model', 'None: ' + SIMULATION.lower()],
            ['Validated', 'No, not against patient data'],
            ['Calibration', 'not calibrated' if not result.get('calibration') else str(result.get('calibration'))],
            ['Seed', str(result.get('seed', ''))],
        ]
    return [
        ['Model', model['algorithm'] or result.get('model_used') or ''],
        ['Model run', model['run_id'] or result.get('model_run') or ''],
        ['AUC on unseen genomes', model['auc_ci']],
        ['Default threshold', f"{model['threshold']}" + (f" ({model['threshold_rule']})" if model['threshold_rule'] else '')],
        ['Evaluation', model['split'] or 'not recorded'],
    ]


def _result_rows(page, result, inputs):
    if page == 'forecast':
        rows = [['Antibiotic', result.get('antibiotic')],
                ['Organism', ' '.join(v for v in (inputs.get('genus'), inputs.get('species')) if v) or 'not given'],
                ['Taxon ID', inputs.get('taxon_id') or 'not given'],
                ['MIC', f"{inputs.get('mic_sign') or ''} {inputs.get('mic_value')} mg/L".strip()
                 if inputs.get('mic_value') else 'not given'],
                ['Prediction', result.get('prediction')],
                ['P(resistant)', _pct(result.get('probability'))],
                ['Threshold used', result.get('threshold')],
                ['Drug class', (result.get('drug_class') or '').replace('_', ' ')],
                ['Model used', result.get('model_used')]]
        if result.get('evidence', {}).get('label'):
            rows.append(['Evidence', result['evidence']['label']])
        return rows
    if page == 'predict':
        return [['Antibiotic', result.get('antibiotic')],
                ['Model knows this antibiotic', 'yes' if result.get('antibiotic_known', True) else 'no'],
                ['Prediction', result.get('prediction')],
                ['P(resistant)', _pct(result.get('probability'))],
                ['Threshold used', result.get('threshold')],
                ['Sequence length', f"{result.get('sequence_length', 0):,} bp"],
                ['GC content', f"{result['gc_content']}%" if result.get('gc_content') is not None
                 else 'not reported by this model'],
                ['Model used', result.get('model_used')],
                *([['Identified as', species_text(result)]] if species_text(result) else []),
                ['Resistance genes', genes_text(result)],
                *([['Warning', result['warning']]] if result.get('warning') else [])]
    if page == 'timeline':
        fw = result.get('failure_week')
        return [['Antibiotic', result.get('antibiotic')],
                ['Drug class', result.get('antibiotic_class')],
                ['Weeks simulated', result.get('n_weeks')],
                ['Treatment failure (resistant >= 50%)', f'week {fw}' if fw else 'not reached'],
                ['Final resistant share', f"{result.get('final_resistant_percent', 0):.1f}%"],
                ['Genome', f"{result.get('sequence_length', 0):,} bp, GC {result.get('gc_content')}%"],
                ['Summary', result.get('summary')]]
    raise ValueError(f'unknown page {page!r}')


def _extra_table(page, result):
    """(title, header, rows) for the page's detail table, or None."""
    if page == 'forecast' and result.get('comparison_chart'):
        return ('Other common antibiotics, same organism, no MIC', ['Antibiotic', 'P(resistant)'],
                [[c['antibiotic'], f"{c['resistance_probability']:.1f}%"] for c in result['comparison_chart']])
    if page == 'predict' and result.get('top_kmers'):
        return ('Most frequent 4-mers', ['4-mer', 'Frequency'],
                [[k['kmer'], f"{k['frequency']:.5f}"] for k in result['top_kmers'][:10]])
    if page == 'timeline' and result.get('timeline'):
        return ('Week by week (' + SIMULATION.lower() + ')',
                ['Week', 'Susceptible', 'Intermediate', 'Resistant', 'MIC fold'],
                [[w['week'], f"{w['susceptible_fraction']:.1f}%", f"{w['intermediate_fraction']:.1f}%",
                  f"{w['resistant_fraction']:.1f}%", w.get('mic_fold_change')] for w in result['timeline']])
    return None


def build_pdf(page, result, inputs, model, chart_png=None):
    """PDF bytes for one page's result."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    small = ParagraphStyle('small', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#475569'))
    body = ParagraphStyle('body', parent=styles['Normal'], fontSize=9, leading=12)
    banner = ParagraphStyle('banner', parent=styles['Normal'], fontSize=11, leading=14,
                            textColor=colors.HexColor('#92400e'), backColor=colors.HexColor('#fef3c7'),
                            borderPadding=6, spaceAfter=10)

    def para(v, style=body):
        return Paragraph(escape('' if v is None else str(v)), style)

    def table(rows, header=None, widths=None):
        data = ([[para(h) for h in header]] if header else []) + [[para(c) for c in r] for r in rows]
        t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
        style = [('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#cbd5e1')),
                 ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                 ('BACKGROUND', (0, 0), (0 if not header else -1, -1 if not header else 0),
                  colors.HexColor('#f1f5f9'))]
        t.setStyle(TableStyle(style))
        return t

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                            title=f'AMR Intelligence Platform: {TITLES[page]}', author='AMR Intelligence Platform')
    story = [Paragraph(escape(f'AMR Intelligence Platform: {TITLES[page]}'), styles['Title']),
             para(f'Generated {now_utc()}', small), Spacer(1, 8)]
    if page == 'timeline':
        story.append(Paragraph(f'<b>{escape(SIMULATION)}.</b> These curves come from a simulation with '
                               'hand-set constants, not from a model trained on data.', banner))

    story += [Paragraph('Result', styles['Heading2']),
              table(_result_rows(page, result, inputs), widths=[5.5 * cm, 11.5 * cm]),
              Spacer(1, 6),
              Paragraph('Model' if page != 'timeline' else 'Method', styles['Heading2']),
              table(_model_rows(page, model, result), widths=[5.5 * cm, 11.5 * cm])]

    if chart_png:
        img = Image(io.BytesIO(chart_png))
        scale = min(17 * cm / img.imageWidth, 9 * cm / img.imageHeight)
        img.drawWidth, img.drawHeight = img.imageWidth * scale, img.imageHeight * scale
        story += [Spacer(1, 6), Paragraph('Chart', styles['Heading2']), img]

    genes = result.get('genes_found') if page == 'predict' else None
    if genes:
        ordered = sorted(genes, key=lambda g: (not g.get('relevant'), g.get('gene', '')))
        story += [Spacer(1, 6), Paragraph('Resistance genes found (AMRFinderPlus)', styles['Heading2']),
                  table([[g.get('gene'), 'mutation' if g.get('type') == 'point_mutation' else 'gene',
                          g.get('drug_class') or '', 'yes' if g.get('relevant') else '']
                         for g in ordered],
                        header=['Gene or mutation', 'Type', 'Drug class', "Linked to this drug's class"])]

    extra = _extra_table(page, result)
    if extra:
        title, header, rows = extra
        story += [Spacer(1, 6), Paragraph(escape(title), styles['Heading2']), table(rows, header=header)]

    story += [Spacer(1, 14), Paragraph(f'<b>{escape(DISCLAIMER)}</b>', body)]
    if page == 'timeline':
        story.append(para(SIMULATION + '.', body))
    doc.build(story)
    return buf.getvalue()
