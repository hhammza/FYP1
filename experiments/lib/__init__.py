"""Shared code for the experiment scripts (run.py, promote.py, export_report.py, ...).

Every script imports from here, so this is where their output is made safe
for Windows: there, output redirected to a file (`python run.py ... > log`)
is encoded as cp1252, which cannot print the '→', '≤' and '±' in the
scripts' messages, and the first such print killed the run.
"""
import sys

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, 'reconfigure') and (_stream.encoding or '').lower() not in ('utf-8', 'utf8'):
        _stream.reconfigure(encoding='utf-8', errors='replace')
