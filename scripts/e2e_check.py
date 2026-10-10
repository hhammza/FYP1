"""End-to-end check of the website in a real browser (T2.7; docs/E2E_CHECKLIST.md).

Opens every page, submits every form and downloads every export, the way a
user would, and prints a tick or a cross per step.

    python scripts/e2e_check.py --start                 # start both servers here, check, stop them
    python scripts/e2e_check.py                         # servers already running (start.bat)
    python scripts/e2e_check.py --base https://...      # the deployed site (Week 5)

Needs Playwright: python -m pip install playwright, then
python -m playwright install chromium (or use --browser msedge on Windows).
For /predict it downloads one complete genome the served model never trained
on from BV-BRC (as scripts/ci_docker_smoke.py does); --no-genome skips that.
Exit code 0 only if every step passed.
"""
import argparse
import os
import subprocess
import sys
import tempfile
import time
import traceback
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))

PAGES = ['/', '/forecast', '/predict', '/timeline', '/models', '/compare', '/genes', '/datasets', '/about',
         '/library', '/train']
results = []


def step(name):
    """Decorator: run one check, record pass/fail, never stop the run."""
    def wrap(fn):
        def run(*a, **kw):
            start = time.time()
            try:
                detail = fn(*a, **kw) or ''
                results.append((True, name, detail, time.time() - start))
                print(f'  ✓ {name}' + (f'  ({detail})' if detail else ''), flush=True)
            except Exception as e:
                results.append((False, name, f'{type(e).__name__}: {e}', time.time() - start))
                print(f'  ✗ {name}: {type(e).__name__}: {str(e)[:300]}', flush=True)
                if os.environ.get('E2E_DEBUG'):
                    traceback.print_exc()
        return run
    return wrap


def check(cond, message):
    if not cond:
        raise AssertionError(message)


# ── servers ────────────────────────────────────────────────────────────
def wait_for(url, seconds):
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                if r.status < 500:
                    return True
        except OSError:
            time.sleep(1)
    return False


def start_servers():
    env = dict(os.environ, DEBUG='True')
    env.pop('PORT', None)
    py = sys.executable
    back = subprocess.Popen([py, 'manage.py', 'runserver', '8000', '--noreload'], cwd=os.path.join(ROOT, 'backend'),
                            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    front = subprocess.Popen([py, 'app.py'], cwd=os.path.join(ROOT, 'frontend'), env=env,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not (wait_for('http://127.0.0.1:8000/api/health/', 180) and wait_for('http://127.0.0.1:5001/', 60)):
        stop_servers([back, front])
        sys.exit('the servers did not start (is the venv set up? try start.bat once)')
    return [back, front]


def stop_servers(procs):
    for p in procs:
        p.terminate()
        try:
            p.wait(10)
        except subprocess.TimeoutExpired:
            p.kill()


# ── the checks ─────────────────────────────────────────────────────────
def main(a):
    from playwright.sync_api import sync_playwright

    base = a.base.rstrip('/')
    genome = None
    if not a.no_genome:
        try:
            import ci_docker_smoke as smoke
            run_id, ids = smoke.test_genomes()
            for gid in ids[:10]:
                data = smoke.download(gid)
                if data:
                    genome = os.path.join(tempfile.gettempdir(), f'e2e_{gid}.fna')
                    with open(genome, 'wb') as fh:
                        fh.write(data)
                    print(f'genome for /predict: {gid}, a test genome of {run_id} ({len(data) / 1e6:.1f} MB)')
                    break
        except Exception as e:
            print(f'(no genome downloaded, /predict with a full genome is skipped: {e})')

    with sync_playwright() as p:
        browser = p.chromium.launch(channel=a.browser if a.browser != 'chromium' else None)
        ctx = browser.new_context(viewport={'width': 1366, 'height': 1000}, accept_downloads=True)
        page = ctx.new_page()
        page.set_default_timeout(30_000)
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        failed_local = []
        page.on('requestfailed', lambda r: failed_local.append(r.url) if r.url.startswith(base) else None)

        def goto(path):
            errors.clear()
            failed_local.clear()
            r = page.goto(base + path, wait_until='networkidle')
            check(r is not None and r.status == 200, f'{path} answered {r.status if r else "nothing"}')
            return r

        def select_when_ready(selector, value):
            page.wait_for_function(f"document.querySelectorAll('{selector} option').length > 1")
            page.select_option(selector, value)

        def download(click, expect_start, name):
            with page.expect_download(timeout=60_000) as info:
                click()
            path = info.value.path()
            with open(path, 'rb') as fh:
                head = fh.read(16)
            check(head.startswith(expect_start), f'{name} starts {head[:8]!r}, expected {expect_start!r}')
            return f'{info.value.suggested_filename}, {os.path.getsize(path):,} bytes'

        def downloads(page_name, png=True, pdf=True):
            bar = f'form.export-bar[data-export-page="{page_name}"]'
            got = [download(lambda: page.click(f'{bar} button[formaction$=".csv"]'), b'', 'CSV')]
            if pdf:
                got.append(download(lambda: page.click(f'{bar} [data-export="pdf"]'), b'%PDF', 'PDF'))
            if png:
                got.append(download(lambda: page.click(f'{bar} [data-export="png"]'), b'\x89PNG', 'PNG'))
            return '; '.join(got)

        print(f'\nChecking {base}')

        @step('Backend health: every model loaded')
        def health():
            # a few tries: Flask's debug server restarts itself once just after it starts
            for attempt in range(5):
                try:
                    r = page.request.get(base + '/api/health', timeout=30_000)
                    if r.ok:
                        break
                except Exception:
                    pass
                time.sleep(3)
            check(r.ok, f'/api/health answered {r.status}')
            d = r.json()
            models = d.get('models') or {}
            check(models.get('lgbm_forecasting', {}).get('trained'), 'the forecaster is not loaded')
            check(models.get('kmer_resistance', {}).get('trained'), 'the genome model is not loaded')
            k = models['kmer_resistance']
            return f"forecast {models['lgbm_forecasting'].get('run_id')}, predict {k.get('run_id')}" \
                   f"{' (gene model)' if k.get('searches_genes') else ''}"
        health()

        for path in PAGES:
            @step(f'Page {path} opens with no errors')
            def open_page(path=path):
                goto(path)
                check(not errors, f'JavaScript errors: {errors[:2]}')
                check(not failed_local, f'files that did not load: {failed_local[:3]}')
            open_page()

        @step('/forecast: genus -> species -> taxon lists, MIC suggestions')
        def forecast_lists():
            goto('/forecast')
            select_when_ready('#forecastForm [name=antibiotic]', 'ciprofloxacin')
            select_when_ready('#genusSelect', 'Escherichia')
            page.select_option('#speciesSelect', 'coli')
            page.wait_for_function("document.getElementById('micHint').textContent.includes('coli')")
            taxa = page.eval_on_selector_all('#taxonSelect option', 'os => os.map(o => o.value).filter(Boolean)')
            check('562' in taxa, f'taxon 562 not offered: {taxa}')
            return f'taxon IDs {taxa}'
        forecast_lists()

        @step('/forecast: "Fill from Genome ID" fills the organism and shows the lab result')
        def genome_fill():
            page.select_option('#forecastForm [name=antibiotic]', 'gentamicin')
            page.fill('#genomeIdInput', '106654.148')
            page.click('#genomeFillBtn')
            page.wait_for_function("document.getElementById('genomeInfo').textContent.includes('fair test') || "
                                   "document.getElementById('genomeInfo').textContent.includes('trained on')")
            check(page.input_value('#genusSelect') == 'Acinetobacter', 'genus not filled')
            return page.inner_text('#genomeInfo').split('\n')[0]
        genome_fill()

        @step('/forecast: a prediction comes back')
        def forecast_submit():
            page.fill('#micInput', '16')
            with page.expect_navigation(timeout=60_000):
                page.click('#predictBtn')
            page.wait_for_selector('.result-main-label')
            return page.inner_text('.result-main-label')
        forecast_submit()

        @step('/forecast: CSV, PDF and PNG downloads')
        def forecast_downloads():
            page.wait_for_selector('#comparisonChart .main-svg')
            return downloads('forecast')
        forecast_downloads()

        @step('/forecast: batch CSV template downloads, uploads and returns results')
        def batch():
            goto('/forecast')
            page.click('button[data-bs-target="#batchPane"]')
            template = download(lambda: page.click('a[href="/forecast/template.csv"]'), b'antibiotic', 'template')
            path = os.path.join(tempfile.gettempdir(), 'e2e_batch.csv')
            with urllib.request.urlopen(base + '/forecast/template.csv', timeout=30) as r, open(path, 'wb') as fh:
                fh.write(r.read())
            page.set_input_files('#batchFile', path)
            with page.expect_navigation(timeout=120_000):
                page.click('#batchForm [type=submit]')
            check(page.locator('form.export-bar[data-export-page="batch"]').count() == 1, 'no batch result')
            got = downloads('batch', png=False, pdf=False)
            return f'template {template}; results {got}'
        batch()

        @step('/predict: a partial sequence is refused with a clear reason')
        def predict_refused():
            goto('/predict')
            select_when_ready('#predictForm [name=antibiotic]', 'ciprofloxacin')
            page.click('#fastaTab .nav-link >> nth=1')
            page.click('text=Load Sample')
            with page.expect_navigation(timeout=60_000):
                page.click('#predictForm [type=submit]')
            text = page.locator('.alert-danger-custom:visible').first.inner_text()   # not the hidden form hint
            check('complete assembly' in text or 'too short' in text, f'unexpected message: {text[:200]}')
            return text.strip()[:90]
        predict_refused()

        if genome:
            @step('/predict: a complete genome gets a prediction')
            def predict_genome():
                goto('/predict')
                select_when_ready('#predictForm [name=antibiotic]', 'ciprofloxacin')
                page.set_input_files('#fastaFile', genome)
                start = time.time()
                with page.expect_navigation(timeout=150_000):
                    page.click('#predictForm [type=submit]')
                page.wait_for_selector('.result-main-label', timeout=30_000)
                genes = page.locator('.gene-chip').count()
                return f"{page.inner_text('.result-main-label')} in {time.time() - start:.0f} s" + \
                       (f', {genes} genes shown' if genes else '')
            predict_genome()

            @step('/predict: CSV, PDF and PNG downloads')
            def predict_downloads():
                has_chart = page.locator('#kmerChart').count() > 0
                return downloads('predict', png=has_chart)
            predict_downloads()

        @step('/timeline: a simulation comes back')
        def timeline_submit():
            goto('/timeline')
            select_when_ready('#timelineForm [name=antibiotic]', 'ciprofloxacin')
            page.click('#fastaTab2 .nav-link >> nth=1')
            page.click('text=Load Sample')
            with page.expect_navigation(timeout=60_000):
                page.click('#timelineForm [type=submit]')
            page.wait_for_selector('#timelineChart .main-svg')
            return 'RL panel shown' if page.locator('#rlPanel').count() else 'no RL block in the response yet'
        timeline_submit()

        @step('/timeline: CSV, PDF and PNG downloads')
        def timeline_downloads():
            return downloads('timeline')
        timeline_downloads()

        @step('/genes: gene matrix and gene info CSV downloads')
        def gene_csvs():
            goto('/genes')
            got = []
            for name in ('matrix.csv', 'info.csv'):
                with urllib.request.urlopen(f'{base}/genes/{name}', timeout=120) as r:
                    head = r.read(64)
                    check(r.headers.get_content_type() == 'text/csv', f'{name} is {r.headers.get_content_type()}')
                check(head.startswith(b'Genome ID') or head.startswith(b'symbol'), f'{name} starts {head[:20]!r}')
                got.append(name)
            return ', '.join(got)
        gene_csvs()

        browser.close()

    passed = sum(ok for ok, *_ in results)
    print(f'\n{passed} of {len(results)} steps passed' + ('' if passed == len(results) else ':'))
    for ok, name, detail, _ in results:
        if not ok:
            print(f'  ✗ {name}: {detail}')
    return passed == len(results)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--base', default='http://127.0.0.1:5001', help='the website to check')
    ap.add_argument('--start', action='store_true', help='start both servers here first, stop them at the end')
    ap.add_argument('--browser', default='msedge' if os.name == 'nt' else 'chromium',
                    help='msedge, chrome or chromium (Playwright\'s own)')
    ap.add_argument('--no-genome', action='store_true', help='skip /predict with a complete genome')
    a = ap.parse_args()
    procs = start_servers() if a.start else []
    try:
        ok = main(a)
    finally:
        stop_servers(procs)
    sys.exit(0 if ok else 1)
