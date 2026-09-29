"""Audit of the BV-BRC AMR export: every data-quality count Paper A quotes.

One command, no network. Reads:
    Data/amr_full/            the complete export (and its manifest.json)
    Data/amr_output/          the April export's download log (.progress.json)
    experiments/cache/        the cleaned April (v5) and current tables (data_prep.get_clean)
    backend/taxon_species.csv taxon ranks from NCBI
Writes experiments/audit/results/audit.md and audit.json.

Run from the project root (about 3 minutes):
    .venv/bin/python experiments/audit/audit_bvbrc.py
"""
import collections
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
ROOT = os.path.dirname(EXP)
sys.path.insert(0, EXP)
sys.path.insert(0, HERE)
from lib import data_prep  # noqa: E402
from compare_clean_versions import summary as clean_summary  # noqa: E402

FULL = os.path.join(data_prep.data_root(), 'amr_full')
APRIL_LOG = os.path.join(data_prep.data_root(), 'amr_output', '.progress.json')
OUT_MD = os.path.join(HERE, 'results', 'audit.md')
OUT_JSON = os.path.join(HERE, 'results', 'audit.json')
PHENOTYPE_MAP = data_prep.PHENOTYPE_MAP
ALIASES = data_prep.ANTIBIOTIC_ALIASES
COLUMNS = ['Taxon ID', 'Genome ID', 'Antibiotic', 'Resistant Phenotype', 'Measurement',
           'Measurement Value', 'Measurement Unit', 'Testing Standard', 'Testing Standard Year',
           'Computational Method', 'Evidence']
BIG_TAXA = {562: 'Escherichia coli', 573: 'Klebsiella pneumoniae',
            28901: 'Salmonella enterica', 1280: 'Staphylococcus aureus'}


def pct(a, b):
    return 100 * a / b if b else 0.0


def scan_raw():
    """One pass over the raw export; counts plus a small frame of usable rows."""
    c = collections.defaultdict(collections.Counter)
    genome_ids, usable = set(), []
    files = sorted(glob.glob(os.path.join(FULL, '**', '*.csv'), recursive=True))
    for f in files:
        d = pd.read_csv(f, dtype=str, usecols=COLUMNS, keep_default_na=False)
        ev = np.where(d['Evidence'] == 'Laboratory Method', 'lab', 'computational')
        d['ev'] = ev
        genome_ids.update(d['Genome ID'])
        c['rows'].update(d['ev'])
        c['taxon_rows'].update(d['Taxon ID'])
        c['phenotype'].update(zip(d['ev'], d['Resistant Phenotype'].replace('', '(empty)')))
        ok = d['Resistant Phenotype'].isin(PHENOTYPE_MAP)
        has_meas = (d['Measurement'] != '') | (d['Measurement Value'] != '')
        c['no_label_but_measurement'].update(d.loc[~ok & has_meas, 'ev'])
        c['method'].update(zip(d['ev'], d['Computational Method'].replace('', '(none)'),
                               np.where(ok, 'label', 'no label')))
        name = d['Antibiotic'].str.strip().str.lower()
        c['raw_names'].update(name)
        c['raw_names_usable'].update(name[ok])
        u = d[ok]
        uv = u['ev'] == 'lab'
        c['usable_mic'].update(zip(u['ev'], np.where(
            (u['Measurement'] != '') | (u['Measurement Value'] != ''), 'yes', 'no')))
        c['usable_unit'].update(zip(u['ev'], u['Measurement Unit'].replace('', '(none)')))
        c['lab_standard'].update(u.loc[uv, 'Testing Standard'].replace('', '(none)'))
        c['lab_year'].update(np.where(u.loc[uv, 'Testing Standard Year'] != '', 'yes', 'no'))
        usable.append(pd.DataFrame({
            'genome': u['Genome ID'].values,
            'drug': name[ok].replace({k: v for k, v in ALIASES.items() if v}).values,
            'target': u['Resistant Phenotype'].map(PHENOTYPE_MAP).astype('int8').values,
            'lab': uv.values}))
    return c, genome_ids, pd.concat(usable, ignore_index=True), len(files)


def id_problems(genome_ids):
    """What reading Genome ID as a number would do (the v1 to v4 bug)."""
    ids = pd.Series(sorted(genome_ids))
    as_float = pd.to_numeric(ids, errors='coerce')
    groups = ids.groupby(as_float).size()
    merged = groups[groups > 1]
    trailing = ids[ids.str.contains(r'\.\d*0$')]
    return {
        'genome_ids': len(ids),
        'ids_in_collisions': int(merged.sum()),
        'ids_lost_to_merging': int((merged - 1).sum()),
        'ids_with_trailing_zero': len(trailing),
        'example_collision': ids[as_float == merged.index[0]].tolist() if len(merged) else [],
    }


def taxonomy(taxon_rows):
    table = pd.read_csv(data_prep.TAXON_SPECIES_PATH)
    rows = pd.Series({int(k): v for k, v in taxon_rows.items() if k.isdigit()})
    t = table.set_index('taxon_id').reindex(rows.index)
    rank = t['rank'].fillna('unknown')
    species_level = rank == 'species'
    ecoli = t.index[t['species_taxon_id'] == 562]
    return {
        'taxon_ids': len(rows),
        'taxon_ids_species_rank': int(species_level.sum()),
        'taxon_ids_below_species': int((~species_level & (rank != 'genus')).sum()),
        'rows_under_species_rank_ids': int(rows[species_level].sum()),
        'rows_total': int(rows.sum()),
        'species': int(t['species_taxon_id'].nunique()),
        'ecoli_taxon_ids': len(ecoli),
        'ecoli_rows_under_562': int(rows.get(562, 0)),
        'ecoli_rows_all_ids': int(rows[ecoli].sum()),
    }


def names(c):
    raw = c['raw_names']
    usable = c['raw_names_usable']
    renamed = {k for k, v in ALIASES.items() if v and k in raw}
    dropped = {k for k, v in ALIASES.items() if v is None and k in raw}
    after = {ALIASES.get(n, n) for n in usable if ALIASES.get(n, n)}
    return {
        'raw_names': len(raw), 'raw_names_with_labels': len(usable),
        'names_after_clean_up': len(after),
        'renamed_names': len(renamed), 'renamed_rows': sum(raw[n] for n in renamed),
        'renamed_rows_with_labels': sum(usable[n] for n in renamed),
        'dropped_names': len(dropped), 'dropped_rows': sum(raw[n] for n in dropped),
        'renamed_examples': sorted(renamed)[:8], 'dropped_examples': sorted(dropped)[:8],
    }


def labels(u):
    """Duplicates, conflicting lab results, and computational vs lab agreement."""
    g = u.groupby(['genome', 'drug'])
    n = g.size()
    lab = u[u['lab']]
    lab_pairs = lab.groupby(['genome', 'drug'])['target'].agg(['min', 'max', 'size'])
    comp = u[~u['lab']].groupby(['genome', 'drug'])['target'].agg(['min', 'max'])
    both = lab_pairs.join(comp, how='inner', lsuffix='_lab', rsuffix='_comp')
    both = both[(both['min_lab'] == both['max_lab']) & (both['min_comp'] == both['max_comp'])]
    agree = both['min_lab'] == both['min_comp']
    miss = (both['min_lab'] == 1) & (both['min_comp'] == 0)
    over = (both['min_lab'] == 0) & (both['min_comp'] == 1)
    return {
        'usable_rows': len(u), 'pairs': len(n), 'pairs_with_repeats': int((n > 1).sum()),
        'rows_removed_by_dedup': int(len(u) - len(n)),
        'lab_pairs': len(lab_pairs), 'lab_pairs_repeated': int((lab_pairs['size'] > 1).sum()),
        'lab_pairs_conflicting': int((lab_pairs['min'] != lab_pairs['max']).sum()),
        'pairs_with_lab_and_computational': len(both),
        'computational_agrees_with_lab': int(agree.sum()),
        'computational_calls_resistant_susceptible': int(miss.sum()),
        'computational_calls_susceptible_resistant': int(over.sum()),
    }


def april(c):
    """What the April download got, from its own log, against the complete export."""
    log = json.load(open(APRIL_LOG))
    status = collections.Counter(v.get('status') for k, v in log.items() if k != '_summary')
    rows = {int(k): v for k, v in log.items() if k != '_summary'}
    capped = [k for k, v in rows.items() if v.get('amr_records') == 500000]
    big = {}
    for tid, name in BIG_TAXA.items():
        r = rows.get(tid, {})
        big[tid] = {'name': name, 'april_status': r.get('status', 'absent'),
                    'april_rows_kept': r.get('amr_records', 0) if r.get('status') == 'done' else 0,
                    'complete_rows': int(c['taxon_rows'].get(str(tid), 0))}
    return {'status': dict(status), 'taxa_at_cap': capped, 'big_taxa': big,
            'april_rows': int(sum(v.get('amr_records', 0) for v in rows.values()
                                  if v.get('status') == 'done'))}


def breakdown(df, key, top=None):
    lab = df['is_lab_confirmed'] == 1
    t = df.groupby(key).agg(rows=('target', 'size'), genomes=('Genome ID', 'nunique'),
                            resistant=('target', 'mean'))
    t['lab_rows'] = df[lab].groupby(key).size()
    t['lab_resistant'] = df[lab].groupby(key)['target'].mean()
    t = t.fillna({'lab_rows': 0}).sort_values('rows', ascending=False)
    return t.head(top) if top else t


def table(t, label, italic=False):
    lines = [f'| {label} | Rows | Genomes | Resistant | Lab rows | Lab resistant |',
             '| --- | --- | --- | --- | --- | --- |']
    for k, r in t.iterrows():
        name = f'*{k}*' if italic else k
        lr = f'{100 * r.lab_resistant:.1f}%' if r.lab_rows else 'n/a'
        lines.append(f'| {name} | {int(r.rows):,} | {int(r.genomes):,} | {100 * r.resistant:.1f}% '
                     f'| {int(r.lab_rows):,} | {lr} |')
    return lines


def main():
    manifest = json.load(open(os.path.join(FULL, 'manifest.json')))
    print('[audit] scanning the raw export ...')
    c, genome_ids, usable, n_files = scan_raw()
    print('[audit] identifiers, taxonomy, names, labels ...')
    res = {'manifest': manifest, 'files': n_files,
           'rows': dict(c['rows']), 'ids': id_problems(genome_ids),
           'taxonomy': taxonomy(c['taxon_rows']), 'names': names(c),
           'labels': labels(usable), 'april': april(c)}
    total = sum(c['rows'].values())
    lab_total, comp_total = c['rows']['lab'], c['rows']['computational']
    ph = c['phenotype']
    res['phenotype'] = {f'{e}|{p}': n for (e, p), n in ph.items()}
    usable_lab = sum(n for (e, p), n in ph.items() if e == 'lab' and p in PHENOTYPE_MAP)
    usable_comp = sum(n for (e, p), n in ph.items() if e == 'computational' and p in PHENOTYPE_MAP)
    res['usable'] = {'lab': usable_lab, 'computational': usable_comp}
    res['methods'] = {f'{e}|{m}|{l}': n for (e, m, l), n in c['method'].items()}
    mic = c['usable_mic']
    units = c['usable_unit']
    res['measurements'] = {
        'usable_lab_with_mic': mic[('lab', 'yes')], 'usable_comp_with_mic': mic[('computational', 'yes')],
        'usable_lab_units': {u: n for (e, u), n in units.items() if e == 'lab'},
        'lab_standard': dict(c['lab_standard']), 'lab_year': dict(c['lab_year']),
        'no_label_but_measurement': dict(c['no_label_but_measurement'])}

    new_version = data_prep.version_of()
    print(f'[audit] cleaned tables v5 and {new_version} ...')
    v6 = data_prep.get_clean(verbose=False)
    v5 = data_prep.get_clean(source='amr_output', verbose=False)
    s5, s6 = clean_summary(v5), clean_summary(v6)
    key = ['Genome ID', 'Antibiotic']
    both = v5.merge(v6, on=key, suffixes=('_5', '_6'))
    res['cleaning'] = new_version
    res['v5_v6'] = {
        'v5': {k: float(v) for k, v in s5.items()}, 'v6': {k: float(v) for k, v in s6.items()},
        'v5_genomes_gone': len(set(v5['Genome ID']) - set(v6['Genome ID'])),
        'labels_changed': int((both['target_5'] != both['target_6']).sum())}

    # ── Markdown ─────────────────────────────────────────────────────────
    L = []
    ids, tx, nm, lb, ap, ms = (res[k] for k in ('ids', 'taxonomy', 'names', 'labels', 'april', 'measurements'))
    L += ['# BV-BRC AMR export: data audit', '',
          f'Export downloaded {manifest["started"][:16].replace("T", " ")} to '
          f'{manifest["finished"][:16].replace("T", " ")} UTC '
          f'from `{manifest["api"]}` ({n_files} files in `Data/amr_full/`). '
          'Every number below comes from `experiments/audit/audit_bvbrc.py`; '
          'machine-readable copy in `audit.json`.', '',
          '## 1. The export', '',
          '| | Lab | Computational | All |', '| --- | --- | --- | --- |',
          f'| Records | {lab_total:,} | {comp_total:,} | {total:,} |',
          f'| With a usable phenotype | {usable_lab:,} ({pct(usable_lab, lab_total):.1f}%) '
          f'| {usable_comp:,} ({pct(usable_comp, comp_total):.1f}%) '
          f'| {usable_lab + usable_comp:,} ({pct(usable_lab + usable_comp, total):.1f}%) |',
          f'| No phenotype, but a measurement | {ms["no_label_but_measurement"].get("lab", 0):,} '
          f'| {ms["no_label_but_measurement"].get("computational", 0):,} | |', '',
          'Lab records without a phenotype are measurements (mostly MICs) that BV-BRC never '
          'turned into a resistant or susceptible call; cleaning drops them, although a '
          'breakpoint table could label them.', '',
          '**Where the computational labels come from:**', '',
          '| Method | Rows with a label | Rows without |', '| --- | --- | --- |']
    meth = collections.defaultdict(lambda: [0, 0])
    for (e, m, l), n in c['method'].items():
        if e == 'computational':
            meth[m][0 if l == 'label' else 1] += n
    for m, (a, b) in sorted(meth.items(), key=lambda x: -sum(x[1])):
        L.append(f'| {m} | {a:,} | {b:,} |')

    L += ['', '## 2. The April export was incomplete', '',
          'The first download (April 2026, `scripts/bvbrc_download/download_amr_csv.py`) '
          'paged each taxon by offset and stopped at 500,000 rows. Its own log:', '',
          '| Status in the April log | Taxa |', '| --- | --- |']
    L += [f'| {k} | {v:,} |' for k, v in sorted(ap['status'].items(), key=lambda x: -x[1])]
    L += ['', f'Rows kept in April: {ap["april_rows"]:,} of {total:,} '
          f'({pct(ap["april_rows"], total):.1f}%). Taxa stopped at the 500,000-row cap: '
          f'{", ".join(map(str, ap["taxa_at_cap"])) or "none"}.', '',
          '| Taxon | April | Complete export |', '| --- | --- | --- |']
    for tid, b in ap['big_taxa'].items():
        a = f'{b["april_rows_kept"]:,} ({b["april_status"]})'
        L.append(f'| {tid} *{b["name"]}* | {a} | {b["complete_rows"]:,} |')
    a5, a6 = res['v5_v6']['v5'], res['v5_v6']['v6']
    L += ['', f'**Effect on the cleaned data** (v5 = April export, {new_version} = complete export; '
          'the cleaning differs only in v7 treating mm values as no MIC):', '',
          f'| | v5 | {new_version} |', '| --- | --- | --- |']
    for k in a5:
        f = (lambda v: f'{100 * v:.1f}%') if a5[k] <= 1 else (lambda v: f'{int(v):,}')
        L.append(f'| {k} | {f(a5[k])} | {f(a6[k])} |')
    L += ['', f'Between the two downloads BV-BRC removed {res["v5_v6"]["v5_genomes_gone"]:,} '
          f'genomes and changed {res["v5_v6"]["labels_changed"]:,} labels, so an export must '
          'be dated to be reproducible.']

    L += ['', '## 3. Identifiers', '',
          '| Genome ID read as a number instead of text | Count |', '| --- | --- |',
          f'| Genome IDs | {ids["genome_ids"]:,} |',
          f'| IDs that collide with another ID | {ids["ids_in_collisions"]:,} |',
          f'| Genomes lost by merging | {ids["ids_lost_to_merging"]:,} |',
          f'| IDs ending in 0 after the dot (lose it as a number) | {ids["ids_with_trailing_zero"]:,} |',
          '', f'Example collision: {" and ".join(ids["example_collision"])}.']

    L += ['', '## 4. Taxonomy', '',
          '| | Count |', '| --- | --- |',
          f'| Taxon IDs in the export | {tx["taxon_ids"]:,} |',
          f'| of which species rank | {tx["taxon_ids_species_rank"]:,} |',
          f'| of which strain, serotype or other sub-species rank | {tx["taxon_ids_below_species"]:,} |',
          f'| Species they belong to | {tx["species"]:,} |',
          f'| Rows filed under a species-rank ID | {tx["rows_under_species_rank_ids"]:,} of {tx["rows_total"]:,} '
          f'({pct(tx["rows_under_species_rank_ids"], tx["rows_total"]):.1f}%) |',
          f'| *E. coli*: taxon IDs | {tx["ecoli_taxon_ids"]:,} |',
          f'| *E. coli*: rows under 562 itself, and under all its IDs | '
          f'{tx["ecoli_rows_under_562"]:,} of {tx["ecoli_rows_all_ids"]:,} |',
          '', 'Most taxon IDs are strains or serotypes, but most rows are filed under a '
          'species ID. The April export looked the other way round (3,224 of its 3,655 taxa '
          'were strains, and *E. coli* 562 never appeared) only because its species-level '
          'downloads failed (section 2).']

    L += ['', '## 5. Antibiotic names', '',
          '| | Count |', '| --- | --- |',
          f'| Distinct names (lower-cased) | {nm["raw_names"]:,} |',
          f'| Distinct names on rows with a phenotype | {nm["raw_names_with_labels"]:,} |',
          f'| After the alias map | {nm["names_after_clean_up"]:,} |',
          f'| Names renamed (spelling variants) | {nm["renamed_names"]:,} ({nm["renamed_rows"]:,} rows, '
          f'{nm["renamed_rows_with_labels"]:,} with a phenotype) |',
          f'| Names dropped (not a drug) | {nm["dropped_names"]:,} ({nm["dropped_rows"]:,} rows) |',
          '', f'Renamed, for example: {", ".join(nm["renamed_examples"])}. '
          f'Dropped, for example: {", ".join(nm["dropped_examples"])}.']

    ul = ms['usable_lab_units']
    std = ms['lab_standard']
    L += ['', '## 6. Measurements and testing standards (rows with a phenotype)', '',
          '| | Count |', '| --- | --- |',
          f'| Lab rows with a measurement | {ms["usable_lab_with_mic"]:,} of {usable_lab:,} '
          f'({pct(ms["usable_lab_with_mic"], usable_lab):.1f}%) |',
          f'| Computational rows with a measurement | {ms["usable_comp_with_mic"]:,} of {usable_comp:,} '
          f'({pct(ms["usable_comp_with_mic"], usable_comp):.1f}%) |']
    L += [f'| Lab rows with unit "{u}" | {n:,} |' for u, n in sorted(ul.items(), key=lambda x: -x[1])[:5]]
    L += [f'| Lab rows with no testing standard | {std.get("(none)", 0):,} |',
          f'| Lab rows with no testing standard year | {ms["lab_year"].get("no", 0):,} |']
    L += ['', 'Testing standards as written (lab rows): ' + ', '.join(
        f'"{k}" {v:,}' for k, v in sorted(std.items(), key=lambda x: -x[1])[:8]) + '.',
        '', 'Rows measured in mm are disk-diffusion zone diameters, not MICs; the cleaning '
        '(`data_prep.clean`) currently reads their number as an MIC.']

    L += ['', '## 7. Duplicates, conflicts and computational vs lab labels', '',
          '| | Count |', '| --- | --- |',
          f'| Rows with a phenotype | {lb["usable_rows"]:,} |',
          f'| Genome and drug pairs | {lb["pairs"]:,} |',
          f'| Rows removed by one-row-per-pair | {lb["rows_removed_by_dedup"]:,} |',
          f'| Lab pairs tested more than once | {lb["lab_pairs_repeated"]:,} |',
          f'| Lab pairs with conflicting results | {lb["lab_pairs_conflicting"]:,} |',
          f'| Pairs with both a lab and a computational label | {lb["pairs_with_lab_and_computational"]:,} |',
          f'| Computational label agrees with the lab | {lb["computational_agrees_with_lab"]:,} '
          f'({pct(lb["computational_agrees_with_lab"], lb["pairs_with_lab_and_computational"]):.1f}%) |',
          f'| Computational says susceptible, lab says resistant | {lb["computational_calls_resistant_susceptible"]:,} |',
          f'| Computational says resistant, lab says susceptible | {lb["computational_calls_susceptible_resistant"]:,} |',
          '', 'Pairs whose lab results conflict with each other, or whose computational results '
          'do, are left out of the agreement count.']

    L += ['', f'## 8. The cleaned data ({new_version}) by genus, drug class and drug', '']
    L += table(breakdown(v6, 'genus', 15), 'Genus', italic=True)
    classes = breakdown(v6, 'drug_class', 15)
    L += ['', *table(classes, 'Drug class')]
    gap = (classes['resistant'] - classes['lab_resistant']).dropna()
    worst = gap.abs().sort_values(ascending=False).head(3)
    L += ['', 'Largest gaps between the resistant share of all rows (mostly computational) and '
          'of lab rows: ' + ', '.join(
              f'{k} {100 * classes.loc[k, "resistant"]:.1f}% vs {100 * classes.loc[k, "lab_resistant"]:.1f}%'
              for k in worst.index) + '.']
    L += ['', *table(breakdown(v6, 'Antibiotic', 20), 'Antibiotic')]

    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_MD, 'w') as fh:
        fh.write('\n'.join(L) + '\n')
    with open(OUT_JSON, 'w') as fh:
        json.dump(res, fh, indent=2, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
    print(f'[audit] wrote {os.path.relpath(OUT_MD, ROOT)} and {os.path.relpath(OUT_JSON, ROOT)}')


if __name__ == '__main__':
    main()
