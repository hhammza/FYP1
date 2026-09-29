"""The site works without internet: every library a page needs is served from
static/vendor/, only the web fonts come from Google (they fall back offline).

    python -m unittest discover -s frontend/tests
"""
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.dirname(HERE)
sys.path.insert(0, FRONTEND)
os.environ['BACKEND_URL'] = 'http://127.0.0.1:1/api'      # nothing listens here
os.environ.pop('PORT', None)
import app  # noqa: E402

ALLOWED_REMOTE = ('https://fonts.googleapis.com/',)


class OfflineAssets(unittest.TestCase):
    def test_templates_load_no_remote_scripts_or_styles(self):
        for name in os.listdir(os.path.join(FRONTEND, 'templates')):
            with open(os.path.join(FRONTEND, 'templates', name), encoding='utf-8') as fh:
                html = fh.read()
            for url in re.findall(r'<(?:script|link)[^>]+(?:src|href)="(https?://[^"]+)"', html):
                self.assertTrue(url.startswith(ALLOWED_REMOTE), f'{name} loads {url} from the internet')

    def test_every_vendor_file_the_pages_use_is_served(self):
        html = app.app.test_client().get('/about').get_data(as_text=True)
        vendor = re.findall(r'(?:src|href)="(/static/vendor/[^"]+)"', html)
        self.assertEqual(len(vendor), 4)                     # Bootstrap CSS + JS, icons, Plotly
        client = app.app.test_client()
        for path in vendor + ['/static/vendor/bootstrap-icons-1.11.3/fonts/bootstrap-icons.woff2']:
            r = client.get(path)
            self.assertEqual(r.status_code, 200, path)
            self.assertGreater(len(r.data), 10_000, path)
            r.close()


if __name__ == '__main__':
    unittest.main()
