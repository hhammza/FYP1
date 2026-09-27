"""Batch CSV forecast, POST /api/forecast/batch/ (T2.3).

    python -m unittest discover -s backend/tests
"""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import django_setup  # noqa: E402,F401  (configures Django)

from django.conf import settings  # noqa: E402
from django.core.cache import cache  # noqa: E402
from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from django.test import Client  # noqa: E402

HEADER = 'antibiotic,genus,species,taxon_id,mic_value,mic_sign\n'


def upload(text, name='batch.csv'):
    return Client().post('/api/forecast/batch/', {'file': SimpleUploadedFile(name, text.encode())})


class BatchForecast(unittest.TestCase):
    def setUp(self):
        cache.clear()

    def test_one_result_row_per_input_row_with_errors_marked(self):
        r = upload(HEADER
                   + 'ciprofloxacin,Escherichia,coli,562,4,>=\n'
                   + ',Escherichia,coli,562,,\n'
                   + 'notadrug,Escherichia,coli,562,,\n'
                   + 'gentamicin,Klebsiella,pneumoniae,abc,,\n'
                   + 'tetracycline,Salmonella,enterica,28901,-2,\n'
                   + 'ampicillin,Escherichia,coli,562,,<=\n')
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertEqual([row['row'] for row in d['rows']], [1, 2, 3, 4, 5, 6])
        errors = [bool(row['error']) for row in d['rows']]
        self.assertEqual(errors, [False, True, True, True, True, False])
        self.assertEqual(d['summary']['rows'], 6)
        self.assertEqual(d['summary']['errors'], 4)
        self.assertEqual(d['summary']['resistant'] + d['summary']['susceptible'], 2)

    def test_same_probability_as_the_single_forecast(self):
        d = upload(HEADER + 'ciprofloxacin,Escherichia,coli,562,4,>=\n').json()
        single = Client().post('/api/forecast/', data=json.dumps({
            'antibiotic': 'ciprofloxacin', 'genus': 'Escherichia', 'species': 'coli',
            'taxon_id': 562, 'mic_value': 4, 'mic_sign': '>='}), content_type='application/json').json()
        self.assertEqual(d['rows'][0]['probability'], single['probability'])
        self.assertEqual(d['threshold'], single['threshold'])

    def test_spelling_variants_are_canonical(self):
        d = upload(HEADER + 'rifampin,Mycobacterium,tuberculosis,1773,,\n').json()
        self.assertEqual(d['rows'][0]['antibiotic'], 'rifampicin')
        self.assertEqual(d['rows'][0]['error'], '')

    def test_needs_an_antibiotic_column(self):
        self.assertEqual(upload('drug,genus\nampicillin,Escherichia\n').status_code, 400)

    def test_needs_a_file_and_rows(self):
        self.assertEqual(Client().post('/api/forecast/batch/', {}).status_code, 400)
        self.assertEqual(upload(HEADER).status_code, 400)

    def test_row_limit_is_413(self):
        r = upload('antibiotic\n' + 'ampicillin\n' * (settings.BATCH_MAX_ROWS + 1))
        self.assertEqual(r.status_code, 413)

    def test_size_limit_is_413(self):
        big = 'antibiotic,genus\n' + ('ampicillin,' + 'x' * 1000 + '\n') * (settings.BATCH_MAX_BYTES // 1000 + 10)
        self.assertEqual(upload(big).status_code, 413)


if __name__ == '__main__':
    unittest.main()
